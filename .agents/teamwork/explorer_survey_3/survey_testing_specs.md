# Relatório de Levantamento Técnico: Ambiente de Testes, Especificações Edge-TTS e Lógica de Silêncio

**Projeto**: Montanha Media Lab & Video Studio  
**Data**: 2026-11-02  
**Autor**: Teamwork Explorer (Testing & Specs Explorer)  
**Arquivo**: `.agents/teamwork/explorer_survey_3/survey_testing_specs.md`  

---

## 1. Sumário Executivo

Este levantamento técnico investigou os requisitos de infraestrutura de teste ponta a ponta (E2E) com Playwright no Microsoft Edge, as especificações exatas e comportamentos empíricos do motor de síntese neural `edge-tts` (v7.3.1) para o português brasileiro, e a mecânica de detecção e recorte de pausas e silêncios via `ffmpeg` integrada à timeline estilo Clipchamp.

### Principais Constatações:
1. **Playwright no Microsoft Edge Nativo**: O Playwright (v1.64.0) já está instalado no ambiente Python 3.11 do sistema e inicializa o Microsoft Edge oficial (`channel='msedge'`, versão 156.0.4314.50) sem necessidade de download de navegadores adicionais. Os testes podem ser executados usando o `unittest` padrão do Python, sem sobrecarga ou dependências npm externas.
2. **Descoberta Crítica de Vozes do `edge-tts`**: Das vozes mencionadas no escopo, **exatamente 3 vozes brasileiras são ativas e gratuitas no serviço Microsoft Edge TTS**: `pt-BR-FranciscaNeural` (Feminino), `pt-BR-AntonioNeural` (Masculino) e `pt-BR-ThalitaMultilingualNeural` (Feminino). As demais (`Brenda`, `Donato`, `Elza`, `Fabio`, `Giovanna`, etc.) são exclusivas do serviço pago Azure Speech SDK; quando solicitadas ao `edge-tts`, resultam em exceção `edge_tts.exceptions.NoAudioReceived`. Um mapeamento defensivo com fallback deve ser implementado no backend.
3. **Discrepância Detectada em `server.py` vs `engine.py`**: A rota `POST /api/silence-detect` em `server.py` invoca `engine.detect_silence_points()`. No entanto, em `engine.py`, a função existente chama-se `detect_silence()`. Essa discrepância de nomenclatura causa `AttributeError` e precisa de alinhamento imediato.
4. **Mecânica de Divisão na Timeline**: A detecção via `silencedetect=noise=-30dB:d=0.4` extrai milimetricamente intervalos `[silence_start, silence_end]`. Para o editor, isso se converte em segmentação de trechos falados contínuos com exclusão dos intervalos de silêncio (efeito ripple cut), integrado ao histórico de Desfazer/Refazer (`saveHistory`).

---

## 2. Levantamento do Ambiente e Infraestrutura de Testes

### 2.1. Estado Atual do Repositório
- **Repositório Git**: Ramo `main` limpo e sincronizado com `origin/main` (`https://github.com/Coach-Montanha/montanha-media-lab.git`).
- **Suíte de Testes Pré-existente**: Inexistente no repositório. Não havia arquivos de teste no diretório raiz ou subpastas.
- **Portas de Operação**:
  - Servidor local Windows: Porta `4190` (já em execução sob processo Python ID 976, servindo `public/index.html`).
  - Ambiente Termux (Android): Porta `8080` (configuração preservada via fallback de variáveis de ambiente `PORT`).

### 2.2. Ferramentas e Runtimes Instalados
| Componente | Versão Detectada | Caminho / Detalhe |
|---|---|---|
| **Python** | 3.11.9 | `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe` |
| **Playwright (Python)** | 1.64.0 | Instalado em `site-packages\playwright` |
| **Microsoft Edge** | 156.0.4314.50 | Canal oficial de produção do Windows (`channel='msedge'`) |
| **edge-tts** | 7.3.1 | CLI e biblioteca Python instaladas |
| **ffmpeg / ffprobe** | 6.1.1 (essentials) | Disponíveis no `PATH` do sistema |
| **Node.js / npm** | v22.14.0 / 10.9.2 | Disponíveis |

### 2.3. Execução do Playwright com Edge no Windows PowerShell
O teste de validação comprovou a inicialização síncrona do Microsoft Edge através do Python Playwright:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:4190", wait_until="domcontentloaded")
    assert "Montanha Media Lab" in page.title()
    browser.close()
```

**Comando de Execução no PowerShell**:
```powershell
python -m unittest discover tests -p "test_*.py"
```
*(Execução 100% nativa sem dependências extras de CI ou npm).*

---

## 3. Especificações Técnicas do Motor Edge-TTS

### 3.1. CLI e SDK Python
- **CLI**:
  ```powershell
  edge-tts --voice pt-BR-FranciscaNeural --rate +0% --pitch +0Hz --text "Texto a ser narrado" --write-media exports/tts_audio.mp3
  ```
- **SDK Assíncrono Python**:
  ```python
  import edge_tts

  async def generate_speech(text: str, voice: str = "pt-BR-FranciscaNeural", rate: str = "+0%", pitch: str = "+0Hz", output_path: str = "uploads/tts.mp3"):
      communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
      await communicate.save(output_path)
  ```

### 3.2. Formatação Obrigatória de Parâmetros
O `edge-tts` exige formatação de strings assinadas com unidades explícitas:
- **Rate (Velocidade)**: Exige formato de porcentagem assinada `+0%` (padrão), `+10%`, `+25%`, `-15%`, `-50%`. Valores inteiros ou decimais puros sem o sinal ou `%` falham.
- **Pitch (Tom)**: Exige formato em Hertz assinado `+0Hz` (padrão), `+5Hz`, `-10Hz`.
- **Volume**: Exige porcentagem assinada `+0%` (padrão), `+20%`, `-30%`.

### 3.3. Catálogo de Vozes Brasileiras: Constatação Empírica Crucial
Uma varredura completa das 322 vozes disponibilizadas pelo endpoint público do Microsoft Edge TTS revelou que **apenas 3 vozes pt-BR existem no serviço**:

| ShortName | Gênero | Nome Amigável / Perfil | Status no Edge TTS |
|---|---|---|---|
| **`pt-BR-FranciscaNeural`** | Feminino | Microsoft Francisca Online (Natural) - Português (Brasil) | **Suportado (Nativo)** |
| **`pt-BR-AntonioNeural`** | Masculino | Microsoft Antonio Online (Natural) - Português (Brasil) | **Suportado (Nativo)** |
| **`pt-BR-ThalitaMultilingualNeural`** | Feminino | Microsoft ThalitaMultilingual Online (Natural) - Português | **Suportado (Nativo)** |
| *pt-PT-DuarteNeural* | Masculino | Microsoft Duarte Online (Natural) - Português (Portugal) | Suportado (PT) |
| *pt-PT-RaquelNeural* | Feminino | Microsoft Raquel Online (Natural) - Português (Portugal) | Suportado (PT) |
| `pt-BR-BrendaNeural` | Feminino | Voz do catálogo Azure Speech pago | **Falha com NoAudioReceived** |
| `pt-BR-DonatoNeural` | Masculino | Voz do catálogo Azure Speech pago | **Falha com NoAudioReceived** |
| `pt-BR-ElzaNeural` etc. | Misto | Vozes do catálogo Azure Speech pago | **Falha com NoAudioReceived** |

#### Recomendação de Arquitetura no Backend (`server.py`):
Implementar um mapa de tolerância a nomes de voz para garantir que requisições solicitando qualquer voz da lista do prompt sejam atendidas sem lançar erro 500:
```python
VALID_EDGE_VOICES = {
    "pt-BR-FranciscaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural": "pt-BR-AntonioNeural",
    "pt-BR-ThalitaMultilingualNeural": "pt-BR-ThalitaMultilingualNeural",
    # Mapeamentos de Fallback inteligente por gênero:
    "pt-BR-BrendaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-DonatoNeural": "pt-BR-AntonioNeural",
    "pt-BR-ElzaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-FabioNeural": "pt-BR-AntonioNeural",
    "pt-BR-GiovannaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-HumbertoNeural": "pt-BR-AntonioNeural",
    "pt-BR-JulioNeural": "pt-BR-AntonioNeural",
    "pt-BR-LeilaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-LeticiaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-ManuelaNeural": "pt-BR-FranciscaNeural",
    "pt-BR-NicolauNeural": "pt-BR-AntonioNeural",
    "pt-BR-ValerioNeural": "pt-BR-AntonioNeural",
    "pt-BR-YaraNeural": "pt-BR-FranciscaNeural",
}
```

### 3.4. Especificação do Endpoint `POST /api/tts`
- **Rota**: `POST /api/tts`
- **Headers**: `Content-Type: application/json`
- **Payload de Entrada**:
  ```json
  {
    "text": "Bem-vindo ao Montanha Media Lab.",
    "voice": "pt-BR-FranciscaNeural",
    "rate": "+0%",
    "pitch": "+0Hz"
  }
  ```
- **Resposta Sucesso (HTTP 200)**:
  ```json
  {
    "status": "success",
    "filename": "tts_1730573900.mp3",
    "url": "/stream?file=C%3A%5CUsers%5C...%5Ctts_1730573900.mp3",
    "path": "C:\\Users\\Administrator\\Documents\\Projetos\\montanha-media-lab\\uploads\\tts_1730573900.mp3",
    "duration": 2.85
  }
  ```
- **Resposta Erro (HTTP 400/500)**:
  ```json
  {
    "status": "error",
    "message": "Texto não pode ser vazio"
  }
  ```

---

## 4. Mecanismo de Detecção de Silêncio e Divisão na Timeline

### 4.1. Extração de Silêncio via FFmpeg
O comando otimizado para extração de silêncio sem decodificação de vídeo:
```powershell
ffmpeg -y -i "midia.mp4" -af "silencedetect=noise=-30dB:d=0.4" -f null -
```
- **Parâmetros**:
  - `noise=-30dB`: Limiar acústico para considerar silêncio ou respiração leve.
  - `d=0.4`: Duração mínima de silêncio (400ms), preservando pausas naturais entre palavras e detectando hesitações e silêncios reais.
- **Linhas Extraídas do Stderr**:
  ```text
  [silencedetect @ 000001a2] silence_start: 1.0002
  [silencedetect @ 000001a2] silence_end: 2.8504 | silence_duration: 1.8502
  ```

### 4.2. Correção de Discrepância em `engine.py` e `server.py`
Para que `/api/silence-detect` funcione de forma transparente, a seguinte assinatura unificada deve existir em `engine.py`:

```python
def detect_silence_points(media_path: str, noise_db: float = -30.0, min_duration: float = 0.4) -> Dict[str, Any]:
    silences = detect_silence(media_path, noise_db=noise_db, min_duration=min_duration)
    info = get_video_info(media_path)
    total_duration = info.get("duration", 0.0)
    speech_segments = compute_speech_segments(total_duration, silences, margin=0.05)
    
    return {
        "status": "success",
        "silences": [{"start": round(s, 3), "end": round(e, 3), "duration": round(e - s, 3)} for s, e in silences],
        "speech_segments": [{"start": round(s, 3), "end": round(e, 3), "duration": round(e - s, 3)} for s, e in speech_segments],
        "total_duration": total_duration
    }
```

### 4.3. Algoritmo de Tradução em Pontos de Divisão na Timeline
Quando o usuário aciona **Menu de Contexto > Sugestões de IA > Recortar Pausas e Silêncios**:

Dado um clipe selecionado na timeline com início em `clip.start` e fim em `clip.end` (duração $D = \text{end} - \text{start}$):
1. O frontend chama `POST /api/silence-detect` passando o caminho do arquivo do clipe.
2. O backend retorna os `speech_segments` relativos ao arquivo (ex: `[[0.0, 1.2], [2.5, 4.8]]`).
3. O frontend substitui o clipe original por sub-clipes contíguos na timeline (ripple cut):
   - **Subclipe 1**: Início no tempo original `clip.start`, duração `1.2s`.
   - **Subclipe 2**: Início imediato após Subclipe 1 (`clip.start + 1.2s`), contendo o segundo trecho de fala de `2.3s`.
   - As pausas vazias são eliminadas da timeline e a duração total do projeto é encurtada pela soma dos silêncios cortados.
4. O estado é salvo com `saveHistory()`, permitindo desfazer o corte de silêncio com `Ctrl+Z`.

---

## 5. Estratégia de Testes E2E Multi-Tier com Playwright no Microsoft Edge

Para garantir cobertura exaustiva e evitar regressões sem lentidão, a suíte de testes deve ser organizada em 4 camadas estruturadas:

```
tests/
├── __init__.py
├── test_tier1_features.py       # Cobertura funcional básica de componentes e UI
├── test_tier2_boundaries.py     # Casos de borda, entradas vazias, limites e atalhos
├── test_tier3_interactions.py   # Interações compostas (TTS -> Timeline -> Context Menu)
└── test_tier4_user_journey.py   # Fluxo de ponta a ponta realista
```

### 5.1. Tier 1: Cobertura Funcional de Recursos (Feature Coverage)
Valida a existência e o comportamento individual dos novos componentes da interface e do backend:
- **T1.1 - Geração de TTS via API**:
  - `POST /api/tts` com voz `pt-BR-FranciscaNeural`, texto `"Teste de voz"`, velocidade `+10%`.
  - Verifica retorno de status 200, existência do arquivo `.mp3` no disco e duração calculada > 0.
- **T1.2 - Dock Vertical Esquerdo (~56px)**:
  - Inspeciona o dock `#leftDockRail`: largura de aproximadamente `56px`, layout vertical limpo.
  - Verifica presença dos 4 ícones especificados:
    1. *Minha Mídia* (`#dockBtnMedia`)
    2. *Gravar & Criar / TTS* (`#dockBtnCreate`)
    3. *Legendas* (`#dockBtnCaptions`)
    4. *Áudio* (`#dockBtnAudio`)
- **T1.3 - Gaveta Expansível Lateral (Drawer)**:
  - Clicar em cada ícone do dock abre a respectiva gaveta lateral `#dockDrawer` sem desalinhamento do player e da timeline.
  - Clicar no ícone ativo fecha a gaveta retrátil.
- **T1.4 - Barra Superior Minimalista da Timeline**:
  - A barra de ferramentas da timeline `#timelineMinimalBar` deve conter **estritamente**:
    - Botão **Dividir** (ícone de tesoura)
    - Botão **Desfazer**
    - Botão **Refazer**
    - Botão **Play / Pause**
  - Demais botões poluídos (aparar, adicionar trilhas redundantes) removidos ou transferidos para o menu de contexto.
- **T1.5 - Menu de Contexto do Botão Direito nos Clipes**:
  - Clique com o botão direito em um clipe da timeline exibe o menu flutuante `#timelineContextMenu` posicionado nas coordenadas do ponteiro.
  - Contém: Duplicar, Copiar, Colar, Excluir, Dividir, Congelar Quadro, Renomear, Submenu Áudio (Mudo, Desanexar), Submenu Sugestões de IA (Recortar Pausas).
- **T1.6 - Dock Retrátil à Direita (Propriedades)**:
  - Ao selecionar um clipe na timeline, o dock direito `#rightInspectorDock` exibe sliders interativos de Volume, Velocidade e controle de Legendas.

### 5.2. Tier 2: Casos de Borda e Limites (Boundary & Corner Cases)
Garante a estabilidade da aplicação sob condições adversas:
- **T2.1 - Texto de TTS Vazio ou com Espaços**:
  - Envio de string vazia ou apenas espaços para `/api/tts`.
  - Frontend deve bloquear o botão ou exibir toast informativo `"Digite um texto para sintetizar!"`, sem travar ou gerar arquivo vazio.
- **T2.2 - Valores Extremos de Velocidade e Tom**:
  - Testa síntese com velocidade máxima (`+100%`) e mínima (`-50%`), garantindo formatação correta de strings no backend.
- **T2.3 - Divisão em Extremidades do Clipe**:
  - Tentar dividir o clipe com a agulha na posição exata `0.0s` ou `end` do clipe exibe toast de aviso sem corromper a lista de clipes.
- **T2.4 - Ações em Timeline Vazia**:
  - Pressionar `Del`, `S` ou `Ctrl+D` sem clipes selecionados não lança exceção no console.
- **T2.5 - Matriz de Atalhos de Teclado**:
  - `Ctrl+D`: Dispara Duplicar clipe selecionado.
  - `S`: Dispara Dividir no cursor.
  - `Del` / `Backspace`: Exclui clipe selecionado.
  - `F`: Congela o quadro atual (Freeze Frame).
  - `Ctrl+Z` / `Ctrl+Y`: Desfaz e refaz alterações.

### 5.3. Tier 3: Interações Cruzadas entre Recursos (Cross-Feature Interactions)
Valida a transição de dados e estados entre diferentes partes do sistema:
- **T3.1 - Ciclo TTS -> Timeline**:
  - Digitar texto na gaveta de TTS -> Clicar em "Prévia" (áudio toca) -> Clicar em "Adicionar à Timeline".
  - Verifica que um novo clipe é injetado na trilha de áudio com as dimensões corretas.
- **T3.2 - Duplicação e Divisão Encadeadas**:
  - Selecionar o clipe de áudio criado -> Pressionar `Ctrl+D` (duplica) -> Mover a agulha para o meio -> Pressionar `S` (divide).
  - Verifica integridade do array `clips` (quantidade e IDs únicos).
- **T3.3 - Mudo e Atualização de Propriedades**:
  - Clicar com botão direito no clipe -> Submenu Áudio > Ativar Mudo.
  - Verifica se o badge de mudo é atualizado no clipe e no dock de propriedades à direita.
- **T3.4 - Integridade do Histórico de Desfazer/Refazer**:
  - Executar a sequência: Duplicar -> Dividir -> Excluir.
  - Pressionar `Ctrl+Z` 3 vezes: restaura a timeline ao estado original sem falhas de renderização.
  - Pressionar `Ctrl+Y` 3 vezes: reaplica as alterações.

### 5.4. Tier 4: Fluxo Real do Usuário (Real-World End-to-End Workflow)
Simula uma sessão completa de edição sem mocks:
1. Abre o editor no Edge (`http://localhost:4190`).
2. Abre a aba "Gravar & Criar" no dock fino esquerdo.
3. Escolhe a voz `pt-BR-FranciscaNeural`, ajusta velocidade para 1.1x e digita fala promocional.
4. Gera o áudio e insere na timeline.
5. Abre o menu de contexto no clipe de áudio -> "Sugestões de IA > Recortar Pausas e Silêncios".
6. Aguarda detecção; verifica que os silêncios foram cortados e os clipes reorganizados contiguamente.
7. Abre o dock de propriedades direito e altera o volume para 120%.
8. Clica no botão Play da barra minimalista e valida avanço contínuo da agulha de reprodução.

---

## 6. Template de Teste Automatizado Base em Python Playwright

Abaixo está o template de teste pronto para ser executado no Microsoft Edge sob `tests/test_e2e_edge.py`:

```python
"""
Montanha Media Lab - Suíte de Testes Automatizados E2E no Microsoft Edge
Executa testes ponta a ponta sem dependências npm ou mocks externos.
"""

import unittest
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4190"

class TestMontanhaMediaLabE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        # Inicializa estritamente o Microsoft Edge oficial do Windows
        cls.browser = cls.playwright.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.page.goto(BASE_URL, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1000)

    def tearDown(self):
        self.context.close()

    def test_tier1_ui_components(self):
        """Verifica a presença dos docks laterais e da barra minimalista."""
        # Dock vertical esquerdo (~56px)
        left_dock = self.page.locator("#leftDockRail")
        self.assertTrue(left_dock.is_visible())
        
        # Barra minimalista com exatamente os botões requeridos
        self.assertTrue(self.page.locator("#btnMinimalSplit").is_visible())
        self.assertTrue(self.page.locator("#btnMinimalUndo").is_visible())
        self.assertTrue(self.page.locator("#btnMinimalRedo").is_visible())
        self.assertTrue(self.page.locator("#btnMinimalPlay").is_visible())

    def test_tier2_tts_generation_and_timeline(self):
        """Valida o fluxo completo de TTS e inserção na timeline."""
        # 1. Abre gaveta de Gravar & Criar (TTS)
        self.page.click("#dockBtnCreate")
        self.page.wait_for_selector("#panel_tts", state="visible")

        # 2. Preenche texto e seleciona voz
        self.page.fill("#ttsInputText", "Teste automatizado do Montanha Media Lab.")
        self.page.select_option("#ttsVoiceSelect", "pt-BR-FranciscaNeural")

        # 3. Clica em Adicionar à Timeline
        self.page.click("#btnTtsAddToTimeline")
        
        # 4. Aguarda a injeção do clipe na trilha de áudio
        self.page.wait_for_selector(".timeline-clip[data-type='audio']", timeout=10000)
        clips = self.page.locator(".timeline-clip[data-type='audio']")
        self.assertGreater(clips.count(), 0)

if __name__ == "__main__":
    unittest.main()
```

---

## 7. Recomendações e Checklist para a Equipe de Implementação

1. **`server.py`**:
   - Adicionar o handler `POST /api/tts` integrando `edge_tts.Communicate`.
   - Adicionar o dicionário `VALID_EDGE_VOICES` para fallback transparente de nomes de vozes Azure.
   - Corrigir a rota `/api/silence-detect` para invocar a função atualizada `engine.detect_silence_points()`.
2. **`engine.py`**:
   - Implementar `detect_silence_points(media_path)` que retorna a lista de intervalos de silêncio e segmentos de fala calculados.
3. **`public/index.html`**:
   - Reestruturar o dock esquerdo para layout vertical fino de ~56px com ícones (`Minha Mídia`, `Gravar & Criar`, `Legendas`, `Áudio`) e gaveta expansível.
   - Simplificar a barra de ferramentas superior da timeline para exibir apenas: Dividir, Desfazer, Refazer e Play.
   - Implementar o menu de contexto completo no clique com o botão direito nos clipes da timeline com atalhos de teclado (`Ctrl+D`, `Ctrl+C`, `Ctrl+V`, `Del`, `S`, `F`) e o item "Recortar Pausas e Silêncios".
   - Adicionar o dock retrátil à direita para propriedades do elemento selecionado (Volume, Velocidade, Legendas).
4. **Testes e CI**:
   - Salvar a suíte em `tests/test_e2e_edge.py` e executar `python tests/test_e2e_edge.py` garantindo que todos os 4 tiers passem no Microsoft Edge.
   - Executar `git add .`, `git commit -m "feat: clipchamp style editor and neural tts engine with edge tests"`, e `git push origin main`.

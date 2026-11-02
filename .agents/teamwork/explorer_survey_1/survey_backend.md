# Levantamento Técnico da Arquitetura Backend: Montanha Media Lab

**Data da Investigação**: 2026-11-02  
**Agente**: `teamwork_explorer` (Backend Architecture Explorer)  
**Diretório do Projeto**: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab`  
**Escopo**: Servidor HTTP local (`server.py`), motor de processamento (`engine.py`), armazenamento e streaming de mídia, portas de execução, integração `edge-tts` e detecção de silêncio/pausas com FFmpeg.

---

## 1. Visão Geral da Arquitetura do Backend

### 1.1 Framework e Tecnologias
- **Framework do Servidor**: Biblioteca padrão Python `http.server` (`HTTPServer`, `BaseHTTPRequestHandler`), implementada na classe `UnifiedMediaStudioHandler`.
- **Ausência de Frameworks Pesados**: Não utiliza Flask, FastAPI ou aiohttp no servidor principal, mantendo zero dependências externas para o servidor HTTP básico.
- **Concorrência Atual**: Atualmente instancia `HTTPServer(("0.0.0.0", port), UnifiedMediaStudioHandler)` (linha 610).
  - *Observação Crítica*: `HTTPServer` é estritamente **monothread**. Durante o streaming de vídeos em chunks (`/stream`) ou execução de tarefas como síntese de áudio ou detecção de silêncio, requisições concorrentes da interface web (ex: `/api/list-media` ou `/api/projects`) podem sofrer bloqueio ou lentidão.
  - *Recomendação Imediata*: Adotar `ThreadingHTTPServer` (`from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler`), nativo no Python 3.7+, permitindo que cada conexão seja tratada em sua própria thread sem acrescentar nenhuma dependência externa.

### 1.2 Configuração de CORS e Cabeçalhos HTTP
- O método `end_headers()` (linhas 88–93 de `server.py`) injeta:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Methods: GET, POST, OPTIONS, HEAD`
  - `Access-Control-Allow-Headers: Range, Content-Type, Authorization`
- Suporte a `do_OPTIONS` (retorna HTTP 200) e `do_HEAD` (redireciona para `do_GET`), garantindo compatibilidade total com fetch/XHR e pré-vôos de CORS.

### 1.3 Mapeamento Atual de Rotas e Endpoints

#### Rotas GET (`do_GET`):
1. `/` ou `/index.html`: Serve `public/index.html` com `Content-Type: text/html; charset=utf-8` e `Cache-Control: no-cache, no-store, must-revalidate` (linhas 106–117).
2. `/api/list-media`, `/api/get-recent-media`: Escaneia pastas de mídia (`DOWNLOADS_DIR`, `UPLOAD_DIR`, `OUTPUT_DIR`), filtra extensões (`.mp4, .mov, .mkv, .webm, .mp3, .wav, .aac, .png, .jpg, .jpeg`), coleta metadados (tamanho, mtime, duração via engine) e retorna JSON ordenado por mais recente (linhas 120–157).
3. `/api/projects`: Lista arquivos `.json` na pasta `projects/` (linhas 160–178).
4. `/stream?file=<caminho>`: Streaming HTTP 206 Byte-Range com suporte a chunks de 64 KB para reprodução sem buffer (linhas 181–192).
5. `/media/<rel_path>`: Fallback de rota direta para streaming de arquivos em `DOWNLOADS_DIR` e `UPLOAD_DIR` (linhas 194–203).
6. `/api/adb-camera`: Dispara `adb shell ls` e `adb pull` para sincronizar automaticamente gravações de câmera do celular Xiaomi Redmi 12 (linhas 206–227).
7. Arquivos estáticos em `public/`: Qualquer rota que corresponda a arquivo existente em `public/` é servida via streaming com range (linhas 229–233).

#### Rotas POST (`do_POST`):
- **Requisições JSON (`application/json`)**:
  - `/api/import-cloud-url`: Download de URL externa via `yt-dlp` ou download direto HTTP (linhas 249–283).
  - `/api/silence-detect`: Detecção de silêncio para AutoCut (linhas 286–296). *Nota: Contém bug crítico diagnosticado na Seção 5.*
  - `/api/generate-subtitles`: Geração de legendas `.srt` e `.ass` via `faster_whisper` INT8 (linhas 299–314).
  - `/api/export-final`: Renderização final com cortes, queima de legenda e enquadramento de aspecto (linhas 317–343).
  - `/api/save-project`, `/api/load-project`, `/api/delete-project`: Persistência de projetos em JSON (linhas 346–380).
  - `/api/delete-media`: Exclusão de arquivo do disco (linhas 382–392).
  - `/api/open-folder`: Abertura da pasta de mídia no explorador do SO (`os.startfile` no Windows, `xdg-open` no Linux/Termux) (linhas 394–403).
- **Requisições Multipart / Form-Data**:
  - `/api/upload`: Upload direto de vídeo, áudio ou imagem salvando em `DOWNLOADS_DIR` (linhas 411–452).
  - Ações legadas (`acao`): `download_url` (yt-dlp), `audio` (extração MP3), `pdf_indexar`, `pdf_gerar`, `foto_prompt`.

---

## 2. Armazenamento, Nomenclatura e Disponibilização de Mídias

### 2.1 Diretórios no Sistema de Arquivos
Configuração em `server.py` (linhas 32–50):
```python
BASE_DIR = Path(__file__).parent.resolve()
PUBLIC_DIR = BASE_DIR / "public"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "exports"
PROJECTS_DIR = BASE_DIR / "projects"

# Shared Media Storage (Termux Android & Windows fallback)
if os.path.exists("/sdcard/Download"):
    DOWNLOADS_DIR = Path("/sdcard/Download/MontanhaMediaLab")
else:
    DOWNLOADS_DIR = Path.home() / "Downloads" / "MontanhaMediaLab"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
```

### 2.2 Estratégia Recomendada para Áudios TTS
1. **Local de Armazenamento**: `DOWNLOADS_DIR`.
   - *No Windows*: `C:\Users\Administrator\Downloads\MontanhaMediaLab` (verificado como existente e acessível).
   - *No Celular (Termux)*: `/sdcard/Download/MontanhaMediaLab` (diretório visível nativamente na Galeria e no Gerenciador de Arquivos do Android, conforme item 2 do Dossiê Técnico).
   - *Benefício Imediato*: Como `DOWNLOADS_DIR` já faz parte do escaneamento de `/api/list-media`, qualquer áudio gerado pelo TTS torna-se instantaneamente visível na biblioteca de mídia do frontend sem nenhuma sincronização manual.
2. **Padrão de Nomenclatura**:
   - `tts_{safe_voice}_{timestamp}.mp3`
   - Exemplos: `tts_francisca_1730578800.mp3`, `tts_antonio_1730578815.mp3`.
   - Onde `{safe_voice}` é o identificador curto em minúsculas (ex: `francisca`, `antonio`, `thalita`).
3. **Serviço e URLs para o Frontend**:
   - Rota de streaming HTTP 206: `/stream?file={urllib.parse.quote(str(target_path))}`.
   - Rota direta simplificada: `/media/{filename}`.
   - *Melhoria de Robustez*: Na linha 194 de `server.py`, a rota `/media/` atualmente checa `DOWNLOADS_DIR` e `UPLOAD_DIR`. Deve-se incluir também `OUTPUT_DIR` para garantir resolução completa de qualquer arquivo de mídia gerado no sistema.

---

## 3. Gerenciamento de Portas e Vínculo de Rede (Windows vs Termux)

### 3.1 Comportamento Atual no Código
Em `server.py` (linhas 622–625):
```python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8080))
    run_server(port)
```
E em `run_server`:
```python
def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), UnifiedMediaStudioHandler)
```

### 3.2 Gaps Identificados vs Requisito R3
- **Requisito R3**: "Manter compatibilidade com execução tanto local no Windows (porta 4190 / Túnel Cloudflare) quanto no celular via Termux (porta 8080 padrão)".
- **Problema Atual**: Se o usuário rodar `python server.py` sem argumentos no Windows, a porta padrão assumida é `8080`, em vez de `4190`. No script de provisionamento da VPS e túnel (`setup_oracle_vps.sh`), a porta esperada é `4190`. No Android `MainActivity.java`, a WebView aponta para `http://localhost:8080`.
- **Solução Recomendada**:
  Implementar detecção automática de ambiente com prioridade estrita para argumentos CLI e variáveis de ambiente:
  ```python
  if __name__ == "__main__":
      is_termux = os.path.exists("/data/data/com.termux") or os.path.exists("/sdcard")
      default_port = 8080 if is_termux else (4190 if sys.platform == "win32" else 8080)
      port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else default_port))
      run_server(port)
  ```
  - `python server.py` no Windows assume automaticamente `4190`.
  - `python server.py` no Termux assume automaticamente `8080`.
  - `python server.py 4190` ou `python server.py 8080` força a porta escolhida em qualquer SO.
  - A variável `PORT=xxxx` continua funcionando para ambientes PaaS/Vercel/Docker.
  - Vínculo em `0.0.0.0` é preservado, permitindo acesso local, LAN e Cloudflare Tunnel.

---

## 4. Integração do Motor Neural Text-to-Speech (edge-tts)

### 4.1 Verificação do Ambiente de Execução
- **Pacote Instalado**: `edge-tts 7.3.1` (verificado via comando de inspeção no Python 3.11.9).
- **Assinatura da API**:
  `edge_tts.Communicate(text: str, voice: str = 'en-US-EmmaMultilingualNeural', *, rate: str = '+0%', volume: str = '+0%', pitch: str = '+0Hz', ...)`
- **Corrotina Assíncrona de Salvamento**:
  `await communicate.save(output_filename)`

### 4.2 Catálogo Homologado de Vozes Brasileiras
Foi executada a consulta empírica das vozes `pt-BR` via API do edge-tts:
1. `pt-BR-FranciscaNeural` (Feminina, tom natural, clara e profissional — padrão para narrações e tutoriais).
2. `pt-BR-AntonioNeural` (Masculino, tom firme, autoritário e dinâmico — padrão para Reels, chamadas de ação e anúncios).
3. `pt-BR-ThalitaMultilingualNeural` (Feminina, flexível e expressiva).
*(Vozes adicionais lusófonas disponíveis: `pt-PT-DuarteNeural` e `pt-PT-RaquelNeural`).*

### 4.3 Formatação de Taxa (Velocidade) e Tom (Pitch)
Testes reais com geração de arquivos `.mp3` demonstraram os seguintes formatos aceitos:
- **Taxa / Velocidade (`rate`)**:
  - Aceita strings com sinal percentual: `"+0%"`, `"+20%"`, `"+50%"`, `"-20%"`.
  - Se o frontend enviar um multiplicador numérico (ex: `1.0`, `1.2`, `1.5`, `0.8`), o backend deve converter cirurgicamente:
    ```python
    def parse_rate(rate_val) -> str:
        if isinstance(rate_val, (int, float)):
            pct = int(round((float(rate_val) - 1.0) * 100))
            return f"+{pct}%" if pct >= 0 else f"{pct}%"
        s = str(rate_val).strip()
        if not s.endswith("%"): s = f"{s}%"
        if not (s.startswith("+") or s.startswith("-")): s = f"+{s}"
        return s
    ```
- **Tom (`pitch`)**:
  - Aceita strings em Hertz com sinal: `"+0Hz"`, `"+10Hz"`, `"-5Hz"`.
  - Se o frontend enviar inteiro ou float (ex: `0`, `5`, `-10`), formata como `f"+{pitch}Hz"` ou `f"{pitch}Hz"`.

### 4.4 Execução da Corrotina em Servidor Síncrono
Para acionar a corrotina assíncrona do `edge_tts` dentro do manipulador HTTP `BaseHTTPRequestHandler`, utiliza-se `asyncio.run()` encapsulado em uma função utilitária:
```python
def generate_tts_sync(text: str, voice: str, rate_str: str, pitch_str: str, output_path: str):
    async def _async_exec():
        comm = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        await comm.save(output_path)
    asyncio.run(_async_exec())
```
*Validação*: Foi testado o isolamento de `asyncio.run` em threads secundárias do `ThreadingHTTPServer` com taxa de sucesso de 100%.

### 4.5 Duração e Metadados do Áudio Gerado
Após a escrita do `.mp3`, o backend deve calcular a duração exata do arquivo utilizando `engine.get_video_info(str(output_path))` ou `ffprobe`. Isso permite que o frontend posicione o clipe na timeline com comprimento exato em segundos (ex: `duration: 3.42`).

---

## 5. Investigação de Detecção de Silêncio e Recorte de Pausas

### 5.1 Auditoria de Bibliotecas de Áudio Locais
Executamos teste de carga das bibliotecas de áudio no ambiente Python:
- `pydub`: **NÃO disponível**
- `scipy`: **NÃO disponível**
- `soundfile`: **NÃO disponível**
- `numpy`: **DISPONÍVEL**
- `wave`: **DISPONÍVEL** (biblioteca padrão)
- `faster_whisper`: **DISPONÍVEL**
- `ffmpeg` e `ffprobe`: **DISPONÍVEIS** (versão 6.1.1 essentials)

### 5.2 Diagnóstico do Bug Existente em `server.py:292`
Ao inspecionar a rota `/api/silence-detect` em `server.py`:
```python
# server.py linhas 286-296
elif parsed.path == "/api/silence-detect":
    video_path = body.get("video_path")
    if not video_path or not os.path.exists(video_path):
        self._send_json({"status": "error", "message": "Arquivo de vídeo não encontrado"})
        return
    if engine:
        res = engine.detect_silence_points(video_path)  # <-- BUG: NÃO EXISTE EM engine.py!
        self._send_json({"status": "success", **res})
    else:
        self._send_json({"status": "error", "message": "Engine não carregada"})
    return
```
- Em `engine.py`, as funções implementadas são:
  1. `detect_silence(video_path: str, noise_db: float = -30.0, min_duration: float = 0.25) -> List[Tuple[float, float]]`
  2. `compute_speech_segments(total_duration: float, silence_intervals: List[Tuple[float, float]], margin: float = 0.08) -> List[Tuple[float, float]]`
  3. `cut_silence(input_path: str, output_path: str, ...)`
- **A função `detect_silence_points` simplesmente não foi declarada em `engine.py`!**
- Qualquer requisição a `/api/silence-detect` dispararia uma exceção `AttributeError`.

### 5.3 Teste Empírico do Filtro `silencedetect` com FFmpeg
Executamos um teste prático criando um arquivo de áudio WAV sintético com 1s de tom senoidal, 1s de silêncio e 1s de tom senoidal (duração total: 3.0s).
- `engine.detect_silence()` retornou:
  `[(0.999977, 2.00005)]` (intervalo de silêncio detectado com precisão de microssegundos).
- `engine.compute_speech_segments()` retornou:
  `[(0.0, 1.079977), (1.92005, 3.0)]` (segmentos de fala preservados com margem de segurança de 0.08s para respiração natural).
- O filtro funciona com qualquer formato de mídia suportado pelo FFmpeg (MP4, MOV, WEBM, MP3, WAV, AAC, M4A).

### 5.4 Especificação da Rota de Detecção de Silêncio
- **Nomes de Endpoint Suportados**: Aceitar tanto `/api/silence-detect` quanto `/api/detect-silence`.
- **Entrada Flexível**: Aceitar `video_path`, `audio_path`, `media_path` ou `file_path` no JSON do corpo da requisição.
- **Parâmetros Opcionais**:
  - `noise_db`: nível de limiar de ruído (padrão: `-30.0` dB, ajustável entre `-20` e `-45` dB).
  - `min_duration`: tempo mínimo de silêncio contínuo para considerar pausa (padrão: `0.25` s).
- **Resposta Estruturada para a Timeline**:
  ```json
  {
    "status": "success",
    "duration": 15.4,
    "silences": [
      {"start": 2.45, "end": 3.80, "duration": 1.35},
      {"start": 7.10, "end": 8.50, "duration": 1.40}
    ],
    "speech_segments": [
      {"start": 0.00, "end": 2.53, "duration": 2.53},
      {"start": 3.72, "end": 7.18, "duration": 3.46},
      {"start": 8.42, "end": 15.40, "duration": 6.98}
    ],
    "silence_count": 2,
    "speech_count": 3,
    "saved_seconds": 2.75
  }
  ```
  Isso permite que o frontend execute a divisão funcional na timeline instantaneamente, transformando um clipe único nos 3 segmentos de fala úteis.

---

## 6. Blueprint Detalhado das Alterações Recomendadas

### 6.1 Adições em `engine.py`

Implementar a função faltante `detect_silence_points`:

```python
def detect_silence_points(media_path: str, noise_db: float = -30.0, min_duration: float = 0.25) -> Dict[str, Any]:
    """
    Detecta intervalos de silêncio e calcula os segmentos úteis de fala/áudio ativo.
    Compatível com arquivos de vídeo (.mp4, .mov, .mkv) e de áudio (.mp3, .wav, .aac).
    """
    info = get_video_info(media_path)
    total_dur = info.get("duration", 0.0)
    
    silence_intervals = detect_silence(media_path, noise_db=noise_db, min_duration=min_duration)
    speech_segments = compute_speech_segments(total_dur, silence_intervals)
    
    silences_data = [
        {"start": round(s, 2), "end": round(e, 2), "duration": round(e - s, 2)}
        for s, e in silence_intervals
    ]
    speech_data = [
        {"start": round(s, 2), "end": round(e, 2), "duration": round(e - s, 2)}
        for s, e in speech_segments
    ]
    saved = sum(item["duration"] for item in silences_data)
    
    return {
        "status": "success",
        "duration": round(total_dur, 2),
        "silences": silences_data,
        "speech_segments": speech_data,
        "silence_count": len(silences_data),
        "speech_count": len(speech_data),
        "saved_seconds": round(saved, 2)
    }
```

### 6.2 Adições em `server.py`

#### A. Troca de `HTTPServer` para `ThreadingHTTPServer`:
```python
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

def run_server(port=8080):
    server = ThreadingHTTPServer(("0.0.0.0", port), UnifiedMediaStudioHandler)
    ...
```

#### B. Novo Endpoint `GET /api/tts/voices` ou `GET /api/tts-voices`:
```python
elif parsed.path in ["/api/tts/voices", "/api/tts-voices"]:
    voices = [
        {
            "id": "pt-BR-FranciscaNeural",
            "name": "Francisca (Neural)",
            "gender": "Feminino",
            "locale": "pt-BR",
            "style": "Natural, suave e didática"
        },
        {
            "id": "pt-BR-AntonioNeural",
            "name": "Antonio (Neural)",
            "gender": "Masculino",
            "locale": "pt-BR",
            "style": "Firme, autoritário e dinâmico"
        },
        {
            "id": "pt-BR-ThalitaMultilingualNeural",
            "name": "Thalita (Multilíngue)",
            "gender": "Feminino",
            "locale": "pt-BR",
            "style": "Expressiva e flexível"
        }
    ]
    self._send_json({"status": "success", "voices": voices})
    return
```

#### C. Novo Endpoint `POST /api/tts`:
```python
elif parsed.path == "/api/tts":
    text = (body.get("text") or "").strip()
    voice = body.get("voice") or "pt-BR-FranciscaNeural"
    rate = body.get("rate") or "+0%"
    pitch = body.get("pitch") or "+0Hz"
    
    if not text:
        self._send_json({"status": "error", "message": "Texto não fornecido para síntese"}, 400)
        return
        
    try:
        import asyncio
        import edge_tts
        
        # Formatação de velocidade
        if isinstance(rate, (int, float)):
            pct = int(round((float(rate) - 1.0) * 100))
            rate_str = f"+{pct}%" if pct >= 0 else f"{pct}%"
        else:
            r_s = str(rate).strip()
            if not r_s.endswith("%"): r_s = f"{r_s}%"
            if not (r_s.startswith("+") or r_s.startswith("-")): r_s = f"+{r_s}"
            rate_str = r_s
            
        # Formatação de tom
        if isinstance(pitch, (int, float)):
            pitch_str = f"+{int(pitch)}Hz" if pitch >= 0 else f"{int(pitch)}Hz"
        else:
            p_s = str(pitch).strip()
            if not (p_s.endswith("Hz") or p_s.endswith("%")): p_s = f"{p_s}Hz"
            if not (p_s.startswith("+") or p_s.startswith("-")): p_s = f"+{p_s}"
            pitch_str = p_s

        voice_tag = voice.replace("pt-BR-", "").replace("Neural", "").lower()
        out_name = f"tts_{voice_tag}_{int(time.time() * 1000)}.mp3"
        out_file = DOWNLOADS_DIR / out_name

        async def _run_tts():
            comm = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
            await comm.save(str(out_file))

        asyncio.run(_run_tts())

        # Obter duração do áudio gerado
        duration = 0.0
        if engine:
            try:
                info = engine.get_video_info(str(out_file))
                duration = info.get("duration", 0.0)
            except Exception:
                duration = 0.0

        self._send_json({
            "status": "success",
            "filename": out_name,
            "server_path": str(out_file),
            "download_url": f"/stream?file={urllib.parse.quote(str(out_file))}",
            "media_url": f"/media/{out_name}",
            "duration": duration,
            "voice": voice,
            "text": text
        })
    except Exception as err:
        self._send_json({"status": "error", "message": f"Erro na geração de TTS: {str(err)}"}, 500)
    return
```

#### D. Ajuste da Rota de Silêncio para Aceitar `/api/silence-detect` e `/api/detect-silence`:
```python
elif parsed.path in ["/api/silence-detect", "/api/detect-silence"]:
    media_path = body.get("video_path") or body.get("audio_path") or body.get("media_path") or body.get("file_path")
    noise_db = float(body.get("noise_db", -30.0))
    min_duration = float(body.get("min_duration", 0.25))

    if not media_path or not os.path.exists(media_path):
        self._send_json({"status": "error", "message": "Arquivo de mídia não encontrado"}, 400)
        return

    if engine and hasattr(engine, "detect_silence_points"):
        try:
            res = engine.detect_silence_points(media_path, noise_db=noise_db, min_duration=min_duration)
            self._send_json({"status": "success", **res})
        except Exception as err:
            self._send_json({"status": "error", "message": f"Erro ao detectar silêncio: {str(err)}"}, 500)
    else:
        # Fallback local direto caso engine não possua o método
        try:
            silences = engine.detect_silence(media_path, noise_db=noise_db, min_duration=min_duration) if engine else []
            info = engine.get_video_info(media_path) if engine else {}
            total_dur = info.get("duration", 0.0)
            speech = engine.compute_speech_segments(total_dur, silences) if engine else []
            self._send_json({
                "status": "success",
                "duration": total_dur,
                "silences": [{"start": s, "end": e, "duration": round(e - s, 2)} for s, e in silences],
                "speech_segments": [{"start": s, "end": e, "duration": round(e - s, 2)} for s, e in speech],
                "silence_count": len(silences),
                "speech_count": len(speech)
            })
        except Exception as err:
            self._send_json({"status": "error", "message": f"Erro na análise de áudio: {str(err)}"}, 500)
    return
```

#### E. Fallback Aprimorado na Rota `/media/`:
Adicionar verificação em `OUTPUT_DIR` para garantir resolução completa:
```python
elif parsed.path.startswith("/media/"):
    rel_path = parsed.path.replace("/media/", "")
    target_path = (DOWNLOADS_DIR / rel_path).resolve()
    if not target_path.exists():
        target_path = (UPLOAD_DIR / rel_path).resolve()
    if not target_path.exists():
        target_path = (OUTPUT_DIR / rel_path).resolve()
    if not target_path.exists() or not target_path.is_file():
        self.send_error(404, "Media not found")
        return
    self._serve_file_with_range(target_path)
    return
```

---

## 7. Verificação e Testes Ponta a Ponta Automatizados

- **Playwright com Microsoft Edge**:
  O pacote Playwright está instalado globalmente (versão 1.64.1) e disponível no Python e Node.js.
  Para satisfazer R4 com Microsoft Edge, os testes e2e devem iniciar o navegador apontando para `channel: "msedge"`:
  ```javascript
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  ```
- **Fluxo de Teste de Backend e TTS**:
  1. Iniciar servidor em `http://127.0.0.1:4190`.
  2. Disparar `POST /api/tts` com payload `{"text": "Teste Playwright", "voice": "pt-BR-FranciscaNeural"}`.
  3. Validar retorno HTTP 200, existência do arquivo `.mp3` em disco com tamanho > 0 bytes e duração > 0.
  4. Validar requisição `GET /media/tts_...mp3` e `/stream?file=...` retornando HTTP 200 ou 206.
  5. Disparar `POST /api/silence-detect` com o arquivo gerado e verificar retorno de `silences` e `speech_segments`.

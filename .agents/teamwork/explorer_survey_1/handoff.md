# Handoff Report — Backend Architecture Survey

**Agent**: `teamwork_explorer` (Backend Architecture Explorer)  
**Parent**: `1b0d68f6-227f-4ee4-b45c-46a635262c12`  
**Working Directory**: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1`  
**Report File**: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1\survey_backend.md`  

---

## 1. Observation

1. **Servidor HTTP e Concorrência**:
   - `server.py` utiliza `http.server.HTTPServer` com `UnifiedMediaStudioHandler(BaseHTTPRequestHandler)` (linhas 22, 87, 610).
   - O servidor escuta em `0.0.0.0` com porta configurada por `port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8080))` (linha 623).
   - No Windows, a porta padrão no código é atualmente 8080 caso nenhum argumento ou variável de ambiente seja fornecida, enquanto o requisito R3 e `setup_oracle_vps.sh` esperam a porta 4190 para Windows e 8080 para Termux.

2. **Armazenamento e Roteamento de Mídia**:
   - `DOWNLOADS_DIR` aponta para `/sdcard/Download/MontanhaMediaLab` no Termux ou `Path.home() / "Downloads" / "MontanhaMediaLab"` no Windows (`C:\Users\Administrator\Downloads\MontanhaMediaLab`) (linhas 38–42).
   - `/api/list-media` varre `DOWNLOADS_DIR`, `UPLOAD_DIR` e `OUTPUT_DIR` para extensões válidas (`.mp4, .mov, .mkv, .webm, .mp3, .wav, .aac, .png, .jpg, .jpeg`) (linhas 120–136).
   - `/stream?file=...` fornece streaming HTTP 206 Byte-Range em blocos de 64 KB (linhas 181–192).
   - `/media/<rel_path>` verifica `DOWNLOADS_DIR` e `UPLOAD_DIR`, mas omite `OUTPUT_DIR` (linhas 194–203).

3. **Instalação e Suporte de `edge-tts`**:
   - Execução do comando de inspeção: `python -c "import edge_tts; print(edge_tts.__version__)"` retornou `7.3.1` sob Python 3.11.9.
   - Listagem de vozes brasileiras (`pt-BR`) retornou três opções neurais oficiais:
     - `pt-BR-FranciscaNeural` (Feminino)
     - `pt-BR-AntonioNeural` (Masculino)
     - `pt-BR-ThalitaMultilingualNeural` (Feminino)
   - Teste de síntese com taxas e tons distintos (`rate='+0%', pitch='+0Hz'`, `rate='+50%', pitch='+10Hz'`, `rate='-20%', pitch='-5Hz'`) gerou arquivos `.mp3` válidos com sucesso (tamanhos: 11520, 11232 e 14256 bytes).

4. **Detecção de Silêncio e Recorte de Pausas**:
   - Em `server.py` linhas 286–296:
     ```python
     elif parsed.path == "/api/silence-detect":
         video_path = body.get("video_path")
         ...
         if engine:
             res = engine.detect_silence_points(video_path)
     ```
   - Em `engine.py`, uma busca exata por `detect_silence_points` retornou zero correspondências. A função `detect_silence_points` não está implementada em `engine.py`, gerando `AttributeError` em tempo de execução.
   - As funções existentes em `engine.py` são `detect_silence(video_path, noise_db, min_duration)`, `compute_speech_segments(total_duration, silence_intervals, margin)` e `cut_silence(...)` (linhas 141–240).
   - Teste empírico com áudio sintetizado de 3.0s (1s sinal, 1s silêncio, 1s sinal) validou que `engine.detect_silence` identificou com precisão o intervalo `[(0.999977, 2.00005)]` e preservou os segmentos de fala `[(0.0, 1.079977), (1.92005, 3.0)]`.
   - As ferramentas `ffmpeg` (6.1.1) e `ffprobe` estão operacionais no sistema. Pacotes opcionais `pydub`, `scipy` e `soundfile` não estão instalados no Python, mas `ffmpeg silencedetect` supre 100% da necessidade sem bibliotecas de terceiros.

---

## 2. Logic Chain

1. **Concorrência e Streaming**:
   - Como `server.py` emprega `HTTPServer` (monothread), streams abertos em `/stream` mantêm conexões ativas que bloqueiam novas chamadas à API.
   - Como `ThreadingHTTPServer` faz parte da biblioteca padrão do Python 3.7+ (`http.server`), sua adoção direta resolve a concorrência sem adicionar pacotes externos.

2. **Armazenamento e Exibição de TTS**:
   - Como `DOWNLOADS_DIR` já é indexado automaticamente por `/api/list-media`, salvar os arquivos gerados por `edge-tts` em `DOWNLOADS_DIR` com prefixo `tts_` garante persistência imediata, visualização na biblioteca do editor e acesso pela Galeria do celular no Termux (`/sdcard/Download/MontanhaMediaLab`).
   - Fornecer tanto a rota `/stream?file=...` quanto a rota amigável `/media/tts_...mp3` garante compatibilidade instantânea com tags de áudio HTML5 e manipulação na timeline.

3. **Detecção e Resolução de Portas**:
   - No Windows, a aplicação deve rodar preferencialmente na porta 4190 para evitar conflitos locais e atender ao Túnel Cloudflare (`setup_oracle_vps.sh`).
   - No celular (Termux/Android), a WebView do `MainActivity.java` acessa estritamente `http://localhost:8080`.
   - Checar se o ambiente possui `/sdcard` ou `/data/data/com.termux` define deterministicamente a porta padrão (8080 para Termux, 4190 para Windows), mantendo a precedência de `sys.argv[1]` e da variável de ambiente `PORT`.

4. **Correção do Bug de Detecção de Silêncio**:
   - Como `server.py` referencia `engine.detect_silence_points()`, a ausência deste método em `engine.py` quebra a funcionalidade de detecção de silêncio solicitada em R2 ("Submenu Sugestões de IA: Recortar Pausas e Silêncios").
   - Implementar `detect_silence_points` em `engine.py` utilizando as funções já existentes `detect_silence` e `compute_speech_segments`, e unificar os endpoints `POST /api/silence-detect` e `POST /api/detect-silence` em `server.py`, restaura o pipeline de AutoCut com retorno estruturado de silêncios e segmentos de fala.

---

## 3. Caveats

- **Conectividade de Rede para `edge-tts`**: O `edge-tts` depende dos servidores do Microsoft Edge na nuvem. Se o dispositivo estiver 100% offline sem internet, a geração de TTS retornará erro; o backend deve tratar a exceção graciosamente com JSON de erro claro (HTTP 500) em vez de quebrar o processo.
- **Formato dos Arquivos na Detecção de Silêncio**: Para arquivos de áudio puro (sem trilha de vídeo), o `ffprobe` e `ffmpeg` funcionam perfeitamente no filtro `-af silencedetect`, porém o parâmetro deve aceitar tanto chaves `video_path` quanto `audio_path` ou `media_path`.
- **Interface e Testes**: Este levantamento cobriu exclusivamente a camada de arquitetura do backend, rotas, dependências e processamento de mídia. A reformulação visual da interface e os testes Playwright foram catalogados no dossiê técnico e serão executados pelos agentes das fases seguintes.

---

## 4. Conclusion

O backend do `montanha-media-lab` possui uma fundação sólida, leve e sem dependências pesadas, utilizando a biblioteca padrão do Python e FFmpeg. Para atender aos requisitos R1, R2 e R3 com robustez de produção:
1. Atualizar o servidor HTTP para `ThreadingHTTPServer`.
2. Adicionar o endpoint `POST /api/tts` (gerando `.mp3` via `edge-tts` em `DOWNLOADS_DIR` com controle de voz brasileira, velocidade e tom) e o endpoint auxiliar `GET /api/tts/voices`.
3. Adicionar `detect_silence_points` em `engine.py` e mapear `POST /api/detect-silence` (com alias para `/api/silence-detect`) em `server.py`, retornando intervalos de pausa e segmentos de fala.
4. Ajustar o binding de porta para 4190 no Windows e 8080 no Termux por padrão.
5. Expandir o fallback de `/media/` para incluir `OUTPUT_DIR`.

O relatório técnico completo com blueprints de código encontra-se em:  
`C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1\survey_backend.md`.

---

## 5. Verification Method

Para verificar independentemente as constatações deste levantamento:

1. **Verificação de `edge-tts`**:
   ```powershell
   python -c "import edge_tts; print(edge_tts.__version__)"
   python -c "import asyncio, edge_tts; print([v['ShortName'] for v in asyncio.run(edge_tts.list_voices()) if v['Locale'].startswith('pt-BR')])"
   ```
2. **Constatação do Bug em `engine.py`**:
   ```powershell
   python -c "import sys; sys.path.insert(0, 'C:\\Users\\Administrator\\Documents\\Projetos\\montanha-media-lab'); import engine; print(hasattr(engine, 'detect_silence_points'))"
   ```
   *Resultado esperado*: `False` (confirma que o método chamado na linha 292 de `server.py` está ausente).
3. **Validação do Filtro FFmpeg Silencedetect**:
   ```powershell
   python -c "import sys; sys.path.insert(0, 'C:\\Users\\Administrator\\Documents\\Projetos\\montanha-media-lab'); import engine; print(engine.detect_silence)"
   ```
   *Resultado esperado*: Função presente e utilizável com FFmpeg 6.1.1.
4. **Verificação da Rota de Porta Padrão**:
   Inspecionar linha 623 de `server.py` para confirmar `sys.argv[1] if len(sys.argv) > 1 else 8080`.

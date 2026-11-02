# Project: Montanha Media Lab - Neural TTS & Clipchamp Editor Redesign

## Architecture
- **Backend**: Python 3.11 with `ThreadingHTTPServer` (`server.py`), `engine.py` for FFmpeg processing, `edge-tts` for neural speech synthesis.
- **Frontend**: Single-page studio interface in `public/index.html` and `public/theme.css` with modular component architecture:
  - 56px left vertical dock (`#clipchampVerticalDock`) with icons for Minha Mídia, Gravar & Criar (TTS), Legendas, and Áudio.
  - Expandable drawer (`#clipchampDrawer`, ~340px) with collapsible state.
  - Center workspace with video player (`#playerFrame`, `#studioVideo`) and canvas container.
  - Retractable right inspector dock (`#rightInspectorPanel`) for properties (Volume, Velocidade, Legendas).
  - Ultra-minimalist bottom timeline toolbar (`#bottomTimelineToolbar`) containing strictly: Dividir/Tesoura, Desfazer, Refazer, Play/Pause.
  - Multi-track timeline supporting video, audio (Track 5), b-roll, captions, with floating context menu on clip right-click.
- **Testing**: Playwright (v1.64.0) with native Microsoft Edge (`channel: 'msedge'`) via Python standard library `unittest`.

## Code Layout
- `server.py`: HTTP server, routing, endpoints (`/api/tts`, `/api/tts/voices`, `/api/detect-silence`, `/api/silence-detect`, `/stream`, `/media/`), port configuration (4190 Windows / 8080 Termux).
- `engine.py`: Video/audio processing, `detect_silence_points()`, `detect_silence()`, `compute_speech_segments()`.
- `public/index.html`: Studio UI markup, Clipchamp layout elements, TTS configuration panel, context menu, modal drawers, and timeline client logic.
- `public/theme.css`: Clipchamp-style styling, 56px dock, floating context menu, minimalist buttons, responsive layout.
- `tests/test_e2e_edge.py`: Playwright on Microsoft Edge E2E test suite (Tiers 1-4).
- `tests/test_m1_backend.py`: Backend and engine unit tests.
- `tests/test_m1_challenger.py`: Concurrency and edge case stress tests.
- `tests/test_m1_adversarial.py`: Directory traversal and port resolution security tests.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Server Concurrency & Threading | Update `server.py` to `ThreadingHTTPServer` | M1 | survey_backend |
| 2 | Edge-TTS Integration & Voice Filtering | Integrate `edge-tts 7.3.1` with pt-BR voices (`Francisca`, `Antonio`, `Thalita`) & parameter formatting | M1 | survey_backend / survey_testing |
| 3 | Endpoint `POST /api/tts` | Synthesize `.mp3` to `DOWNLOADS_DIR`, return JSON with url, duration, and metadata | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Endpoint `GET /api/tts/voices` | Catalog available Brazilian neural voices for frontend dropdown | M1 | survey_backend |
| 5 | Silence Detection Backend & Engine Fix | Implement `detect_silence_points()` in `engine.py` & wire `/api/detect-silence` + `/api/silence-detect` | M1 | survey_backend / survey_testing |
| 6 | Environment & Port Auto-detection | Bind port 4190 on Windows, 8080 on Termux, respect CLI args & PORT env | M1 | ORIGINAL_REQUEST §R3 |
| 7 | Left Vertical Dock (~56px) | Thin icons rail for Minha Mídia, Gravar & Criar (TTS), Legendas, Áudio | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Expandable Left Drawer | Side drawer (~340px) for active tool, keeping player and timeline centered | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Frontend TTS Panel & Preview | Voice selector, rate/pitch sliders, audio preview player, and "Adicionar à Timeline" button | M2 | ORIGINAL_REQUEST §R1 |
| 10 | Ultra-Minimalist Timeline Toolbar | Strictly 4 controls: Dividir/Tesoura, Desfazer, Refazer, Play/Pause | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Clip Right-Click Context Menu | Floating menu on right click with keyboard shortcuts: Ctrl+D, Ctrl+C, Ctrl+V, Del, S, F, Rename | M2 | ORIGINAL_REQUEST §R2 |
| 12 | Context Menu Audio Submenu | Mudo (Mute/Unmute) and Desanexar Áudio (detach audio to audio track) | M2 | ORIGINAL_REQUEST §R2 |
| 13 | Context Menu AI Suggestions Submenu | Recortar Pausas e Silêncios with automatic silence detection & functional timeline ripple split | M2 | ORIGINAL_REQUEST §R2 |
| 14 | Retractable Right Properties Dock | Dock for element properties (Volume, Velocidade, Legendas) with toggle | M2 | ORIGINAL_REQUEST §R2 |
| 15 | Playwright Edge E2E Test Suite | Automated test suite on Microsoft Edge covering Tiers 1-4 (TTS, UI, shortcuts, silence cut) | M3 | ORIGINAL_REQUEST §R4 |
| 16 | Production Git Sync | Commit all changes and push cleanly to `origin main` | M4 | ORIGINAL_REQUEST §R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Neural TTS & Engine Services | `server.py`, `engine.py`, `edge-tts` integration, `POST /api/tts`, `detect_silence_points`, port auto-bind | none | DONE |
| M2 | Clipchamp-Style Frontend Editor Redesign | `public/index.html`, `public/theme.css`: 56px dock, drawer, TTS panel, minimalist toolbar, context menu, shortcuts, right dock | M1 | DONE |
| M3 | E2E Testing Suite (Playwright on Edge) | `TEST_INFRA.md`, `tests/test_e2e_edge.py` (Tiers 1-4), `TEST_READY.md` | M1, M2 | DONE |
| M4 | Final Integration, Audit & Git Sync | Run 100% E2E tests, forensic audit gate, git commit and `git push origin main` | M1, M2, M3 | DONE |

## Interface Contracts
### Frontend ↔ Backend: `POST /api/tts`
- Request: `application/json`
  ```json
  {
    "text": "Texto a ser falado",
    "voice": "pt-BR-FranciscaNeural",
    "rate": "+0%",
    "pitch": "+0Hz"
  }
  ```
- Response (HTTP 200):
  ```json
  {
    "status": "success",
    "filename": "tts_francisca_1730578800_a1b2c3.mp3",
    "server_path": "C:\\Users\\Administrator\\Downloads\\MontanhaMediaLab\\tts_francisca_1730578800_a1b2c3.mp3",
    "download_url": "/stream?file=...",
    "media_url": "/media/tts_francisca_1730578800_a1b2c3.mp3",
    "duration": 4.12,
    "voice": "pt-BR-FranciscaNeural",
    "text": "Texto a ser falado"
  }
  ```

### Frontend ↔ Backend: `POST /api/detect-silence` / `POST /api/silence-detect`
- Request: `application/json`
  ```json
  {
    "media_path": "caminho_ou_url_do_arquivo",
    "noise_db": -30.0,
    "min_duration": 0.4
  }
  ```
- Response (HTTP 200):
  ```json
  {
    "status": "success",
    "duration": 12.5,
    "silences": [{"start": 2.0, "end": 3.5, "duration": 1.5}],
    "speech_segments": [{"start": 0.0, "end": 2.0, "duration": 2.0}, {"start": 3.5, "end": 12.5, "duration": 9.0}],
    "silence_count": 1,
    "speech_count": 2,
    "saved_seconds": 1.5
  }
  ```

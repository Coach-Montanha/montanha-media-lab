# BRIEFING — 2026-11-02T19:53:00Z

## Mission
Technical survey of backend architecture in montanha-media-lab (server.py, static file serving, port binding, edge-tts, silence detection, endpoints).

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend Architecture Explorer
- Working directory: C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1
- Original parent: 1b0d68f6-227f-4ee4-b45c-46a635262c12
- Milestone: milestone-1-survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Write only to working directory: C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1
- 5-Component handoff report + send_message to parent

## Current Parent
- Conversation ID: 1b0d68f6-227f-4ee4-b45c-46a635262c12
- Updated: not yet

## Investigation State
- **Explored paths**: `server.py`, `engine.py`, `api/index.py`, `package.json`, `setup_oracle_vps.sh`, `android/MainActivity.java`, `public/index.html`, `public/theme.css`
- **Key findings**:
  1. Server is built on Python standard library `http.server.HTTPServer` (monothread). Should upgrade to `ThreadingHTTPServer` to avoid request stalling.
  2. `edge-tts 7.3.1` is installed and verified working with Brazilian voices (`pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaMultilingualNeural`) and speed/pitch adjustments (`+0%`, `+50%`, `-20%`, `+10Hz`).
  3. `server.py:292` has a critical bug calling nonexistent `engine.detect_silence_points()`. `engine.py` defines `detect_silence()` and `compute_speech_segments()`.
  4. FFmpeg 6.1.1 is available and its `silencedetect` filter works fast on all audio/video formats. Pydub/scipy are absent but not needed.
  5. Port binding currently defaults to 8080 everywhere; needs smart default of 4190 on Windows and 8080 on Termux, preserving CLI args and `PORT` env var.
  6. TTS files should be written to `DOWNLOADS_DIR` (`tts_{voice}_{timestamp}.mp3`), which automatically registers in `/api/list-media` and gallery.
- **Unexplored areas**: Frontend UI overhaul and Playwright test suite implementation (delegated to subsequent roles).

## Key Decisions Made
- Fully surveyed backend code, empirical test runs completed, and detailed implementation blueprints documented in `survey_backend.md`.

## Artifact Index
- DISPATCH.md — Initial dispatch message
- progress.md — Liveness & task progress
- survey_backend.md — Comprehensive backend survey report
- handoff.md — Standard 5-component handoff report

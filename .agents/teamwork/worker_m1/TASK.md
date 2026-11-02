# Task Assignment for Worker M1: Backend Neural TTS & Engine Services

## Work Product Files Owned Exclusively
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\server.py`
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\engine.py`

## Inputs
- `ORIGINAL_REQUEST.md`: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\ORIGINAL_REQUEST.md`
- `PROJECT.md`: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\PROJECT.md`
- Backend Survey: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1\survey_backend.md`
- Testing Specs Survey: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_3\survey_testing_specs.md`

## Objectives
1. Implement `detect_silence_points()` in `engine.py`.
2. Upgrade `server.py` to `ThreadingHTTPServer`.
3. Implement `POST /api/tts` with `edge-tts` async execution, audio duration retrieval, Brazilian voices fallback mapping, and parameter formatting.
4. Implement `GET /api/tts/voices` and `GET /api/tts-voices`.
5. Support `POST /api/detect-silence` and `POST /api/silence-detect` with structured JSON output.
6. Configure port binding: 4190 on Windows, 8080 on Termux, CLI args and PORT env precedence.
7. Expand `/media/` fallback to `OUTPUT_DIR`.
8. Execute verification tests and report results in `handoff.md`.

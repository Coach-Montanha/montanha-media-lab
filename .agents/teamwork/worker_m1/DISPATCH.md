## 2026-11-02T19:58:07Z
You are teamwork_worker (Backend & Engine Worker) executing Milestone M1: Backend Neural TTS & Engine Services.
Your working directory is: C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\worker_m1
Parent conversation ID: 1b0d68f6-227f-4ee4-b45c-46a635262c12

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEPS:
1. Read C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\ORIGINAL_REQUEST.md completely.
2. Read C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\PROJECT.md completely.
3. Read C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_1\survey_backend.md for the complete technical blueprint and verified edge-tts code patterns.

YOUR WRITE OWNERSHIP:
You EXCLUSIVELY own and may modify:
- C:\Users\Administrator\Documents\Projetos\montanha-media-lab\server.py
- C:\Users\Administrator\Documents\Projetos\montanha-media-lab\engine.py
Do NOT touch public/index.html or public/theme.css.

SPECIFIC OBJECTIVES:
1. In engine.py:
   - Implement `detect_silence_points(media_path: str, noise_db: float = -30.0, min_duration: float = 0.25) -> Dict[str, Any]` which wraps `detect_silence()` and `compute_speech_segments()`, returning structured dictionary with duration, silences, speech_segments, silence_count, speech_count, and saved_seconds (see survey_backend.md §6.1).
2. In server.py:
   - Upgrade HTTP server class from `HTTPServer` to `ThreadingHTTPServer` from `http.server`.
   - Implement `GET /api/tts/voices` and `GET /api/tts-voices` returning verified pt-BR neural voices (Francisca, Antonio, Thalita).
   - Implement `POST /api/tts`: receives JSON `text`, `voice`, `rate`, `pitch`. Uses `edge-tts 7.3.1` (async Communicate saved to DOWNLOADS_DIR with name `tts_{voice}_{timestamp}.mp3`). Formats rate (e.g. `+0%`, `+20%`, `-10%`) and pitch (e.g. `+0Hz`). Computes audio duration via engine.get_video_info. Returns JSON response with `status: "success"`, `filename`, `server_path`, `download_url`, `media_url`, `duration`, `voice`, `text`. Implements defensive voice fallback mapping.
   - Implement `POST /api/detect-silence` and `POST /api/silence-detect`: accepts `video_path`, `audio_path`, `media_path`, or `file_path`, calls `engine.detect_silence_points()`, returns structured JSON.
   - Configure smart port binding in `server.py`:
     Default to port 4190 on Windows (win32), 8080 on Termux (check `/sdcard` or `/data/data/com.termux`). Give precedence to `sys.argv[1]` and `os.environ.get("PORT")`.
   - Update `/media/` handler in server.py to check DOWNLOADS_DIR, UPLOAD_DIR, and OUTPUT_DIR.
3. Verification:
   - Write and execute a python test script to verify:
     a) Python syntax validity of server.py and engine.py.
     b) `engine.detect_silence_points` functions properly.
     c) `server.py` port resolution logic.
     d) Synthesis via `edge-tts` with Brazilian voice.
4. Document all changes and verification results in C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\worker_m1\handoff.md and notify parent via send_message.

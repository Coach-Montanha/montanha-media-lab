# Forensic Audit Report: Milestone M1 — Backend Neural TTS & Engine Services

## Forensic Audit Summary

**Work Product**: Milestone M1 (`server.py`, `engine.py`, `tests/test_m1_backend.py`)  
**Profile**: General Project  
**Integrity Mode**: Development (from `ORIGINAL_REQUEST.md:8`)  
**Verdict**: **CLEAN**

---

### Phase Results
- **Hardcoded Output Detection**: **PASS** — No dummy responses, mock payloads, or hardcoded test strings found. `POST /api/tts` in `server.py:320-416` genuinely invokes `edge_tts.Communicate(...).save(...)` generating physical `.mp3` files on disk, and duration is dynamically calculated using `engine.get_video_info`.
- **Facade Implementation Detection**: **PASS** — `engine.detect_silence_points` in `engine.py:191-224` genuinely executes `ffmpeg -af silencedetect` via subprocess, parses live stderr markers (`silence_start:`, `silence_end:`), and computes real speech intervals via `compute_speech_segments`.
- **Pre-populated Artifact Detection**: **PASS** — Scan across the repository for pre-existing `*.log`, `*output*`, or `*result*` files returned 0 matches.
- **Behavioral & Test Suite Execution**: **PASS** — Independent execution of `python -m unittest tests.test_m1_backend -v` succeeded with 8/8 tests passing in 9.45 seconds. Physical MP3 inspection via `ffprobe` confirmed genuine MPEG audio (24kHz, mono, 48kbps).
- **Integrity Mode Enforcement (Development Mode)**: **PASS** — No violations of development mode constraints. All third-party libraries (`edge-tts`, `ffmpeg`) provide auxiliary media processing, and all internal logic is authentically implemented.

---

## 1. Observation

1. **Source Code Inspection**:
   - `server.py:22`: Upgraded to `from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler`.
   - `server.py:125-150`: Genuine JSON catalog for Brazilian neural voices (`pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaMultilingualNeural`) served on `/api/tts/voices` and `/api/tts-voices`.
   - `server.py:227-240`: `/media/<path>` safely resolves files across `DOWNLOADS_DIR`, `UPLOAD_DIR`, and `OUTPUT_DIR`.
   - `server.py:320-416`: `POST /api/tts` normalizes voice strings (defensive fallback), formats rate and pitch parameters, executes `asyncio.run(_run_tts())` with `edge_tts.Communicate`, creates physical file `tts_{voice}_{timestamp}.mp3`, reads duration via `engine.get_video_info`, and returns metadata with media stream URLs.
   - `server.py:418-482`: `POST /api/detect-silence` and `POST /api/silence-detect` accept multiple path keys, resolve files across media directories, and call `engine.detect_silence_points`.
   - `server.py:794-817`: `get_default_port()` prioritizes `sys.argv[1]` > `os.environ["PORT"]` > platform detection (Windows `4190`, Termux `8080`).
   - `engine.py:30-33`: `get_video_info()` handles audio-only containers (.mp3, .wav) with audio stream duration and codec fallback.
   - `engine.py:191-224`: `detect_silence_points()` executes `detect_silence()` via `ffmpeg -af silencedetect` and calls `compute_speech_segments()`.

2. **Artifact & Physical File Inspection**:
   - Generated files in `C:\Users\Administrator\Downloads\MontanhaMediaLab`:
     ```
     Name                         Length LastWriteTime
     ----                         ------ -------------
     tts_francisca_1793650255.mp3  12528 02/11/2026 17:10:57
     tts_thalita_1793650254.mp3    13680 02/11/2026 17:10:55
     tts_antonio_1793650253.mp3    16992 02/11/2026 17:10:54
     tts_francisca_1793650251.mp3  16128 02/11/2026 17:10:53
     tts_antonio_1793650250.mp3    23184 02/11/2026 17:10:51
     ```
   - Running `ffprobe -v quiet -print_format json -show_format -show_streams C:\Users\Administrator\Downloads\MontanhaMediaLab\tts_antonio_1793650250.mp3`:
     ```json
     {
       "streams": [
         {
           "codec_name": "mp3",
           "codec_long_name": "MP3 (MPEG audio layer 3)",
           "codec_type": "audio",
           "sample_rate": "24000",
           "channels": 1,
           "duration": "3.864000",
           "bit_rate": "48000"
         }
       ],
       "format": {
         "format_name": "mp3",
         "duration": "3.864000",
         "size": "23184"
       }
     }
     ```

3. **Subprocess Silence Detection Execution**:
   - Running `python -c "import engine; print(engine.detect_silence_points(r'C:\Users\Administrator\Downloads\MontanhaMediaLab\tts_antonio_1793650250.mp3'))"`:
     ```python
     {'status': 'success', 'duration': 3.86, 'silences': [{'start': 3.14, 'end': 3.86, 'duration': 0.72}], 'speech_segments': [{'start': 0.0, 'end': 3.22, 'duration': 3.22}, {'start': 3.78, 'end': 3.86, 'duration': 0.08}], 'silence_count': 1, 'speech_count': 2, 'saved_seconds': 0.72}
     ```

4. **Independent Test Suite Execution**:
   - Executing `python -m unittest tests.test_m1_backend -v`:
     ```text
     test_01_syntax_validity_engine_and_server (tests.test_m1_backend.TestM1BackendAndEngine.test_01_syntax_validity_engine_and_server) ... ok
     test_02_port_resolution_logic (tests.test_m1_backend.TestM1BackendAndEngine.test_02_port_resolution_logic) ... ok
     test_03_engine_detect_silence_points (tests.test_m1_backend.TestM1BackendAndEngine.test_03_engine_detect_silence_points) ... ok
     test_04_edge_tts_synthesis_direct (tests.test_m1_backend.TestM1BackendAndEngine.test_04_edge_tts_synthesis_direct) ... ok
     test_05_api_tts_voices_endpoint (tests.test_m1_backend.TestM1BackendAndEngine.test_05_api_tts_voices_endpoint) ... ok
     test_06_api_tts_post_endpoint (tests.test_m1_backend.TestM1BackendAndEngine.test_06_api_tts_post_endpoint) ... ok
     test_07_api_tts_defensive_voice_fallback (tests.test_m1_backend.TestM1BackendAndEngine.test_07_api_tts_defensive_voice_fallback) ... ok
     test_08_api_detect_silence_post_endpoint (tests.test_m1_backend.TestM1BackendAndEngine.test_08_api_detect_silence_post_endpoint) ... ok

     ----------------------------------------------------------------------
     Ran 8 tests in 9.446s

     OK
     ```

---

## 2. Logic Chain

1. *Observation*: `server.py` and `engine.py` contain no hardcoded strings or stubbed returns matching test fixtures.
   *Inference*: The implementation relies on genuine computation and external service calls, passing the hardcoded output check.
2. *Observation*: Physical `.mp3` files are created on disk with valid headers, codecs (MP3 mono 24kHz), and durations verified by `ffprobe`.
   *Inference*: The `POST /api/tts` endpoint authentically synthesizes neural voice audio via `edge-tts`.
3. *Observation*: Calling `engine.detect_silence_points` on both synthetic audio with programmed silence gaps and live generated TTS files produces correct, non-static silence and speech boundaries.
   *Inference*: `detect_silence_points` is a genuine implementation delegating to FFmpeg `silencedetect` and not a facade.
4. *Observation*: All 8 tests in `tests/test_m1_backend.py` execute live HTTP requests against a `ThreadingHTTPServer` test instance, verify HTTP 200/206 byte-range responses, and test boundary conditions.
   *Inference*: The test suite is authentic, verifiable, and free of self-certifying shortcuts.
5. *Observation*: `ORIGINAL_REQUEST.md` specifies `Integrity mode: development`. Under development mode, external tool usage (`edge-tts`, `ffmpeg`) is permitted.
   *Inference*: No integrity violations exist. The verdict is CLEAN.

---

## 3. Caveats

- Synthesis through `edge-tts` requires an active outbound network connection to Microsoft speech services; when offline, requests will return HTTP 500 JSON error objects as expected.
- Milestone M1 does not touch frontend files (`public/index.html` or `public/theme.css`), which are scheduled for Milestone M2.

---

## 4. Conclusion

Milestone M1 (Backend Neural TTS & Engine Services) has successfully passed all forensic integrity checks. The implementation is authentic, robust, non-facaded, and fully meets the requirements set forth in `ORIGINAL_REQUEST.md` and `PROJECT.md`.
**Final Verdict: CLEAN — APPROVED FOR MILESTONE M2.**

---

## 5. Verification Method

To independently reproduce the forensic verification results:

```powershell
cd C:\Users\Administrator\Documents\Projetos\montanha-media-lab
python -m unittest tests.test_m1_backend -v
```

Expected result:
- 8 tests executed and passed (`Ran 8 tests in ~9-15s`, `OK`).
- Audio files generated in `C:\Users\Administrator\Downloads\MontanhaMediaLab\tts_*.mp3`.

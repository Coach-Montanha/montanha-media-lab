# Handoff Report — Technical Survey: Testing & Specs

**Agent**: teamwork_explorer (Testing & Specs Explorer)  
**Task**: Survey Testing Infrastructure, Playwright on Edge, Edge-TTS Specs, and Silence Detection Logic  
**Date**: 2026-11-02  
**Handoff Type**: Hard (Task Complete)  

---

## 1. Observation

- **Observation 1.1 (Runtime & Test Infra)**:
  - Command: `python --version` returned `Python 3.11.9`.
  - Command: `pip show playwright edge-tts` revealed `playwright` version `1.64.0` and `edge-tts` version `7.3.1` already installed in `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\Lib\site-packages`.
  - Command: `python -m pytest --version` exited with code 1 (`No module named pytest`).
  - Python standard library `unittest` is present and functional without external runners.
  - Inspection of `C:\Users\Administrator\Documents\Projetos\montanha-media-lab`: no prior test directory or test scripts existed (`find_by_name *test*` returned 0 results).
  - Port 4190 is active on Windows, serving `public/index.html` via Python PID 976.

- **Observation 1.2 (Microsoft Edge via Playwright)**:
  - Command: `python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(channel='msedge', headless=True); print('BROWSER:', b.version); b.close(); p.stop()"` returned:
    `BROWSER: 156.0.4314.50`.
  - Playwright navigated to `http://localhost:4190` on Edge and extracted `Page Title: Montanha Media Lab & Video Studio` in headless mode without any errors.

- **Observation 1.3 (Edge-TTS Voices & Parameter Formatting)**:
  - Command: `edge-tts --help` confirmed parameter flags: `--voice VOICE`, `--rate RATE` (default `+0%`), `--pitch PITCH` (default `+0Hz`), `--volume VOLUME` (default `+0%`).
  - Analysis of `await edge_tts.list_voices()`: Out of 322 total voices in `edge-tts`, exactly 3 Brazilian Portuguese voices exist:
    - `pt-BR-FranciscaNeural` (Female, Natural)
    - `pt-BR-AntonioNeural` (Male, Natural)
    - `pt-BR-ThalitaMultilingualNeural` (Female, Multilingual)
  - Empirical test with `pt-BR-BrendaNeural`:
    `FAILED with Brenda: <class 'edge_tts.exceptions.NoAudioReceived'> No audio was received. Please verify that your parameters are correct.`
  - Empirical tests with `pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, and `pt-BR-ThalitaMultilingualNeural`: all returned `SUCCESS` and generated playable MP3 files with rates/pitches like `rate="+10%"`, `pitch="+2Hz"`.

- **Observation 1.4 (Silence Detection & Engine Discrepancy)**:
  - Command: `ffmpeg -version` returned `ffmpeg version 6.1.1-essentials_build-www.gyan.dev`.
  - Tested synthetic audio with 1s tone, 2s silence, 2s tone using filter `-af silencedetect=noise=-30dB:d=0.5`. FFmpeg stderr reported `silence_start: 0.999977`, `silence_end: 3.00005`, `duration: 2.00007`, translating into keep speech segments `[0.0, 1.0]` and `[3.0, 5.0]`.
  - In `server.py` line 292: `res = engine.detect_silence_points(video_path)` is called under `/api/silence-detect`.
  - In `engine.py` line 141: the function is defined as `def detect_silence(video_path: str, noise_db: float = -30.0, min_duration: float = 0.25) -> List[Tuple[float, float]]:`. There is NO function named `detect_silence_points` in `engine.py`. Calling `/api/silence-detect` currently fails with `AttributeError`.

- **Observation 1.5 (Editor UI & Keyboard Shortcuts)**:
  - In `public/index.html`: `clips` array, `selectedClipIndex`, `saveHistory()`, `undoAction()`, `redoAction()`, and `splitSelectedClip()` exist.
  - Keyboard shortcuts in `setupKeyboardShortcuts()` (lines 2489-2534) handle: Space, S, Q, W, Delete, Ctrl+X, Ctrl+C, Ctrl+V, Ctrl+Z, Ctrl+Y.
  - Currently missing: `Ctrl+D` (Duplicate), `F` (Freeze Frame), right-click context menu (`contextmenu` events count is 0), left dock rail (~56px), and right properties inspector dock.

---

## 2. Logic Chain

1. **Test Runner Selection (from Obs 1.1 & 1.2)**: Since Python 3.11 with `playwright` 1.64.0 is installed and launches Microsoft Edge 156 flawlessly, while `pytest` is absent and `npm` test packages are not configured, the most robust, zero-dependency test runner is Python's standard library `unittest` with `playwright.sync_api`. Tests can be executed via `python -m unittest tests/test_e2e_edge.py` on Windows PowerShell without extra setup.
2. **TTS Resiliency (from Obs 1.3)**: Because `edge-tts` relies on the free Edge TTS WebSocket service, only the 3 official pt-BR voices are accepted. To fulfill user requests mentioning other Azure voices (`Brenda`, `Donato`, etc.) without throwing `NoAudioReceived` 500 errors, `server.py` must maintain a fallback dictionary that redirects requested Azure voice names to the nearest supported Edge voice (`Francisca` for female, `Antonio` for male).
3. **Backend Engine Alignment (from Obs 1.4)**: The mismatch between `server.py` calling `engine.detect_silence_points()` and `engine.py` defining `detect_silence()` must be bridged by adding `detect_silence_points(media_path)` to `engine.py`, returning both silence intervals and computed speech segments.
4. **Timeline Functional Split & Ripple Cut (from Obs 1.4 & 1.5)**: The detected silence intervals allow the frontend to execute a ripple cut: replacing the original clip with contiguous speech segments, removing silent gaps, and calling `saveHistory()` to preserve undo/redo fidelity.
5. **Multi-Tier E2E Architecture**: A 4-tier testing hierarchy ensures that basic component rendering (Tier 1), boundary conditions (Tier 2), chained operations (Tier 3), and end-to-end authoring workflows (Tier 4) are independently verified on Edge before deployment.

---

## 3. Caveats

- **Network Dependency of Edge TTS**: The `edge-tts` service relies on Microsoft's online endpoint (`speech.platform.bing.com`). It requires internet access during TTS generation; offline local fallback is not provided by `edge-tts` itself.
- **Port 4190 in Use**: A Python process (PID 976) is already running and listening on port 4190. During testing and subsequent server modifications, the existing process should either be restarted or tested against directly.
- **Termux Android Execution**: While tests on Windows use Microsoft Edge, execution on Termux utilizes port 8080. Testing in Termux is outside the local Windows Playwright scope, but code compatibility is maintained.

---

## 4. Conclusion

The testing environment, browser channel, TTS synthesis parameters, and silence detection logic are fully mapped, empirically tested, and ready for implementation:
- **Test Engine**: Python `unittest` + `playwright.sync_api` launching `channel='msedge'`.
- **TTS Engine**: `edge-tts` with mandatory signed string formatting (`rate="+0%"`, `pitch="+0Hz"`) and defensive fallback mapping to the 3 native pt-BR voices (`pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaMultilingualNeural`).
- **Silence Cut**: FFmpeg `-af silencedetect=noise=-30dB:d=0.4` paired with an aligned `engine.detect_silence_points()` method and frontend ripple cut.
- **Detailed Report**: Delivered at `.agents/teamwork/explorer_survey_3/survey_testing_specs.md`.

---

## 5. Verification Method

To independently verify these findings, run the following commands in Windows PowerShell:

1. **Verify Microsoft Edge Launch via Playwright**:
   ```powershell
   python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(channel='msedge', headless=True); print('EDGE VERSION:', b.version); b.close(); p.stop()"
   ```
   *Expected*: Prints `EDGE VERSION: 156.0.4314.50` without errors.

2. **Verify Edge-TTS Synthesis & Brazilian Voice List**:
   ```powershell
   python C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_3\check_specs.py
   ```
   *Expected*: Shows 3 supported pt-BR voices, reports `NoAudioReceived` on `Brenda`, and succeeds on `Francisca`, `Antonio`, `Thalita`.

3. **Verify Silence Detection Parsing**:
   ```powershell
   python C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_3\silence_test.py
   ```
   *Expected*: Outputs detected silences and keep segments with high precision.

4. **Inspect Comprehensive Survey Report**:
   Inspect `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_3\survey_testing_specs.md`.

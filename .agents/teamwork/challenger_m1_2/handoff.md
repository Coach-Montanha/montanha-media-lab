# Handoff Report: Milestone M1 Adversarial Backend Challenge 2

## 1. Observation
- **Test Artifact Created**:
  - `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\tests\test_m1_adversarial.py` (10 automated adversarial tests).
- **Test Execution Command & Result**:
  - Command: `python -m unittest tests.test_m1_adversarial -v`
  - Output:
    ```
    test_01_port_argv_precedence_over_env_and_default ... ok
    test_02_port_env_precedence_over_platform_default ... ok
    test_03_port_platform_termux_vs_win32_simulation ... ok
    test_04_live_socket_concurrency ... ok
    test_05_media_route_resolution_downloads_dir ... ok
    test_06_media_route_resolution_upload_dir ... ok
    test_07_media_route_resolution_output_dir ... ok
    test_08_media_route_non_existent_returns_404 ... ok
    test_09_media_route_directory_traversal_security_probe ... FAIL
    test_10_edge_tts_audio_integrity_and_duration_parity ... ok
    ----------------------------------------------------------------------
    Ran 10 tests in 2.792s
    FAILED (failures=1)
    ```
- **Direct Vulnerability Observation**:
  - In `server.py` lines 227-238:
    ```python
    elif parsed.path.startswith("/media/"):
        rel_path = parsed.path.replace("/media/", "").lstrip("/")
        target_path = (DOWNLOADS_DIR / rel_path).resolve()
        if not target_path.exists() or not target_path.is_file():
            target_path = (UPLOAD_DIR / rel_path).resolve()
        if not target_path.exists() or not target_path.is_file():
            target_path = (OUTPUT_DIR / rel_path).resolve()
        if not target_path.exists() or not target_path.is_file():
            self.send_error(404, "Media not found")
            return
        self._serve_file_with_range(target_path)
        return
    ```
  - Running raw HTTP requests:
    - Forward-slash traversal: `GET /media/../../Documents/Projetos/montanha-media-lab/server.py HTTP/1.1` returned `HTTP/1.0 200 OK` and served the Python backend source code.
    - Windows backslash traversal: `GET /media/..\..\Documents\Projetos\montanha-media-lab\server.py HTTP/1.1` returned `HTTP/1.0 200 OK` and served the source code.
    - URL-encoded traversal: `GET /media/%2e%2e%2f%2e%2e%2fDocuments%2fProjetos%2fmontanha-media-lab%2fserver.py HTTP/1.1` returned `HTTP/1.0 200 OK` and served the source code.
- **Port Resolution Verification**:
  - `server.py:794-817` correctly prioritized `sys.argv[1]` > `os.environ["PORT"]` > platform default (8080 on Termux detection via `/data/data/com.termux` or `/sdcard`, 4190 on Windows `sys.platform == "win32"`, 8080 fallback).
  - Robust exception handling confirmed: non-integer argv/env gracefully fall back without crashes.
- **Neural TTS & Engine Media Inspection**:
  - Synthesized `.mp3` via `edge-tts 7.3.1` inspected via `ffprobe` format and audio stream:
    - Codec: `mp3`
    - Channels: `1` (mono)
    - Sample Rate: `24000 Hz`
    - Format duration: `4.82s`
  - `engine.get_video_info(temp_mp3)` returned `{"status": "success", "codec": "mp3", "duration": 4.82, "has_audio": True}`.
  - Duration parity delta between ffprobe format duration and `engine.get_video_info`: `0.00s`.

## 2. Logic Chain
1. *Observation*: `server.py` line 107 executes `raw_path = urllib.parse.unquote(self.path)`, and line 228 strips only `/media/` and leading `/` (`rel_path = parsed.path.replace("/media/", "").lstrip("/")`).
   *Inference*: Any relative traversal tokens (`..`, `../`, `..\`) present in the requested URL survive unquoting and stripping.
2. *Observation*: Lines 229, 231, and 233 execute `(DOWNLOADS_DIR / rel_path).resolve()`.
   *Inference*: `Path.resolve()` navigates up directory levels across relative dot sequences (`..`), resolving to arbitrary locations outside `DOWNLOADS_DIR`, `UPLOAD_DIR`, and `OUTPUT_DIR`.
3. *Observation*: Lines 230, 232, and 234 only check `if not target_path.exists() or not target_path.is_file():` with no boundary check against allowed base directories.
   *Inference*: Any file on the filesystem accessible to the running process is served to external clients via `/media/`. Because ORIGINAL_REQUEST §R3 specifies production deployment on Windows via Cloudflare tunnel, this allows unauthenticated external attackers to read project source files, configuration, tokens, or system files (CWE-22 / Arbitrary File Disclosure).
4. *Observation*: 9 out of 10 tests passed (port precedence, live concurrency, legitimate /media/ resolution across all 3 folders, 404 handling, edge-tts audio integrity, ffprobe stream validation, get_video_info parity). Only directory traversal failed.
   *Inference*: All functional TTS and port mechanics are working, but the critical path traversal vulnerability must be addressed before production release.

## 3. Caveats
- Direct multipart file uploads were not audited as they belong to legacy media import rather than the M1 Neural TTS scope.
- `server.py` has a separate `/stream?file=...` parameter designed to accept system file paths for video streaming; however, `/media/` is exposed as the relative public asset endpoint (`/media/{filename}`) and must be bounded to media directories.

## 4. Conclusion
**VERDICT: REQUEST_CHANGES**

Milestone M1 cannot be approved in its current state due to a **Critical Security Vulnerability (Path Traversal / Arbitrary File Disclosure)** in the `/media/` route (`server.py:227-238`).

### Required Change for Worker M1:
Enforce directory containment on `/media/` resolution. For each candidate directory (`DOWNLOADS_DIR`, `UPLOAD_DIR`, `OUTPUT_DIR`), verify that the resolved path is strictly a descendant of the base directory before serving:
```python
        elif parsed.path.startswith("/media/"):
            rel_path = parsed.path.replace("/media/", "").lstrip("/")
            candidate = None
            for base_dir in [DOWNLOADS_DIR, UPLOAD_DIR, OUTPUT_DIR]:
                try:
                    resolved_base = base_dir.resolve()
                    potential = (base_dir / rel_path).resolve()
                    potential.relative_to(resolved_base)
                    if potential.is_file():
                        candidate = potential
                        break
                except (ValueError, RuntimeError):
                    continue
            if not candidate:
                self.send_error(404, "Media not found")
                return
            self._serve_file_with_range(candidate)
            return
```
Once this patch is applied, all 10 tests in `tests/test_m1_adversarial.py` will pass 100%.

## 5. Verification Method
To independently verify the test suite and vulnerability:
```powershell
Set-Location "C:\Users\Administrator\Documents\Projetos\montanha-media-lab"
python -m unittest tests.test_m1_adversarial -v
```
Expected output:
- `test_09_media_route_directory_traversal_security_probe` fails with `AssertionError: SECURITY VULNERABILITY DETECTED in /media/ route resolution` when vulnerable.
- When patched with the containment validation above, all 10 tests pass with `OK`.

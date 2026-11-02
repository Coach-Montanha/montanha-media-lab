# Task Assignment for Worker M1 (Iteration 2 Fixes)

## Context
Milestone M1 Gate failed due to 3 defects discovered by Adversarial Challenger 1.
Challenger handoff: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\challenger_m1_1\handoff.md`
Challenger test suite: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\tests\test_m1_challenger.py`

## Owned Files
- `server.py`
- `engine.py`

## Defects to Fix
1. Concurrency Race Condition in `POST /api/tts`:
   In `server.py`, ensure generated audio filename includes a random nonce (e.g. `import uuid; f"tts_{voice_tag}_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"`), guaranteeing 100% unique filenames even under concurrent rapid requests.
2. 0-Byte and Unreadable Media Handling:
   In `engine.py:detect_silence_points()` and `server.py:/api/detect-silence`, check if file size == 0 or duration <= 0. Return `{"status": "error", "message": "Arquivo de mídia inválido, vazio ou ilegível"}` with HTTP 400. Do NOT return phantom speech segments like `[0.0, 0.0]`.
3. Path Traversal on `GET /media/`:
   In `server.py`, sanitize `rel_path` and verify containment:
   ```python
   rel_path = parsed.path.replace("/media/", "").lstrip("/")
   if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
       self.send_error(403, "Access denied")
       return
   ```
   Or verify `target_path.is_relative_to(DOWNLOADS_DIR)` / `UPLOAD_DIR` / `OUTPUT_DIR`.
4. Verification:
   Run:
   `python -m unittest tests/test_m1_backend.py -v`
   `python tests/test_m1_challenger.py -v`
   Both suites must pass with 100% OK!

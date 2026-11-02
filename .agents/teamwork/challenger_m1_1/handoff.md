# Handoff Report: Milestone M1 Adversarial Challenge

**Verdict**: **REQUEST_CHANGES**  
**Role**: Empirical Challenger 1 (Backend Neural TTS & Engine Services)  
**Target Milestone**: M1 (Worker: `worker_m1`)  

---

## 1. Observation

### Verification Harness Executed
Created and executed an adversarial test suite in `tests/test_m1_challenger.py` covering 8 distinct challenge dimensions:
```powershell
cd C:\Users\Administrator\Documents\Projetos\montanha-media-lab
python tests/test_m1_challenger.py -v
```
**Test Result**: `Ran 8 tests in 20.026s. FAILED (failures=3)`

---

### Defect 1: Race Condition & Audio File Collision under Concurrent `POST /api/tts`
- **Location**: `server.py:380-386`:
  ```python
  voice_tag = selected_voice.replace("pt-BR-", "").replace("pt-PT-", "").replace("Multilingual", "").replace("Neural", "").lower()
  timestamp = int(time.time())
  out_name = f"tts_{voice_tag}_{timestamp}.mp3"
  out_file = DOWNLOADS_DIR / out_name
  if out_file.exists():
      out_name = f"tts_{voice_tag}_{timestamp}_{int(time.time() * 1000) % 1000}.mp3"
      out_file = DOWNLOADS_DIR / out_name
  ```
- **Observed Behavior**:
  When 6 concurrent requests were dispatched simultaneously via `threading.Barrier(6)` in `test_challenge_01_concurrent_rapid_tts_synthesis`:
  ```
  [CHALLENGE 1 RESULT] Dispatched 6 concurrent requests -> Generated 5 unique filenames
  AssertionError: 6 != 5 : CRITICAL BUG: File collision detected under concurrency!
  6 requests generated only 5 unique files.
  Filenames: [
    '...\\tts_francisca_1793650447_304.mp3',
    '...\\tts_francisca_1793650447.mp3',
    '...\\tts_francisca_1793650447.mp3',
    '...\\tts_francisca_1793650447_312.mp3',
    '...\\tts_francisca_1793650447_305.mp3',
    '...\\tts_francisca_1793650447_303.mp3'
  ]
  ```
  Multiple threads calculated the same second timestamp `1793650447`. Before the first thread finished writing to disk, subsequent threads checked `if out_file.exists()`, evaluated to `False`, and targeted the exact same output path, silently overwriting each other's audio files.

---

### Defect 2: 0-Byte and Unreadable Media Returns False "Success" with Phantom Speech Segment
- **Location**: `engine.py:191-224` (`detect_silence_points`) & `server.py:448-460`:
  ```python
  info = get_video_info(media_path)
  total_dur = info.get("duration", 0.0)
  silence_intervals = detect_silence(media_path, noise_db=noise_db, min_duration=min_duration)
  ...
  speech_segments = compute_speech_segments(total_dur, silence_intervals)
  ```
- **Observed Behavior**:
  Submitting a 0-byte or corrupted file to `POST /api/detect-silence` in `test_challenge_05_silence_detection_nonexistent_and_corrupt`:
  ```
  [CHALLENGE 5 RESULT] 0-byte file response: HTTP 200 ->
  {
    'status': 'success',
    'duration': 0.0,
    'silences': [],
    'speech_segments': [{'start': 0.0, 'end': 0.0, 'duration': 0.0}],
    'silence_count': 0,
    'speech_count': 1,
    'saved_seconds': 0
  }
  ```
  The endpoint returns HTTP 200 `status: "success"` with a dummy speech segment `[0.0, 0.0]`. In the frontend timeline, this triggers phantom cut operations or errors on invalid zero-duration segments instead of alerting the user that the media is unreadable.

---

### Defect 3: Arbitrary File Read / Path Traversal Vulnerability in `GET /media/`
- **Location**: `server.py:227-238`:
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
- **Observed Behavior**:
  Executing `GET /media/../../Documents/Projetos/montanha-media-lab/server.py` in `test_challenge_07_media_path_traversal_vulnerability`:
  ```
  [CHALLENGE 7 RESULT] Traversal probe returned HTTP 200, length: 39447 bytes
  AssertionError: 200 == 200 : SECURITY VULNERABILITY: /media/ is vulnerable to Path Traversal! Leaked server.py source code.
  ```
  Because `Path.resolve()` navigates through `..` without verifying that `target_path` remains anchored within the designated media directories, any file on the host machine readable by the process is exposed to clients.

---

### Robust Capabilities Verified (Passing Tests)
1. **Extreme Rate and Pitch Variations**:
   - `+100%`, `-50%`, `+50Hz`, `-30Hz`, float `2.0`, float `0.5`, int `50`, int `-30` all synthesized successfully.
   - Speed comparison verified: `-50%` generated audio duration > 1.5x longer than `+100%`.
2. **Text Robustness**:
   - Accented Brazilian Portuguese characters (`á, é, í, ó, ú, â, ê, ô, ã, õ, ç, à, ü`), emojis (`🚀, 🎙️, 🇧🇷`), quotes, linebreaks (`\n\r\t`), and XML characters (`<Clipchamp>`, `&`) synthesized without SSML syntax errors.
3. **Defensive Voice Fallback**:
   - Unknown voice names (`alien_voice_9000_does_not_exist`) safely fell back to `pt-BR-FranciscaNeural`.
   - Empty text and whitespace-only text correctly returned HTTP 400 Bad Request without crashing.
4. **Silence Detection on Valid Media**:
   - Pure continuous tone correctly reported `silence_count: 0`, `saved_seconds: 0.0`.
   - Pure silence correctly reported `silences` covering full duration and `saved_seconds > 2.5s`.
   - Alternating multi-second audio accurately identified distinct silence intervals and speech boundaries.
5. **Post-Stress Server Stability**:
   - Server process survived the entire battery of adversarial requests without deadlocks or zombie threads.

---

## 2. Logic Chain

1. *Observation*: `server.py:380-386` uses `int(time.time())` with a fallback `int(time.time() * 1000) % 1000` that is only evaluated *after* `out_file.exists()` is true on disk.
   *Inference*: When `ThreadingHTTPServer` executes multiple requests concurrently in parallel threads, multiple threads check `out_file.exists()` before any thread completes writing the `.mp3` file. They all obtain the identical path and overwrite each other. Adding a random UUID nonce (e.g. `uuid.uuid4().hex[:6]`) guarantees 100% uniqueness regardless of concurrency.
2. *Observation*: `engine.py:191-224` assumes any file where `get_video_info` returns duration 0 and `detect_silence` returns `[]` is a valid audio file with a speech segment of `[(0.0, 0.0)]`.
   *Inference*: A 0-byte or corrupt file has no audio stream. Returning `status: "success"` with duration 0.0 and `speech_segments: [{'start': 0.0, 'end': 0.0, 'duration': 0.0}]` misleads callers into treating unreadable media as valid speech, risking timeline corruption. Checking `if os.path.getsize(media_path) == 0 or total_dur <= 0.0:` and returning `status: "error"` ensures graceful error handling.
3. *Observation*: `server.py:228-237` resolves `(DIRECTORY / rel_path).resolve()` where `rel_path` contains `..`, and serves the resulting path without checking containment.
   *Inference*: An HTTP client requesting `/media/../../path` can read arbitrary files on the Windows filesystem. Sanitizing `rel_path` via `Path(rel_path).name` or asserting `target_path.is_relative_to(d)` stops directory traversal.

---

## 3. Caveats
- The concurrency test was executed with 6 concurrent workers. At higher concurrency (e.g. 50+ threads), rate limits from upstream Microsoft `edge-tts` websockets could occur.
- No modifications were made to implementation files in accordance with the review-only constraint.

---

## 4. Conclusion
Milestone M1 cannot be approved in its current state.
**Verdict**: **REQUEST_CHANGES**.
The implementation exhibits high quality in voice synthesis, parameter normalization, and silence detection algorithms, but requires three surgical fixes from Worker M1 before proceeding to production:
1. **Fix File Collision**: Use `uuid.uuid4().hex[:6]` in `server.py:381` for TTS filename generation.
2. **Fix 0-Byte/Empty File Handling**: Return HTTP 400 with `status: "error"` in `/api/detect-silence` and `engine.detect_silence_points` when media file size is 0 or unreadable.
3. **Fix Path Traversal**: Sanitize or validate `target_path` in `server.py:227-238` to prevent arbitrary file reading.

---

## 5. Verification Method
Run the challenger test suite to reproduce the findings:
```powershell
cd C:\Users\Administrator\Documents\Projetos\montanha-media-lab
python tests/test_m1_challenger.py -v
```
**Expected Invalidation Condition for Approval**:
Once Worker M1 applies the three fixes, running `python tests/test_m1_challenger.py -v` must yield:
`Ran 8 tests in ~20s. OK` with 0 failures and 0 errors.

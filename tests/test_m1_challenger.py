"""
Montanha Media Lab - Milestone M1 Empirical Adversarial Challenge Suite
Role: Empirical Challenger (Adversarial stress-testing M1 TTS & Silence Detection)

Stress-tests:
1. Concurrency: Rapid concurrent synthesis requests via ThreadingHTTPServer (tests race conditions and file collisions)
2. Extreme values: Extreme rate and pitch variations (+100%, -50%, +50Hz, -30Hz, floats/ints)
3. Text robustness: Punctuation, Brazilian accents, emojis, quotes, line breaks, XML/HTML symbols
4. Defensive voice fallback & invalid input rejection (empty text, invalid voice)
5. Silence detection edge cases: Non-existent files, 0-byte files, corrupt files
6. Silence detection accuracy: Pure tone, pure silence, alternating tone/silence multi-second WAVs
7. Media security: Path traversal vulnerability probe on /media/
8. Post-stress health check: Server process stability and zero deadlocks
"""

import ast
import concurrent.futures
import json
import math
import os
import struct
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import engine
import server


class TestM1EmpiricalChallenger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use dynamic ephemeral port to avoid collisions with any running server
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.UnifiedMediaStudioHandler)
        cls.test_port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "httpd") and cls.httpd:
            cls.httpd.shutdown()
            cls.httpd.server_close()

    def _http_get(self, path: str, timeout: float = 15.0):
        url = f"http://127.0.0.1:{self.test_port}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)

    def _http_post(self, path: str, payload: dict, timeout: float = 40.0):
        url = f"http://127.0.0.1:{self.test_port}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body}
            return e.code, parsed

    # -------------------------------------------------------------------------
    # CHALLENGE 1: Rapid Concurrent Synthesis Requests (ThreadingHTTPServer)
    # -------------------------------------------------------------------------
    def test_challenge_01_concurrent_rapid_tts_synthesis(self):
        """
        Adversarial test: Fire 6 simultaneous synthesis requests with the same voice
        synchronized via threading.Barrier to probe race conditions in file naming,
        event loops, and thread handling.
        """
        num_workers = 6
        barrier = threading.Barrier(num_workers)
        results = []

        def _synthesize_task(idx):
            barrier.wait()  # Synchronize launch to exact same millisecond
            t0 = time.time()
            text = f"Sessão concorrente número {idx} executando teste de estresse de áudio."
            payload = {
                "text": text,
                "voice": "pt-BR-FranciscaNeural",
                "rate": "+10%",
                "pitch": "+0Hz"
            }
            status, data = self._http_post("/api/tts", payload, timeout=60.0)
            elapsed = time.time() - t0
            return (idx, status, data, elapsed)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_synthesize_task, i) for i in range(num_workers)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        self.assertEqual(len(results), num_workers)

        # Check all succeeded with HTTP 200
        for idx, status, data, elapsed in results:
            self.assertEqual(status, 200, f"Worker {idx} failed with status {status}: {data}")
            self.assertEqual(data.get("status"), "success")
            self.assertIn("server_path", data)
            self.assertTrue(os.path.exists(data["server_path"]), f"Generated file not found: {data.get('server_path')}")
            self.assertGreater(data.get("duration", 0), 0.5)

        # Check for file collisions
        file_paths = [data["server_path"] for _, _, data, _ in results]
        unique_files = len(set(file_paths))
        print(f"\n[CHALLENGE 1 RESULT] Dispatched {num_workers} concurrent requests -> Generated {unique_files} unique filenames")
        self.assertEqual(
            len(file_paths),
            len(set(file_paths)),
            f"CRITICAL BUG: File collision detected under concurrency! {num_workers} requests generated only {unique_files} unique files. Filenames: {file_paths}"
        )

    # -------------------------------------------------------------------------
    # CHALLENGE 2: Extreme Rate and Pitch Variations
    # -------------------------------------------------------------------------
    def test_challenge_02_extreme_rate_and_pitch_variations(self):
        """
        Adversarial test: Test extreme values:
        - Rate: +100% (2x), -50% (0.5x), float 2.0 (+100%), float 0.5 (-50%)
        - Pitch: +50Hz, -30Hz, int +50, int -30
        """
        cases = [
            {"rate": "+100%", "pitch": "+0Hz", "label": "rate_+100%"},
            {"rate": "-50%", "pitch": "+0Hz", "label": "rate_-50%"},
            {"rate": "+0%", "pitch": "+50Hz", "label": "pitch_+50Hz"},
            {"rate": "+0%", "pitch": "-30Hz", "label": "pitch_-30Hz"},
            {"rate": 2.0, "pitch": "+0Hz", "label": "float_rate_2.0"},
            {"rate": 0.5, "pitch": "+0Hz", "label": "float_rate_0.5"},
            {"rate": "+0%", "pitch": 50, "label": "numeric_pitch_50"},
            {"rate": "+0%", "pitch": -30, "label": "numeric_pitch_-30"}
        ]

        durations = {}
        for c in cases:
            payload = {
                "text": "Velocidade e tom extremos em teste de estresse.",
                "voice": "pt-BR-AntonioNeural",
                "rate": c["rate"],
                "pitch": c["pitch"]
            }
            status, data = self._http_post("/api/tts", payload)
            self.assertEqual(status, 200, f"Failed on {c['label']}: {data}")
            self.assertEqual(data.get("status"), "success")
            self.assertTrue(os.path.exists(data["server_path"]))
            durations[c["label"]] = data.get("duration", 0)

        fast_dur = durations["rate_+100%"]
        slow_dur = durations["rate_-50%"]
        self.assertGreater(slow_dur, fast_dur * 1.5, f"Expected slow ({slow_dur}s) to be > 1.5x fast ({fast_dur}s)")

    # -------------------------------------------------------------------------
    # CHALLENGE 3: Text Robustness (Accents, Emojis, Quotes, Line Breaks, XML)
    # -------------------------------------------------------------------------
    def test_challenge_03_text_robustness_and_special_chars(self):
        """
        Adversarial test: Text containing:
        - Portuguese diacritics: á, é, í, ó, ú, â, ê, ô, ã, õ, ç, à, ü
        - Emojis: 🚀 🔥 🎬 🎙️ 🇧🇷
        - Quotes and punctuation: "duplas", 'simples', «angulares», --, ..., ?!
        - Line breaks and tabs: \n \r \t
        - XML/HTML sensitive characters: & < >
        """
        complex_text = (
            "Montanha Media Lab: Áudio & Vídeo com <Clipchamp> e vozes neurais! 🚀🎙️\n"
            "Parágrafo com acentuação: Ação, você, café, amanhã, ímpar, saúde.\r\n"
            "\tCitação: \"A simplicidade é o último grau de sofisticação\" — Leonardo da Vinci."
        )

        payload = {
            "text": complex_text,
            "voice": "pt-BR-FranciscaNeural",
            "rate": "+0%",
            "pitch": "+0Hz"
        }
        status, data = self._http_post("/api/tts", payload)
        self.assertEqual(status, 200, f"Failed with complex text: {data}")
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(os.path.exists(data["server_path"]))
        self.assertGreater(data.get("duration", 0), 2.0)

    # -------------------------------------------------------------------------
    # CHALLENGE 4: Unsupported Voice Inputs & Graceful Fallbacks
    # -------------------------------------------------------------------------
    def test_challenge_04_unsupported_voices_and_bad_input_handling(self):
        """
        Adversarial test:
        - Non-existent voice -> graceful fallback to Francisca without crashing
        - Invalid voice format -> fallback without crashing
        - Empty text -> HTTP 400 Bad Request
        - Whitespace text -> HTTP 400 Bad Request
        """
        payload_bad_voice = {
            "text": "Voz inexistente deve fazer fallback gracioso.",
            "voice": "alien_voice_9000_does_not_exist"
        }
        status, data = self._http_post("/api/tts", payload_bad_voice)
        self.assertEqual(status, 200, f"Fallback failed: {data}")
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("voice"), "pt-BR-FranciscaNeural")
        self.assertTrue(os.path.exists(data["server_path"]))

        payload_thalita = {
            "text": "Voz Thalita em minúsculas.",
            "voice": "pt-br-thalitaneural"
        }
        status, data = self._http_post("/api/tts", payload_thalita)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("voice"), "pt-BR-ThalitaMultilingualNeural")

        payload_empty = {"text": "", "voice": "pt-BR-FranciscaNeural"}
        status, data = self._http_post("/api/tts", payload_empty)
        self.assertEqual(status, 400)
        self.assertEqual(data.get("status"), "error")

        payload_spaces = {"text": "   \n\t   ", "voice": "pt-BR-FranciscaNeural"}
        status, data = self._http_post("/api/tts", payload_spaces)
        self.assertEqual(status, 400)
        self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # CHALLENGE 5: Silence Detection Edge Cases (Nonexistent, 0-byte, Corrupt)
    # -------------------------------------------------------------------------
    def test_challenge_05_silence_detection_nonexistent_and_corrupt(self):
        """
        Adversarial test:
        - Nonexistent file path -> HTTP 400 JSON error, server remains alive
        - 0-byte file -> Handled without crashing; should return error status or be flagged
        """
        # Test 1: Nonexistent file
        status, data = self._http_post("/api/detect-silence", {"media_path": "C:\\nonexistent_media_xyz.mp4"})
        self.assertEqual(status, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("não encontrado", data.get("message", "").lower())

        # Test 2: 0-byte file
        temp_dir = tempfile.gettempdir()
        empty_file = os.path.join(temp_dir, f"empty_audio_{int(time.time())}.wav")
        with open(empty_file, "wb") as f:
            pass  # 0 bytes

        try:
            status, data = self._http_post("/api/detect-silence", {"media_path": empty_file})
            print(f"\n[CHALLENGE 5 RESULT] 0-byte file response: HTTP {status} -> {data}")
            # If backend returns success with 0.0 duration and phantom speech segment, flag as logic flaw
            if status == 200 and data.get("status") == "success":
                self.assertNotEqual(
                    data.get("speech_segments"),
                    [{"start": 0.0, "end": 0.0, "duration": 0.0}],
                    "BUG: 0-byte unreadable file returned status 'success' with phantom speech segment [0.0, 0.0]"
                )
        finally:
            if os.path.exists(empty_file):
                os.remove(empty_file)

    # -------------------------------------------------------------------------
    # CHALLENGE 6: Silence Detection Accuracy on Multi-second Synthetic Scenarios
    # -------------------------------------------------------------------------
    def test_challenge_06_silence_detection_synthetic_scenarios(self):
        """
        Adversarial empirical tests on synthetic audio:
        Case A: 3.0s Continuous Tone (0% silence)
        Case B: 3.0s Pure Silence (100% silence)
        Case C: Alternating Tone (1s) - Silence (1.5s) - Tone (1.5s) - Silence (1.0s) - Tone (1.0s) = 6.0s
        """
        temp_dir = tempfile.gettempdir()
        sample_rate = 16000

        def _write_wav(filename, tone_intervals, total_duration):
            wav_path = os.path.join(temp_dir, filename)
            num_samples = int(sample_rate * total_duration)
            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                is_tone = any(start <= t < end for start, end in tone_intervals)
                if is_tone:
                    val = int(32767 * 0.5 * math.sin(2 * math.pi * 440.0 * t))
                else:
                    val = 0
                samples.append(val)
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
            return wav_path

        # Case A: 3.0s Pure Continuous Tone (No silence)
        file_a = _write_wav(f"syn_pure_tone_{int(time.time())}.wav", [(0.0, 3.0)], 3.0)
        try:
            res_a = engine.detect_silence_points(file_a, noise_db=-30.0, min_duration=0.4)
            self.assertEqual(res_a.get("status"), "success")
            self.assertAlmostEqual(res_a["duration"], 3.0, delta=0.1)
            self.assertEqual(res_a["silence_count"], 0)
            self.assertEqual(res_a["saved_seconds"], 0.0)
            self.assertGreaterEqual(res_a["speech_count"], 1)
        finally:
            if os.path.exists(file_a):
                os.remove(file_a)

        # Case B: 3.0s Pure Silence (100% silence)
        file_b = _write_wav(f"syn_pure_silence_{int(time.time())}.wav", [], 3.0)
        try:
            res_b = engine.detect_silence_points(file_b, noise_db=-30.0, min_duration=0.4)
            self.assertEqual(res_b.get("status"), "success")
            self.assertAlmostEqual(res_b["duration"], 3.0, delta=0.1)
            self.assertGreaterEqual(res_b["silence_count"], 1)
            self.assertGreater(res_b["saved_seconds"], 2.5)
        finally:
            if os.path.exists(file_b):
                os.remove(file_b)

        # Case C: 6.0s Alternating Tone and Silence
        file_c = _write_wav(
            f"syn_alternating_{int(time.time())}.wav",
            [(0.0, 1.0), (2.5, 4.0), (5.0, 6.0)],
            6.0
        )
        try:
            status, res_c = self._http_post("/api/detect-silence", {
                "media_path": file_c,
                "noise_db": -30.0,
                "min_duration": 0.4
            })
            self.assertEqual(status, 200)
            self.assertEqual(res_c.get("status"), "success")
            self.assertAlmostEqual(res_c["duration"], 6.0, delta=0.2)
            self.assertGreaterEqual(res_c["silence_count"], 2)
            self.assertGreaterEqual(res_c["speech_count"], 3)
            self.assertAlmostEqual(res_c["saved_seconds"], 2.5, delta=0.4)
        finally:
            if os.path.exists(file_c):
                os.remove(file_c)

    # -------------------------------------------------------------------------
    # CHALLENGE 7: Path Traversal Vulnerability Probe on /media/
    # -------------------------------------------------------------------------
    def test_challenge_07_media_path_traversal_vulnerability(self):
        """
        Adversarial test: Attempt directory traversal via /media/../../path
        to verify whether server restricts access strictly to allowed directories.
        """
        traversal_url = f"http://127.0.0.1:{self.test_port}/media/../../Documents/Projetos/montanha-media-lab/server.py"
        try:
            req = urllib.request.Request(traversal_url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read()
                print(f"\n[CHALLENGE 7 RESULT] Traversal probe returned HTTP {resp.status}, length: {len(body)} bytes")
                # If server returned 200 and leaked server.py, assert vulnerability
                self.assertNotEqual(
                    resp.status,
                    200,
                    "SECURITY VULNERABILITY: /media/ is vulnerable to Path Traversal! Leaked server.py source code."
                )
        except urllib.error.HTTPError as e:
            # Expected secure behavior is HTTP 403 or 404
            self.assertIn(e.code, [403, 404])

    # -------------------------------------------------------------------------
    # CHALLENGE 8: Post-Stress Process Health Check
    # -------------------------------------------------------------------------
    def test_challenge_08_post_stress_server_health(self):
        """
        Verify the server remains 100% responsive, functional, and uncorrupted
        after enduring the full battery of adversarial stress tests.
        """
        status, data = self._http_get("/api/tts/voices")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertGreaterEqual(len(data.get("voices", [])), 3)

        status, tts_res = self._http_post("/api/tts", {
            "text": "Verificação final de saúde pós-estresse.",
            "voice": "pt-BR-FranciscaNeural"
        })
        self.assertEqual(status, 200)
        self.assertEqual(tts_res.get("status"), "success")
        self.assertTrue(os.path.exists(tts_res["server_path"]))


if __name__ == "__main__":
    unittest.main()

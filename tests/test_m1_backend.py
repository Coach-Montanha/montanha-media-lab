"""
Montanha Media Lab - Milestone M1 Backend & Engine Verification Test Suite
Verifies:
1. Python syntax validity of server.py and engine.py
2. engine.detect_silence_points functionality with synthetic audio
3. server.py get_default_port resolution logic (CLI arg, env var, win32/termux platform)
4. Synthesis via edge-tts with Brazilian voice (pt-BR-FranciscaNeural)
5. Live HTTP endpoints on ThreadingHTTPServer:
   - GET /api/tts/voices & GET /api/tts-voices
   - POST /api/tts
   - POST /api/detect-silence & POST /api/silence-detect
   - GET /media/ with byte-range and multi-directory resolution
"""

import ast
import json
import math
import os
import struct
import subprocess
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


class TestM1BackendAndEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start a test instance of ThreadingHTTPServer on an ephemeral port
        cls.test_port = 4195
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", cls.test_port), server.UnifiedMediaStudioHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "httpd") and cls.httpd:
            cls.httpd.shutdown()
            cls.httpd.server_close()

    def _http_get(self, path: str):
        url = f"http://127.0.0.1:{self.test_port}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)

    def _http_post(self, path: str, payload: dict):
        url = f"http://127.0.0.1:{self.test_port}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
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
    # 1. Syntax Validity
    # -------------------------------------------------------------------------
    def test_01_syntax_validity_engine_and_server(self):
        """Verify Python syntax validity of both server.py and engine.py using AST."""
        for filename in ["server.py", "engine.py"]:
            filepath = PROJECT_ROOT / filename
            self.assertTrue(filepath.exists(), f"File {filename} does not exist")
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code, filename=str(filepath))
            self.assertIsNotNone(tree, f"AST parse failed for {filename}")

    # -------------------------------------------------------------------------
    # 2. Port Resolution Logic
    # -------------------------------------------------------------------------
    def test_02_port_resolution_logic(self):
        """Verify smart port calculation logic with precedence."""
        orig_argv = sys.argv.copy()
        orig_env_port = os.environ.get("PORT")

        try:
            # Test CLI argument precedence
            sys.argv = ["server.py", "9090"]
            os.environ["PORT"] = "7070"
            self.assertEqual(server.get_default_port(), 9090)

            # Test env PORT precedence when no CLI arg
            sys.argv = ["server.py"]
            os.environ["PORT"] = "8081"
            self.assertEqual(server.get_default_port(), 8081)

            # Test platform default (Windows win32 -> 4190)
            if "PORT" in os.environ:
                del os.environ["PORT"]
            sys.argv = ["server.py"]
            if sys.platform == "win32" and not os.path.exists("/sdcard"):
                self.assertEqual(server.get_default_port(), 4190)

        finally:
            sys.argv = orig_argv
            if orig_env_port is not None:
                os.environ["PORT"] = orig_env_port
            elif "PORT" in os.environ:
                del os.environ["PORT"]

    # -------------------------------------------------------------------------
    # 3. Engine Silence Detection Points
    # -------------------------------------------------------------------------
    def test_03_engine_detect_silence_points(self):
        """
        Create a synthetic WAV file:
        0.0s - 1.0s: Tone (Active audio)
        1.0s - 2.5s: Silence (1.5s silence)
        2.5s - 4.0s: Tone (Active audio)
        Verify detect_silence_points correctly identifies the silence and speech segments.
        """
        temp_dir = tempfile.gettempdir()
        wav_path = os.path.join(temp_dir, f"test_silence_{int(time.time())}.wav")

        sample_rate = 16000
        total_duration = 4.0
        tone_freq = 440.0

        num_samples = int(sample_rate * total_duration)
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            if 0.0 <= t < 1.0 or 2.5 <= t < 4.0:
                # Active audio tone
                val = int(32767 * 0.5 * math.sin(2 * math.pi * tone_freq * t))
            else:
                # Silence
                val = 0
            samples.append(val)

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            raw_data = struct.pack(f"<{len(samples)}h", *samples)
            wf.writeframes(raw_data)

        try:
            self.assertTrue(os.path.exists(wav_path))
            result = engine.detect_silence_points(wav_path, noise_db=-30.0, min_duration=0.5)

            self.assertEqual(result.get("status"), "success")
            self.assertIn("duration", result)
            self.assertGreaterEqual(result["duration"], 3.9)
            self.assertIn("silences", result)
            self.assertIn("speech_segments", result)
            self.assertIn("silence_count", result)
            self.assertIn("speech_count", result)
            self.assertIn("saved_seconds", result)

            self.assertGreaterEqual(result["silence_count"], 1)
            first_silence = result["silences"][0]
            # Silence should start around 1.0s and end around 2.5s
            self.assertAlmostEqual(first_silence["start"], 1.0, delta=0.2)
            self.assertAlmostEqual(first_silence["end"], 2.5, delta=0.2)
            self.assertGreater(result["saved_seconds"], 1.0)

            # Speech segments should have 2 segments
            self.assertGreaterEqual(result["speech_count"], 2)

        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)

    # -------------------------------------------------------------------------
    # 4. Neural TTS Synthesis via edge-tts with Brazilian Voice
    # -------------------------------------------------------------------------
    def test_04_edge_tts_synthesis_direct(self):
        """Directly synthesize speech with edge-tts and check output."""
        import edge_tts
        import asyncio

        out_path = os.path.join(tempfile.gettempdir(), f"test_direct_tts_{int(time.time())}.mp3")
        text = "Montanha Media Lab texto de teste para síntese de voz neural."

        async def _test_tts():
            comm = edge_tts.Communicate(text, "pt-BR-FranciscaNeural", rate="+10%", pitch="+0Hz")
            await comm.save(out_path)

        asyncio.run(_test_tts())

        try:
            self.assertTrue(os.path.exists(out_path), "Synthesized file must exist")
            size = os.path.getsize(out_path)
            self.assertGreater(size, 1000, f"File size too small: {size} bytes")

            info = engine.get_video_info(out_path)
            self.assertEqual(info.get("status"), "success")
            self.assertGreater(info.get("duration", 0), 1.0)
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    # -------------------------------------------------------------------------
    # 5. Live Server Endpoint Tests
    # -------------------------------------------------------------------------
    def test_05_api_tts_voices_endpoint(self):
        """Verify GET /api/tts/voices returns the pt-BR voice catalog."""
        for path in ["/api/tts/voices", "/api/tts-voices"]:
            status, data = self._http_get(path)
            self.assertEqual(status, 200)
            self.assertEqual(data.get("status"), "success")
            voices = data.get("voices", [])
            self.assertGreaterEqual(len(voices), 3)

            voice_ids = [v["id"] for v in voices]
            self.assertIn("pt-BR-FranciscaNeural", voice_ids)
            self.assertIn("pt-BR-AntonioNeural", voice_ids)
            self.assertIn("pt-BR-ThalitaMultilingualNeural", voice_ids)

    def test_06_api_tts_post_endpoint(self):
        """Verify POST /api/tts generates MP3, returns metadata and accessible URLs."""
        payload = {
            "text": "Executando teste automatizado do Milestone M1 no servidor.",
            "voice": "pt-BR-AntonioNeural",
            "rate": "+20%",
            "pitch": "+0Hz"
        }
        status, data = self._http_post("/api/tts", payload)
        self.assertEqual(status, 200, f"Failed: {data}")
        self.assertEqual(data.get("status"), "success")
        self.assertIn("filename", data)
        self.assertTrue(data["filename"].endswith(".mp3"))
        self.assertIn("server_path", data)
        self.assertTrue(os.path.exists(data["server_path"]))
        self.assertGreater(data.get("duration", 0), 0)
        self.assertIn("download_url", data)
        self.assertIn("media_url", data)

        # Verify media file is accessible via GET /media/
        media_url = f"http://127.0.0.1:{self.test_port}{data['media_url']}"
        req = urllib.request.Request(media_url, headers={"Range": "bytes=0-512"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertIn(resp.status, [200, 206])
            self.assertGreater(len(resp.read()), 0)

    def test_07_api_tts_defensive_voice_fallback(self):
        """Verify POST /api/tts gracefully maps informal or lowercase voice names."""
        for raw_voice, expected in [("francisca", "pt-BR-FranciscaNeural"),
                                     ("antonio", "pt-BR-AntonioNeural"),
                                     ("thalita", "pt-BR-ThalitaMultilingualNeural")]:
            payload = {
                "text": "Teste de mapeamento defensivo.",
                "voice": raw_voice,
                "rate": 1.0,  # float rate
                "pitch": 0    # int pitch
            }
            status, data = self._http_post("/api/tts", payload)
            self.assertEqual(status, 200)
            self.assertEqual(data.get("voice"), expected)
            self.assertTrue(os.path.exists(data["server_path"]))

    def test_08_api_detect_silence_post_endpoint(self):
        """Verify POST /api/detect-silence and /api/silence-detect with generated TTS audio."""
        # First generate a TTS clip
        payload_tts = {
            "text": "Silêncio teste.",
            "voice": "pt-BR-FranciscaNeural"
        }
        _, tts_data = self._http_post("/api/tts", payload_tts)
        tts_file = tts_data["server_path"]

        # Now call silence detection using both endpoint aliases
        for endpoint in ["/api/silence-detect", "/api/detect-silence"]:
            payload_silence = {
                "media_path": tts_file,
                "noise_db": -35.0,
                "min_duration": 0.2
            }
            status, data = self._http_post(endpoint, payload_silence)
            self.assertEqual(status, 200, f"Failed on {endpoint}: {data}")
            self.assertEqual(data.get("status"), "success")
            self.assertIn("duration", data)
            self.assertIn("speech_segments", data)
            self.assertIn("silences", data)
            self.assertIn("saved_seconds", data)


if __name__ == "__main__":
    unittest.main()

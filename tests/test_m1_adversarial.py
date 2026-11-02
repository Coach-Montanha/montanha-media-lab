"""
Montanha Media Lab - Milestone M1 Adversarial Verification Suite
Empirically stress-tests:
1. Port resolution precedence: sys.argv[1] vs PORT env vs platform (Termux vs win32 vs linux fallback).
2. Live port binding & concurrency under ThreadingHTTPServer.
3. /media/ route resolution across DOWNLOADS_DIR, UPLOAD_DIR, OUTPUT_DIR.
4. /media/ non-existent file handling (404 status).
5. /media/ directory traversal security probe (relative dots, backslashes, URL encoded).
6. edge-tts audio generation & ffprobe deep stream inspection (codec, channels, sample rate).
7. get_video_info duration parity vs ffprobe format duration.
"""

import asyncio
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.parse
import urllib.request
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import engine
import server


def safe_unlink(path: Path, max_retries: int = 10, delay: float = 0.1):
    """Safely unlink a file on Windows with retries to account for async socket closures."""
    for _ in range(max_retries):
        try:
            if path.exists():
                path.unlink()
            return
        except PermissionError:
            time.sleep(delay)
    if path.exists():
        try:
            path.unlink()
        except Exception:
            pass


class TestM1AdversarialChallenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind an ephemeral port for live server tests
        cls.test_port = 4198
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", cls.test_port), server.UnifiedMediaStudioHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "httpd") and cls.httpd:
            cls.httpd.shutdown()
            cls.httpd.server_close()

    # -------------------------------------------------------------------------
    # 1. Port Resolution & Binding Logic
    # -------------------------------------------------------------------------
    def test_01_port_argv_precedence_over_env_and_default(self):
        """Verify sys.argv[1] strictly takes precedence over os.environ['PORT'] and defaults."""
        orig_argv = sys.argv.copy()
        orig_env = os.environ.get("PORT")
        try:
            # sys.argv priority
            sys.argv = ["server.py", "5555"]
            os.environ["PORT"] = "6666"
            self.assertEqual(server.get_default_port(), 5555)

            # Invalid argv falls back to env
            sys.argv = ["server.py", "invalid_port"]
            os.environ["PORT"] = "7777"
            self.assertEqual(server.get_default_port(), 7777)
        finally:
            sys.argv = orig_argv
            if orig_env is not None:
                os.environ["PORT"] = orig_env
            elif "PORT" in os.environ:
                del os.environ["PORT"]

    def test_02_port_env_precedence_over_platform_default(self):
        """Verify os.environ['PORT'] takes precedence over platform default when argv is absent."""
        orig_argv = sys.argv.copy()
        orig_env = os.environ.get("PORT")
        try:
            sys.argv = ["server.py"]
            os.environ["PORT"] = "8888"
            self.assertEqual(server.get_default_port(), 8888)

            # Invalid env port falls back to platform default
            os.environ["PORT"] = "not_a_number"
            if sys.platform == "win32" and not (os.path.exists("/sdcard") or os.path.exists("/data/data/com.termux")):
                self.assertEqual(server.get_default_port(), 4190)
        finally:
            sys.argv = orig_argv
            if orig_env is not None:
                os.environ["PORT"] = orig_env
            elif "PORT" in os.environ:
                del os.environ["PORT"]

    def test_03_port_platform_termux_vs_win32_simulation(self):
        """Simulate Termux, Windows, and Linux environments to verify platform default port calculation."""
        orig_argv = sys.argv.copy()
        orig_env = os.environ.get("PORT")
        try:
            sys.argv = ["server.py"]
            if "PORT" in os.environ:
                del os.environ["PORT"]

            # Scenario A: Termux via /data/data/com.termux
            with patch("os.path.exists") as mock_exists:
                mock_exists.side_effect = lambda p: p == "/data/data/com.termux"
                self.assertEqual(server.get_default_port(), 8080)

            # Scenario B: Termux via /sdcard
            with patch("os.path.exists") as mock_exists:
                mock_exists.side_effect = lambda p: p == "/sdcard"
                self.assertEqual(server.get_default_port(), 8080)

            # Scenario C: Windows (win32) with no Termux paths
            with patch("os.path.exists", return_value=False):
                with patch("sys.platform", "win32"):
                    self.assertEqual(server.get_default_port(), 4190)

            # Scenario D: Linux generic with no Termux paths
            with patch("os.path.exists", return_value=False):
                with patch("sys.platform", "linux"):
                    self.assertEqual(server.get_default_port(), 8080)
        finally:
            sys.argv = orig_argv
            if orig_env is not None:
                os.environ["PORT"] = orig_env
            elif "PORT" in os.environ:
                del os.environ["PORT"]

    def test_04_live_socket_concurrency(self):
        """Verify ThreadingHTTPServer can handle concurrent connections without blocking."""
        def make_request(path):
            conn = http.client.HTTPConnection("127.0.0.1", self.test_port, timeout=10)
            conn.request("GET", path)
            resp = conn.getresponse()
            data = resp.read()
            conn.close()
            return resp.status, data

        threads = []
        results = [None] * 5

        def worker(idx):
            results[idx] = make_request("/api/tts/voices")

        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        for i in range(5):
            self.assertIsNotNone(results[i])
            status, body = results[i]
            self.assertEqual(status, 200)
            self.assertIn(b"pt-BR-FranciscaNeural", body)

    # -------------------------------------------------------------------------
    # 2. /media/ Route Resolution & Security Probes
    # -------------------------------------------------------------------------
    def test_05_media_route_resolution_downloads_dir(self):
        """Verify file stored in DOWNLOADS_DIR is resolved and served via /media/."""
        fname = f"adv_test_dl_{int(time.time())}.txt"
        target = server.DOWNLOADS_DIR / fname
        target.write_text("DOWNLOADS_DIR content payload", encoding="utf-8")
        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.test_port, timeout=5)
            conn.request("GET", f"/media/{fname}")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            conn.close()
            self.assertIn(resp.status, [200, 206])
            self.assertEqual(body, "DOWNLOADS_DIR content payload")
        finally:
            time.sleep(0.05)
            safe_unlink(target)

    def test_06_media_route_resolution_upload_dir(self):
        """Verify file stored in UPLOAD_DIR (and absent in DOWNLOADS_DIR) is resolved and served."""
        fname = f"adv_test_up_{int(time.time())}.txt"
        target = server.UPLOAD_DIR / fname
        target.write_text("UPLOAD_DIR content payload", encoding="utf-8")
        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.test_port, timeout=5)
            conn.request("GET", f"/media/{fname}")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            conn.close()
            self.assertIn(resp.status, [200, 206])
            self.assertEqual(body, "UPLOAD_DIR content payload")
        finally:
            time.sleep(0.05)
            safe_unlink(target)

    def test_07_media_route_resolution_output_dir(self):
        """Verify file stored in OUTPUT_DIR (and absent in others) is resolved and served."""
        fname = f"adv_test_out_{int(time.time())}.txt"
        target = server.OUTPUT_DIR / fname
        target.write_text("OUTPUT_DIR content payload", encoding="utf-8")
        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.test_port, timeout=5)
            conn.request("GET", f"/media/{fname}")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            conn.close()
            self.assertIn(resp.status, [200, 206])
            self.assertEqual(body, "OUTPUT_DIR content payload")
        finally:
            time.sleep(0.05)
            safe_unlink(target)

    def test_08_media_route_non_existent_returns_404(self):
        """Verify non-existent files cleanly return 404 without traceback."""
        conn = http.client.HTTPConnection("127.0.0.1", self.test_port, timeout=5)
        conn.request("GET", "/media/non_existent_file_9988776655.mp3")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="ignore")
        conn.close()
        self.assertEqual(resp.status, 404)
        self.assertIn("Media not found", body)

    def test_09_media_route_directory_traversal_security_probe(self):
        """
        Adversarial probe: Attempt directory traversal outside media folders.
        Target: project file 'server.py' via:
        1. Relative traversal dots '../'
        2. Windows backslashes '..\\..\\'
        3. URL encoded dots '%2e%2e%2f'
        Expected Secure Behavior: 403 Forbidden or 404 Not Found (blocking path traversal).
        Vulnerable Behavior: 200 OK returning server.py source code.
        """
        traversal_attempts = [
            ("../../Documents/Projetos/montanha-media-lab/server.py", "relative forward slash"),
            ("..\\..\\Documents\\Projetos\\montanha-media-lab\\server.py", "Windows backslash"),
            ("%2e%2e%2f%2e%2e%2fDocuments%2fProjetos%2fmontanha-media-lab%2fserver.py", "URL-encoded traversal"),
        ]

        leaks = []
        for path_payload, desc in traversal_attempts:
            conn = http.client.HTTPConnection("127.0.0.1", self.test_port, timeout=5)
            conn.request("GET", f"/media/{path_payload}")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8", errors="ignore")
            conn.close()

            if resp.status == 200 and "UnifiedMediaStudioHandler" in body:
                leaks.append(f"Payload '{desc}' ({path_payload}) returned 200 OK and leaked server.py")

        self.assertEqual(
            leaks, [],
            f"SECURITY VULNERABILITY DETECTED in /media/ route resolution:\n" + "\n".join(leaks)
        )

    # -------------------------------------------------------------------------
    # 3. edge-tts Audio File Generation & ffprobe Integrity
    # -------------------------------------------------------------------------
    def test_10_edge_tts_audio_integrity_and_duration_parity(self):
        """
        Synthesize speech with edge-tts and perform deep audio stream validation using ffprobe:
        - Stream codec is 'mp3'
        - Sample rate is valid (>= 22050 Hz)
        - Audio channels is 1 (mono)
        - Format duration matches engine.get_video_info duration
        """
        import edge_tts
        temp_mp3 = Path(tempfile.gettempdir()) / f"adv_tts_probe_{int(time.time())}.mp3"
        test_text = "Montanha Media Lab teste de integridade profunda com ffprobe e medição de duração."

        async def _synth():
            comm = edge_tts.Communicate(test_text, "pt-BR-FranciscaNeural", rate="+0%", pitch="+0Hz")
            await comm.save(str(temp_mp3))

        asyncio.run(_synth())

        try:
            self.assertTrue(temp_mp3.exists(), "TTS file must be created")
            self.assertGreater(temp_mp3.stat().st_size, 2048, "File size should be > 2KB")

            # 1. Run ffprobe directly
            probe_cmd = [
                "ffprobe", "-v", "error", "-show_format", "-show_streams",
                "-print_format", "json", str(temp_mp3)
            ]
            proc = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            data = json.loads(proc.stdout)

            # Check format
            fmt = data.get("format", {})
            self.assertIn("mp3", fmt.get("format_name", "").lower(), f"Unexpected format: {fmt.get('format_name')}")
            raw_duration = float(fmt.get("duration", 0.0))
            self.assertGreater(raw_duration, 1.0, f"Duration too short: {raw_duration}")

            # Check audio stream
            streams = data.get("streams", [])
            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
            self.assertEqual(len(audio_streams), 1, "Must have exactly 1 audio stream")

            a_stream = audio_streams[0]
            self.assertEqual(a_stream.get("codec_name"), "mp3", "Codec must be mp3")
            self.assertIn(int(a_stream.get("sample_rate", 0)), [22050, 24000, 32000, 44100, 48000])
            self.assertEqual(int(a_stream.get("channels", 0)), 1, "Channels should be mono (1)")

            # 2. Check engine.get_video_info duration parity
            info = engine.get_video_info(str(temp_mp3))
            self.assertEqual(info.get("status"), "success")
            self.assertEqual(info.get("codec"), "mp3")
            self.assertTrue(info.get("has_audio"))
            engine_duration = float(info.get("duration", 0.0))

            # Parity check: difference should be within 0.05 seconds (rounding difference)
            self.assertAlmostEqual(raw_duration, engine_duration, delta=0.05,
                                  msg=f"Duration mismatch: ffprobe={raw_duration} vs engine={engine_duration}")

        finally:
            time.sleep(0.05)
            safe_unlink(temp_mp3)


if __name__ == "__main__":
    unittest.main()

import sys
import os
import time
import json
import threading
import urllib.request
import urllib.error

sys.path.insert(0, r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab")
import server
import engine

port = 4197
httpd = server.ThreadingHTTPServer(("127.0.0.1", port), server.UnifiedMediaStudioHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.5)

results = {}

def post(endpoint, payload):
    url = f"http://127.0.0.1:{port}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def get(path):
    url = f"http://127.0.0.1:{port}{path}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

try:
    # 1. Empty text validation
    s1, d1 = post("/api/tts", {"text": ""})
    results["empty_text"] = {"status_code": s1, "data": d1}

    # 2. Special chars & emojis in TTS
    s2, d2 = post("/api/tts", {"text": "Olá mundo & teste com caracteres especiais! 🎙️✨", "voice": "francisca"})
    results["special_chars"] = {"status_code": s2, "status": d2.get("status"), "has_duration": d2.get("duration", 0) > 0}

    # 3. Unknown voice fallback
    s3, d3 = post("/api/tts", {"text": "Voz desconhecida.", "voice": "robot_xyz_99"})
    results["unknown_voice"] = {"status_code": s3, "voice": d3.get("voice")}

    # 4. Path traversal check on /media/
    s4, d4 = get("/media/../server.py")
    results["path_traversal_media"] = {"status_code": s4, "bytes_served": len(d4) if s4 == 200 else 0}

    # 5. Non-existent media on silence-detect
    s5, d5 = post("/api/detect-silence", {"media_path": "does_not_exist_file.mp4"})
    results["missing_media_silence"] = {"status_code": s5, "data": d5}

    # 6. Concurrency test: 3 simultaneous requests
    conc_res = []
    def worker(n):
        s, d = post("/api/tts", {"text": f"Concorrência teste {n}", "voice": "antonio"})
        conc_res.append((n, s, d.get("status")))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    results["concurrency"] = conc_res

finally:
    httpd.shutdown()
    httpd.server_close()

print(json.dumps(results, indent=2))

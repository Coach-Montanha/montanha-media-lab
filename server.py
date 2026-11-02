"""
Montanha Media Lab & Video Studio — Unified 24/7 Local & Cloud Server
Consolidates:
- HTTP 206 Byte-Range Streaming (Zero-buffer playback)
- Multi-track Video Editor APIs (AutoCut, Export, Cloud Import, Silence Detection)
- PDF Intelligence Pro (Chapter Indexer & 5-in-1 Social Suite)
- Social Downloader (yt-dlp for TikTok, Instagram, YouTube)
- Photo & Lighting Analyzer (Pillow 32x32)
"""

import os
import sys
import json
import re
import shutil
import subprocess
import mimetypes
import urllib.parse
import urllib.request
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Directories & Configuration
BASE_DIR = Path(__file__).parent.resolve()
PUBLIC_DIR = BASE_DIR / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

# Shared Media Storage (Termux Android & Windows fallback)
if os.path.exists("/sdcard/Download"):
    DOWNLOADS_DIR = Path("/sdcard/Download/MontanhaMediaLab")
else:
    DOWNLOADS_DIR = Path.home() / "Downloads" / "MontanhaMediaLab"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = BASE_DIR / "exports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Import engine if available
try:
    import engine
except ImportError:
    engine = None

PDF_CACHE = {"texto_completo": "", "secoes": []}

def dividir_em_capitulos(texto):
    linhas = texto.split("\n")
    secoes = []
    bloco = []
    titulo = "Início / Introdução"
    padrao = re.compile(r'^(cap[ií]tulo|cap\.|se[çc][aã]o|m[oó]dulo|parte|\d+\.|\d+\s+[A-Z])', re.IGNORECASE)

    for l in linhas:
        s = l.strip()
        if not s: continue
        if len(s) < 60 and padrao.match(s):
            if bloco:
                secoes.append({"titulo": titulo, "texto": "\n".join(bloco).strip()})
                bloco = []
            titulo = s
        else:
            bloco.append(l)

    if bloco:
        secoes.append({"titulo": titulo, "texto": "\n".join(bloco).strip()})
    if len(secoes) <= 1:
        palavras = texto.split()
        secoes = []
        for i in range(0, len(palavras), 1800):
            secoes.append({"titulo": f"Trecho / Bloco {(i//1800)+1}", "texto": " ".join(palavras[i:i+1800])})
    return secoes


class UnifiedMediaStudioHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Range, Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        raw_path = urllib.parse.unquote(self.path)
        parsed = urllib.parse.urlparse(raw_path)

        # 1. Main Application HTML
        if parsed.path in ["/", "/index.html"]:
            index_file = PUBLIC_DIR / "index.html"
            if not index_file.exists():
                self.send_error(404, "index.html not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            with open(index_file, "rb") as f:
                self.wfile.write(f.read())
            return

        # 2. List Media Library (Scans DOWNLOADS_DIR, uploads, and exports)
        elif parsed.path in ["/api/list-media", "/api/get-recent-media"]:
            items = []
            valid_exts = {".mp4", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".aac", ".png", ".jpg", ".jpeg"}
            seen_names = set()

            scan_folders = [DOWNLOADS_DIR, UPLOAD_DIR, OUTPUT_DIR]
            for folder in scan_folders:
                if folder.exists():
                    for f in folder.iterdir():
                        if f.is_file() and f.suffix.lower() in valid_exts:
                            display_name = f.name
                            if display_name in seen_names:
                                continue
                            seen_names.add(display_name)
                            
                            ext = f.suffix.lower()
                            file_type = "video" if ext in {".mp4", ".mov", ".mkv", ".webm"} else ("audio" if ext in {".mp3", ".wav", ".aac"} else "image")
                            st = f.stat()
                            dur = 0.0
                            if file_type == "video" and engine:
                                try:
                                    info = engine.get_video_info(str(f))
                                    dur = info.get("duration", 0.0)
                                except Exception:
                                    dur = 0.0
                            
                            items.append({
                                "name": display_name,
                                "server_path": str(f),
                                "download_url": f"/stream?file={urllib.parse.quote(str(f))}",
                                "type": file_type,
                                "size_bytes": st.st_size,
                                "mtime": st.st_mtime,
                                "duration": dur
                            })
            items.sort(key=lambda x: x["mtime"], reverse=True)
            self._send_json({"status": "success", "media": items})
            return

        # 3. Stream Video/Audio with HTTP 206 Byte-Range (Zero-Buffer Streaming)
        elif parsed.path == "/stream":
            query = urllib.parse.parse_qs(parsed.query)
            file_param = query.get("file", [""])[0]
            if not file_param:
                self.send_error(400, "Missing file parameter")
                return
            target_path = Path(file_param).resolve()
            if not target_path.exists() or not target_path.is_file():
                self.send_error(404, "File not found")
                return
            self._serve_file_with_range(target_path)
            return

        elif parsed.path.startswith("/media/"):
            rel_path = parsed.path.replace("/media/", "")
            target_path = (DOWNLOADS_DIR / rel_path).resolve()
            if not target_path.exists():
                target_path = (UPLOAD_DIR / rel_path).resolve()
            if not target_path.exists() or not target_path.is_file():
                self.send_error(404, "Media not found")
                return
            self._serve_file_with_range(target_path)
            return

        # 4. ADB Camera Sync (Redmi 12 over USB)
        elif parsed.path == "/api/adb-camera":
            try:
                cmd = ["adb", "shell", "ls", "-t", "/sdcard/DCIM/Camera/*.mp4"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                files = [l.strip() for l in res.stdout.split("\n") if l.strip().endswith(".mp4")]
                if not files:
                    self._send_json({"status": "error", "message": "Nenhum vídeo encontrado na câmera do Redmi 12"})
                    return
                latest_remote = files[0]
                local_name = Path(latest_remote).name
                local_dest = DOWNLOADS_DIR / local_name
                pull_cmd = ["adb", "pull", latest_remote, str(local_dest)]
                subprocess.run(pull_cmd, check=True, timeout=30)
                self._send_json({
                    "status": "success",
                    "filename": local_name,
                    "url": f"/stream?file={urllib.parse.quote(str(local_dest))}",
                    "path": str(local_dest)
                })
            except Exception as e:
                self._send_json({"status": "error", "message": f"Erro ADB: {str(e)}"})
            return

        # 5. Static Files in public/
        static_file = (PUBLIC_DIR / parsed.path.lstrip("/")).resolve()
        if static_file.exists() and static_file.is_file():
            self._serve_file_with_range(static_file)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        raw_path = urllib.parse.unquote(self.path)
        parsed = urllib.parse.urlparse(raw_path)
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        # A. JSON POST Requests (Video Studio Engine APIs)
        if "application/json" in content_type:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            body = json.loads(raw_body) if raw_body else {}

            # Import Cloud URL (Drive, Dropbox, Photos, Web)
            if parsed.path == "/api/import-cloud-url":
                url = body.get("url", "").strip()
                if not url:
                    self._send_json({"status": "error", "message": "URL vazia"})
                    return
                try:
                    import yt_dlp
                    ydl_opts = {
                        "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
                        "format": "best[ext=mp4]/best",
                        "quiet": True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)
                    self._send_json({
                        "status": "success",
                        "filename": Path(filename).name,
                        "url": f"/stream?file={urllib.parse.quote(filename)}",
                        "path": filename
                    })
                except Exception as e:
                    # Fallback direct download
                    try:
                        dest_file = DOWNLOADS_DIR / f"cloud_import_{int(os.times().elapsed)}.mp4"
                        urllib.request.urlretrieve(url, str(dest_file))
                        self._send_json({
                            "status": "success",
                            "filename": dest_file.name,
                            "url": f"/stream?file={urllib.parse.quote(str(dest_file))}",
                            "path": str(dest_file)
                        })
                    except Exception as e2:
                        self._send_json({"status": "error", "message": f"Erro no download: {str(e2)}"})
                return

            # Silence Detection for AutoCut
            elif parsed.path == "/api/silence-detect":
                video_path = body.get("video_path")
                if not video_path or not os.path.exists(video_path):
                    self._send_json({"status": "error", "message": "Arquivo de vídeo não encontrado"})
                    return
                if engine:
                    res = engine.detect_silence_points(video_path)
                    self._send_json({"status": "success", **res})
                else:
                    self._send_json({"status": "error", "message": "Engine não carregada"})
                return

            # Subtitle Generation (Whisper INT8)
            elif parsed.path == "/api/generate-subtitles":
                video_path = body.get("video_path")
                if not video_path or not os.path.exists(video_path):
                    self._send_json({"status": "error", "message": "Arquivo não encontrado"})
                    return
                srt_out = str(OUTPUT_DIR / f"sub_{Path(video_path).stem}.srt")
                ass_out = str(OUTPUT_DIR / f"sub_{Path(video_path).stem}.ass")
                if engine:
                    try:
                        res = engine.generate_subtitles(video_path, srt_out, ass_out)
                        self._send_json({"status": "success", **res})
                    except Exception as err:
                        self._send_json({"status": "error", "message": str(err)})
                else:
                    self._send_json({"status": "error", "message": "Engine não disponível"})
                return

            # Final Video Export (Cuts + Burn Subtitles + Aspect Ratio)
            elif parsed.path == "/api/export-final":
                video_path = body.get("video_path")
                clips = body.get("clips", [])
                ass_path = body.get("ass_path")
                ratio = body.get("ratio", "9/16")
                
                if not video_path or not os.path.exists(video_path):
                    self._send_json({"status": "error", "message": "Vídeo fonte não encontrado"})
                    return
                
                out_name = f"export_{Path(video_path).stem}_{int(os.times().elapsed)}.mp4"
                out_final = OUTPUT_DIR / out_name
                
                if engine:
                    try:
                        res = engine.render_final_video(video_path, str(out_final), clips, ass_path, ratio)
                        self._send_json({
                            "status": "success",
                            "download_url": f"/stream?file={urllib.parse.quote(str(out_final))}",
                            "filename": out_name,
                            "path": str(out_final)
                        })
                    except Exception as err:
                        self._send_json({"status": "error", "message": f"Erro na renderização: {str(err)}"})
                else:
                    self._send_json({"status": "error", "message": "Engine indisponível"})
                return

            elif parsed.path == "/api/delete-media":
                file_path = body.get("path")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self._send_json({"status": "success", "message": "Arquivo removido com sucesso"})
                    except Exception as err:
                        self._send_json({"status": "error", "message": str(err)})
                else:
                    self._send_json({"status": "error", "message": "Arquivo não encontrado"})
                return

            elif parsed.path == "/api/open-folder":
                try:
                    if sys.platform == "win32":
                        os.startfile(str(DOWNLOADS_DIR))
                    else:
                        subprocess.run(["xdg-open", str(DOWNLOADS_DIR)])
                    self._send_json({"status": "success", "message": "Pasta aberta no explorador"})
                except Exception as err:
                    self._send_json({"status": "error", "message": str(err)})
                return

        # B. Multipart Form POST Requests (Media Lab: PDF Pro, Downloader, Foto & Direct Uploads)
        body = self.rfile.read(content_length)
        boundary = content_type.split("boundary=")[-1].encode() if "boundary=" in content_type else b""
        partes = body.split(b"--" + boundary) if boundary else []

        # 0. DIRECT UPLOAD HANDLER (/api/upload for PC & Mobile)
        if parsed.path == "/api/upload":
            upload_filename = "upload_midia.mp4"
            uploaded_bytes = None
            for p in partes:
                if b'filename="' in p:
                    try:
                        header_part = p.split(b"\r\n\r\n", 1)[0].decode("utf-8", "ignore")
                        match = re.search(r'filename="([^"]+)"', header_part)
                        if match:
                            upload_filename = Path(match.group(1)).name
                    except Exception:
                        pass
                    uploaded_bytes = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0]
                    break

            if uploaded_bytes:
                safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', upload_filename)
                if not safe_name:
                    safe_name = f"upload_{int(os.times().elapsed)}.mp4"
                target_file = DOWNLOADS_DIR / safe_name
                with open(target_file, "wb") as f:
                    f.write(uploaded_bytes)

                dur = 0.0
                if engine and safe_name.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
                    try:
                        info = engine.get_video_info(str(target_file))
                        dur = info.get("duration", 0.0)
                    except Exception:
                        dur = 0.0

                self._send_json({
                    "status": "success",
                    "filename": safe_name,
                    "server_path": str(target_file),
                    "download_url": f"/stream?file={urllib.parse.quote(str(target_file))}",
                    "info": {"duration": dur}
                })
                return
            else:
                self._send_json({"status": "error", "message": "Nenhum arquivo enviado"})
                return

        acao, url_midia, formato_midia, file_bytes, idx_secao = "transcrever", "", "video", None, 0
        for p in partes:
            if b'name="acao"' in p:
                acao = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore")
            elif b'name="url_midia"' in p:
                url_midia = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore").strip()
            elif b'name="formato_midia"' in p:
                formato_midia = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore")
            elif b'name="idx_secao"' in p:
                try: idx_secao = int(p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore"))
                except: idx_secao = 0
            elif b'filename="' in p:
                file_bytes = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0]

        res = {"sucesso": True, "tipo": acao}

        # 1. Downloader Social (yt-dlp)
        if acao == "download_url":
            if not url_midia:
                res["status"] = "Cole uma URL válida."
            else:
                cmd = ["yt-dlp", "--no-warnings", "--no-check-certificates", "--concurrent-fragments", "4", "-P", str(DOWNLOADS_DIR)]
                if formato_midia == "audio":
                    cmd += ["-x", "--audio-format", "mp3", url_midia]
                else:
                    cmd += ["-f", "b[ext=mp4]/b", url_midia]
                try:
                    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    if p.returncode == 0:
                        res["status"] = f"✓ Download Concluído! Salvo em: {DOWNLOADS_DIR}"
                    else:
                        res["status"] = f"Aviso de download:\n{p.stderr[:300] or p.stdout[:300]}"
                except Exception as err:
                    res["status"] = f"Erro no download: {err}"

        # 2. Extração Direta de MP3
        elif acao == "audio":
            tmp_vid = BASE_DIR / "temp_vid.mp4"
            out_mp3 = DOWNLOADS_DIR / f"audio_{int(os.times().elapsed)}.mp3"
            if file_bytes:
                with open(tmp_vid, "wb") as f: f.write(file_bytes)
                subprocess.run(["ffmpeg", "-i", str(tmp_vid), "-vn", "-acodec", "libmp3lame", "-b:a", "192k", str(out_mp3), "-y"], capture_output=True)
                res["status"] = f"✓ Áudio MP3 extraído com sucesso!\nSalvo em: {out_mp3.name}"

        # 3. PDF Intelligence Pro (Indexador & Suíte)
        elif acao == "pdf_indexar":
            tmp_pdf = BASE_DIR / "temp_doc.pdf"
            tmp_txt = BASE_DIR / "temp_doc.txt"
            if file_bytes:
                with open(tmp_pdf, "wb") as f: f.write(file_bytes)
                subprocess.run(["pdftotext", str(tmp_pdf), str(tmp_txt)], capture_output=True)
                texto = ""
                if os.path.exists(tmp_txt):
                    with open(tmp_txt, "r", encoding="utf-8", errors="ignore") as tf: texto = tf.read().strip()
                secoes = dividir_em_capitulos(texto)
                PDF_CACHE["texto_completo"] = texto
                PDF_CACHE["secoes"] = secoes
                res["capitulos"] = [{"idx": i, "titulo": sec["titulo"]} for i, sec in enumerate(secoes)]

        elif acao == "pdf_gerar":
            if not PDF_CACHE["secoes"] or idx_secao >= len(PDF_CACHE["secoes"]):
                res["status"] = "Capítulo inválido."
            else:
                cap = PDF_CACHE["secoes"][idx_secao]
                trecho, titulo = cap["texto"], cap["titulo"]
                amostra = trecho[:4000] if len(trecho) > 4000 else trecho
                res["transcricao_trecho"] = trecho
                res["prompt_suite"] = (
                    f"Aja como redator e estrategista do Ecossistema Montanha. Com base estrita no trecho '{titulo}' abaixo, gere em Markdown:\n\n"
                    f"TRECHO DO CONTEÚDO:\n---\n{amostra}\n---\n\n"
                    f"1. RESUMO SUCINTO (3 frases de impacto)\n"
                    f"2. RESUMO COMPLETO (Conceitos centrais em tópicos)\n"
                    f"3. CARROSSEL DE 5 A 7 LÂMINAS + LEGENDA COMPLETA com 5 hashtags\n"
                    f"4. ROTEIRO DE REELS / TIKTOK (45-60s com gancho 0-3s, 3 pontos e CTA)\n"
                    f"5. ROTEIRO DE STORIES (4 stories interativos)\n\n"
                    f"DIRETIVA: Sem introduções, entregue o pacote pronto para publicação."
                )

        # 4. Foto & Análise de Iluminação (Pillow 32x32)
        elif acao == "foto_prompt":
            tmp_img = BASE_DIR / "temp_img.jpg"
            if file_bytes:
                with open(tmp_img, "wb") as f: f.write(file_bytes)
                try:
                    im = Image.open(tmp_img)
                    w, h = im.size
                    ratio = "9:16" if h > w else ("16:9" if w > h else "1:1")
                    im_small = im.resize((32, 32)).convert("L")
                    pixels = list(im_small.getdata())
                    avg_lum = sum(pixels) / len(pixels)
                    ilum = "Dramática / Low-Key" if avg_lum < 85 else ("Suave / High-Key" if avg_lum > 170 else "Equilibrada de Estúdio")
                    res["analise"] = f"Dimensões: {w}x{h} | Proporção: {ratio} | Iluminação: {ilum}"
                    res["prompt"] = f"Cinematic shot, aspect ratio {ratio}, lighting {ilum}, hyper-detailed, 8k resolution, professional color grading."
                except Exception as err:
                    res["status"] = f"Erro na análise da imagem: {err}"

        self._send_json(res)

    def _serve_file_with_range(self, file_path: Path):
        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "video/mp4" if file_path.suffix.lower() == ".mp4" else "application/octet-stream"

        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_left = length
                    while bytes_left > 0:
                        chunk_size = min(bytes_left, 64 * 1024)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        try:
                            self.wfile.write(data)
                        except (ConnectionResetError, BrokenPipeError):
                            break
                        bytes_left -= len(data)
                return

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def _send_json(self, data: dict, status: int = 200):
        resp = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), UnifiedMediaStudioHandler)
    print(f"\n=======================================================")
    print(f"[*] MONTANHA MEDIA LAB & VIDEO STUDIO UNIFICADO ATIVO!")
    print(f"[*] Local: http://localhost:{port}")
    print(f"📁 Pasta de Mídia: {DOWNLOADS_DIR}")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8080))
    run_server(port)

import http.server
import socketserver
import os
import json
import re
import subprocess
from PIL import Image

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = "/sdcard/Download/MontanhaStudio"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

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
            if bloco: secoes.append({"titulo": titulo, "texto": "\n".join(bloco).strip()}); bloco = []
            titulo = s
        else: bloco.append(l)

    if bloco: secoes.append({"titulo": titulo, "texto": "\n".join(bloco).strip()})
    if len(secoes) <= 1:
        palavras = texto.split()
        secoes = []
        for i in range(0, len(palavras), 1800):
            secoes.append({"titulo": f"Trecho / Bloco {(i//1800)+1}", "texto": " ".join(palavras[i:i+1800])})
    return secoes

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self.send_response(200); self.send_header("Content-type", "text/html; charset=utf-8"); self.end_headers()
            with open(os.path.join(BASE_DIR, "index.html"), "rb") as f: self.wfile.write(f.read())
            return
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        boundary = self.headers.get('Content-Type', '').split("boundary=")[-1].encode()
        partes = body.split(b"--" + boundary)

        acao, url_midia, formato_midia, file_bytes, idx_secao = "transcrever", "", "video", None, 0
        for p in partes:
            if b'name="acao"' in p: acao = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore")
            elif b'name="url_midia"' in p: url_midia = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore").strip()
            elif b'name="formato_midia"' in p: formato_midia = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore")
            elif b'name="idx_secao"' in p:
                try: idx_secao = int(p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0].decode("utf-8", "ignore"))
                except: idx_secao = 0
            elif b'filename="' in p: file_bytes = p.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0]

        res = {"sucesso": True, "tipo": acao}

        # -------------------------------------------------------------
        # 1. TRANSCRIÇÃO DUPLA (LIMPA + COM TIMESTAMPS/LEGENDAS .SRT)
        # -------------------------------------------------------------
        if acao == "transcrever":
            tmp_vid = os.path.join(BASE_DIR, "temp_vid.mp4")
            out_wav = os.path.join(BASE_DIR, "audio_16k.wav")
            out_base = os.path.join(DOWNLOADS_DIR, "legenda_whisper")
            
            if file_bytes:
                with open(tmp_vid, "wb") as f: f.write(file_bytes)
                # Extrai audio WAV 16k mono (obrigatorio pro whisper)
                subprocess.run(["ffmpeg", "-i", tmp_vid, "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", out_wav, "-y"], capture_output=True)

            whisper_bin = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
            whisper_model = os.path.expanduser("~/models/ggml-base.bin")

            if not os.path.exists(whisper_bin) or not os.path.exists(whisper_model):
                res["status"] = "Motor Whisper ou modelo ainda não compilado no Termux."
            else:
                # Gera SRT (com timestamps) e texto limpo
                cmd = [
                    whisper_bin, "-m", whisper_model, "-f", out_wav,
                    "-l", "pt", "-osrt", "-of", out_base, "-t", "4"
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                
                srt_path = out_base + ".srt"
                txt_path = out_base + ".txt"

                # Leitura do SRT com timestamps
                srt_conteudo = ""
                if os.path.exists(srt_path):
                    with open(srt_path, "r", encoding="utf-8", errors="ignore") as sf:
                        srt_conteudo = sf.read().strip()
                else:
                    srt_conteudo = proc.stdout.strip()

                # Remove timestamps para criar a transcrição limpa de leitura
                texto_limpo = re.sub(r'\d+\n\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d\n', '', srt_conteudo)
                texto_limpo = re.sub(r'\[\d\d:\d\d:\d\d\.\d\d\d --> \d\d:\d\d:\d\d\.\d\d\d\]\s*', '', texto_limpo).strip()

                prompt_legendas = (
                    f"Aja como um editor profissional de vídeos curtos (Reels, TikTok, Shorts). "
                    f"Abaixo está a transcrição marcada com timestamps de um vídeo real. "
                    f"Execute duas coisas:\n"
                    f"1. CORREÇÃO DE LEGENDAS: Ajuste termos técnicos, nomes próprios e pontuação sem alterar os timestamps.\n"
                    f"2. PALAVRAS-CHAVE DINÂMICAS: Indique quais palavras devem receber destaque colorido/animação estilo Hormozi para prender a atenção.\n\n"
                    f"TRANSCRIÇÃO MARCADA:\n---\n{srt_conteudo[:3000]}\n---"
                )

                res["transcricao_pura"] = texto_limpo
                res["transcricao_marcada"] = srt_conteudo
                res["prompt_legendas"] = prompt_legendas
                res["caminho_srt"] = srt_path

        # -------------------------------------------------------------
        # 2. DOWNLOAD RÁPIDO OTIMIZADO (SEM CONVERSÕES PESADAS)
        # -------------------------------------------------------------
        elif acao == "download_url":
            if not url_midia:
                res["status"] = "Cole uma URL válida."
            else:
                # Otimizacao radical: baixa stream nativo mais rapido sem recomprimir
                cmd = ["yt-dlp", "--no-warnings", "--no-check-certificates", "--concurrent-fragments", "4", "-P", DOWNLOADS_DIR]
                if formato_midia == "audio":
                    cmd += ["-x", "--audio-format", "mp3", url_midia]
                else:
                    cmd += ["-f", "b[ext=mp4]/b", url_midia]

                try:
                    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    if p.returncode == 0:
                        res["status"] = "✓ Download Concluído com sucesso!\nSalvo em: Download/MontanhaStudio"
                    else:
                        res["status"] = f"Aviso de download:\n{p.stderr[:300] or p.stdout[:300]}"
                except Exception as err:
                    res["status"] = f"Erro no download: {err}"

        # -------------------------------------------------------------
        # 3. EXTRAÇÃO DIRETA DE MP3
        # -------------------------------------------------------------
        elif acao == "audio":
            tmp_vid = os.path.join(BASE_DIR, "temp_vid.mp4")
            out_mp3 = os.path.join(DOWNLOADS_DIR, "audio_extraido.mp3")
            if file_bytes:
                with open(tmp_vid, "wb") as f: f.write(file_bytes)
                subprocess.run(["ffmpeg", "-i", tmp_vid, "-vn", "-acodec", "libmp3lame", "-b:a", "192k", out_mp3, "-y"], capture_output=True)
                res["status"] = f"✓ Áudio MP3 extraído com sucesso!\nSalvo em: {out_mp3}"

        # -------------------------------------------------------------
        # 4. PDF INDEXER & SUITE
        # -------------------------------------------------------------
        elif acao == "pdf_indexar":
            tmp_pdf = os.path.join(BASE_DIR, "temp_doc.pdf")
            tmp_txt = os.path.join(BASE_DIR, "temp_doc.txt")
            if file_bytes:
                with open(tmp_pdf, "wb") as f: f.write(file_bytes)
                subprocess.run(["pdftotext", tmp_pdf, tmp_txt], capture_output=True)
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
                prompt_suite = (
                    f"Aja como redator e estrategista do Ecossistema Montanha. Com base estrita no trecho '{titulo}' abaixo, gere em Markdown:\n\n"
                    f"TRECHO DO CONTEÚDO:\n---\n{amostra}\n---\n\n"
                    f"1. RESUMO SUCINTO (3 frases de impacto)\n"
                    f"2. RESUMO COMPLETO (Conceitos, argumentos e lições centrais em tópicos)\n"
                    f"3. CARROSSEL DE 5 A 7 LÂMINAS (Lâmina 1 gancho anti-mito, Lâminas 2-5 método prático, CTA final) + LEGENDA COMPLETA com 5 hashtags\n"
                    f"4. ROTEIRO DE REELS / TIKTOK (45-60s com gancho 0-3s, 3 pontos e CTA)\n"
                    f"5. ROTEIRO DE STORIES (4 stories: Enquete polêmica, Erro comum, Virada de chave e Caixa de perguntas)\n\n"
                    f"DIRETIVA: Sem introduções ou enrolação, entregue o pacote pronto para publicação."
                )
                res["prompt_suite"] = prompt_suite

        resp = json.dumps(res, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(resp))); self.end_headers()
        self.wfile.write(resp)

with socketserver.TCPServer(("", PORT), H) as s:
    print(f"\n[+] MONTANHA STUDIO PRO (WHISPER DUPLO + FAST DL) ATIVO! Acesse: http://localhost:{PORT}")
    s.serve_forever()

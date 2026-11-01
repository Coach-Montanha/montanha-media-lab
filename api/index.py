from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        
        # Resposta Serverless para Vercel
        res = {
            "sucesso": True,
            "ambiente": "Vercel Serverless Edge",
            "mensagem": "Endpoint ativo pronto para orquestração híbrida (Local / Nuvem)"
        }
        
        resp = json.dumps(res, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "online", "engine": "Montanha Studio Vercel Edge"}).encode())
        return

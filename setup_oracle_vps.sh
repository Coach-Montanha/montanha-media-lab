#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE PROVISIONAMENTO 1-CLIQUE: ORACLE CLOUD ALWAYS FREE (ARM / X86)
# Ecossistema Montanha - Montanha Video Studio & Media Lab 24/7
# ==============================================================================
set -e

echo "🚀 Iniciando configuração do Servidor 24/7 na Oracle Cloud..."

# 1. Atualizar repositórios do Ubuntu
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependências de sistema (Python, FFmpeg acelerado, Git, Curl)
sudo apt install -y python3 python3-pip python3-venv ffmpeg git curl wget htop ufw

# 3. Configurar diretório do projeto
PROJECT_DIR="/opt/montanha-video-studio"
echo "📂 Configurando diretório em $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

# 4. Criar ambiente virtual Python otimizado
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Instalar pacotes essenciais do editor
pip install --no-cache-dir \
    yt-dlp \
    pillow \
    requests \
    urllib3

# 5. Instalar Cloudflare Tunnel oficial (cloudflared)
if ! command -v cloudflared &> /dev/null; then
    echo "🌐 Instalando Cloudflare Tunnel oficial..."
    ARCH=$(dpkg --print-architecture)
    if [ "$ARCH" = "arm64" ]; then
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
    else
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    fi
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
fi

# 6. Criar serviço systemd para rodar 24/7 ininterrupto (Reinicia sozinho após reboot)
echo "⚙️ Configurando serviço autônomo systemd..."
sudo tee /etc/systemd/system/montanha-studio.service > /dev/null <<EOF
[Unit]
Description=Montanha Video Studio 24/7 Daemon
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/app.py 4190
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 7. Ativar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable montanha-studio.service

# 8. Script Keep-Alive Anti-Ociosidade da Oracle (Evita suspensão por idle)
echo "🛡️ Configurando proteção anti-ociosidade Always Free..."
sudo tee /usr/local/bin/oracle-keepalive.sh > /dev/null <<'EOF'
#!/bin/bash
# Gera pequena carga periódica (2 min a cada 6 horas) para garantir que a Oracle
# nunca considere a instância ociosa nos critérios de CPU Always Free.
python3 -c "import time, math; t = time.time() + 60; [math.factorial(500) for _ in iter(lambda: time.time() < t, False)]"
EOF
sudo chmod +x /usr/local/bin/oracle-keepalive.sh

# Adicionar no cron para rodar 4x ao dia
(crontab -l 2>/dev/null | grep -v 'oracle-keepalive.sh' ; echo "0 */6 * * * /usr/local/bin/oracle-keepalive.sh >/dev/null 2>&1") | crontab -

echo "===================================================================="
echo "✅ Servidor Oracle Cloud provisionado com sucesso!"
echo "➡️  Para iniciar o Cloudflare Tunnel conectado ao seu domínio:"
echo "    cloudflared tunnel --url http://127.0.0.1:4190"
echo "===================================================================="

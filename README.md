# Montanha Studio

<p align="center">
  <img src="public/favicon.svg" width="120" height="120" alt="Montanha Studio Logo">
</p>

> **Processamento Criativo Local, Extração Visual, Transcrição Whisper & Automação de Conteúdo.**
> Projetado para máxima eficiência e independência de nuvem sob a diretriz `/eco`.

---

## ⚡ Visão Geral do Projeto

O **Montanha Studio** é um ecossistema híbrido que opera tanto localmente no smartphone (otimizado para processadores ARM64 como o MediaTek Helio G88 no Xiaomi Redmi 12 com HyperOS) quanto em ambiente serverless na **Vercel** ou servidores headless.

### 🎯 Funcionalidades Principais:
1. **🎬 Vídeo, Transcrição & Legendas (.SRT):**
   - Transcrição neural de fala offline utilizando `whisper.cpp` (modelo GGML Base em português).
   - Saída dupla: Legenda sincronizada `.srt` com timestamps + Texto limpo contínuo.
   - Gerador de Prompt Especialista para Legendas Dinâmicas estilo Hormozi.
   - Extração instantânea de MP3 via FFmpeg nativo.
2. **📄 PDF Intelligence Pro:**
   - Indexador automático de livros, tratados e artigos em capítulos e seções.
   - Seletor de capítulos para geração de Suíte Completa: Resumo Sucinto (3 frases), Resumo Completo, Carrossel de 5-7 Lâminas com legenda e Roteiros de Reels e Stories.
3. **📥 Downloader Ultra Rápido:**
   - Download acelerado de vídeos e áudios do TikTok, Instagram e YouTube sem anúncios nem marcas d'água via `yt-dlp`.
   - Armazenamento direto na pasta acessível pela Galeria (`Download/MontanhaStudio`).
4. **📷 Foto & Composição Visual (Needle):**
   - Extração de variáveis visuais (iluminação, proporção 9:16/16:9, enquadramento e paleta de cores) sem envio para nuvem.
   - Montagem de Prompt técnico em inglês pronto para Antigravity, Midjourney ou Flux.
5. **📱 APK Nativo Android & Apple UI:**
   - Interface inspirada nas Human Interface Guidelines (HIG) da Apple: Dark Mode OLED, acabamento *frosted glass* e controle segmentado de abas.
   - Empacotado em APK leve para Android 14/15 (HyperOS).

---

## 📂 Estrutura do Repositório

```text
montanha-studio/
├── public/                 # Interface Web Apple HIG & Assets estáticos
│   ├── index.html          # Frontend responsivo com Glassmorphism
│   ├── favicon.svg         # Favicon vetorial com gradiente Apple
│   ├── favicon.ico         # Ícone de compatibilidade
│   └── manifest.json       # PWA Manifest para instalação
├── api/                    # Serverless Functions (Deploy Vercel)
│   └── index.py            # API Gateway para execução em nuvem
├── android/                # Código-fonte e build do APK nativo
│   ├── MainActivity.java   # WebView nativa com file chooser
│   ├── AndroidManifest.xml # Permissões de armazenamento e cleartext HTTP
│   └── gerar_apk.sh        # Script de compilação autônoma via Termux
├── server.py               # Servidor local Python para Termux (Porta 8080)
├── vercel.json             # Configuração de rotas e build da Vercel
├── package.json            # Metadados do projeto
└── README.md               # Documentação técnica completa
```

---

## 🚀 Como Executar Localmente (Android / Termux)

1. Clone ou copie a pasta para o seu Termux:
```bash
git clone https://github.com/SEU_USUARIO/montanha-studio.git
cd montanha-studio
```

2. Inicie o estúdio local:
```bash
python server.py
```
*(Ou use o atalho configurado `ligar`)*.

3. Abra o aplicativo instalado **Montanha Studio** ou acesse no navegador:  
👉 `http://localhost:8080`

---

## ☁️ Deploy na Vercel (1 Clique)

1. Faça o fork ou envie este repositório para o seu **GitHub**.
2. Conecte o repositório na **Vercel** (`New Project > Import`).
3. O arquivo [`vercel.json`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/montanha-studio/vercel.json) já está configurado para entregar o frontend estático e as rotas de API automaticamente com zero configurações adicionais.

---

## 🛡️ Licença
Distribuído sob a licença MIT. Criado para o **Ecossistema Montanha**.

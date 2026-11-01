# Dossiê Técnico Completo: Montanha Media Lab
**Documento de Continuidade de Conversa (Handoff & Context Export)**

---

## 1. Visão Geral do Projeto e Identidade
- **Nome Oficial:** Montanha Media Lab
- **Diretório Local (Windows):** `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\`
- **Repositório GitHub:** `https://github.com/Coach-Montanha/montanha-media-lab.git` (ou legado: `montanha-studio.git`)
- **Deploy Nuvem:** Pronto para Vercel via `vercel.json` e `api/index.py` (Python Serverless + Static Edge).
- **Diretiva Mestre:** `/eco` (Ultra-eficiência, zero tokens desperdiçados, blindagem térmica e simplicidade cirúrgica).
- **Design System:** Apple Human Interface Guidelines (Onyx Dark Mode, Frosted Glass `backdrop-filter: blur(25px)`, iOS Segmented Control, botões `#2997ff` com haptics).

---

## 2. Hardware e Ambiente Alvo (Dispositivo Móvel)
- **Smartphone:** Xiaomi Redmi 12 4G
- **Processador:** MediaTek Helio G88 (2x Cortex-A75 @ 2.0 GHz + 6x Cortex-A55 @ 1.8 GHz, GPU Mali-G52 MC2)
- **Sistema Operacional:** Xiaomi HyperOS 2.0 / Android 15 (115 GB livres)
- **Ambiente de Execução:** Termux (ARM64 v8a oficial via GitHub/F-Droid) + Python 3.11/3.12 + FFmpeg + Whisper.cpp + Poppler + yt-dlp.
- **Pasta de Mídia Acessível na Galeria:** `/sdcard/Download/MontanhaMediaLab`

---

## 3. Arquitetura dos Módulos do Montanha Media Lab

### A. Módulo 1: Vídeo, Transcrição & Legendas (.SRT)
- **Motor:** `whisper.cpp` compilado localmente em C++ (`~/whisper.cpp/build/bin/whisper-cli`) com modelo `ggml-base.bin` (~140 MB em português).
- **Saídas Simultâneas:**
  1. `.srt` sincronizado com timestamps exatos (`00:01 --> 00:04`).
  2. Transcrição limpa de fala contínua para artigos e roteiros.
  3. Prompt Especialista para Legendas Dinâmicas (destaques estilo Hormozi).
  4. Extração de áudio MP3 192k em 1 segundo via FFmpeg.

### B. Módulo 2: PDF Intelligence Pro (Indexador de Capítulos)
- **Motor:** `pdftotext` (Poppler) + Regex de capítulos em Python.
- **Funcionamento:**
  - Indexa livros/tratados inteiros e divide automaticamente por capítulos e seções.
  - Seletor dinâmico de capítulos na tela.
  - Geração da **Suíte Editorial Completa (5 em 1)**:
    1. Resumo Sucinto (Executive Summary em 3 frases).
    2. Resumo Completo em tópicos conceituais.
    3. Carrossel de 5 a 7 Lâminas + Legenda com 5 hashtags.
    4. Roteiro de Reels/TikTok de 45-60s (Gancho, 3 atos, CTA).
    5. Sequência de 4 Stories Interativos (Enquete, quebra de mito, virada e CTA).

### C. Módulo 3: Downloader Rápido (TikTok, Instagram, YouTube)
- **Motor:** `yt-dlp` com aceleração por fragmentos paralelos (`--concurrent-fragments 4`) e formato nativo pré-mesclado (`b[ext=mp4]`).
- **Salvamento:** Direto na pasta da Galeria (`/sdcard/Download/MontanhaMediaLab`), sem travar o processador com recompreensão desnecessária.

### D. Módulo 4: Foto & Composição Visual (Needle Local)
- **Motor:** Pillow (`PIL`) com amostragem algorítmica ultrarrápida (32x32 pixels).
- **Extração:** Proporção de tela (9:16, 16:9, 1:1), brilho médio, tipo de iluminação e paleta de cores.
- **Geração:** JSON estruturado de estilo + Prompt cinematográfico em inglês técnico pronto para Antigravity/Midjourney/Flux.

---

## 4. Estrutura do Repositório (`montanha-media-lab`)

```text
montanha-media-lab/
├── public/                 # Frontend Apple HIG
│   ├── index.html          # UI completa responsiva com Glassmorphism
│   ├── favicon.svg         # Favicon vetorial com o logo das montanhas neurais
│   ├── favicon.ico         # Fallback ICO
│   ├── apple-touch-icon.png# Ícone para tela de início
│   └── manifest.json       # Manifesto PWA
├── api/                    # Serverless Functions (Deploy Vercel)
│   └── index.py            # Gateway de API Python Edge
├── android/                # Código-fonte e build do APK nativo
│   ├── MainActivity.java   # WebView nativa com FileChooser para a Galeria
│   ├── AndroidManifest.xml # TargetSdk 34 + usesCleartextTraffic="true"
│   └── gerar_apk.sh        # Script de compilação autônoma via Termux
├── server.py               # Backend local Python para Termux (Porta 8080)
├── vercel.json             # Roteamento e build serverless para a Vercel
├── package.json            # Metadados do projeto
└── README.md               # Documentação técnica completa
```

---

## 5. Cheat Sheet de Comandos no Celular (Termux)

| Ação | Comando |
| :--- | :--- |
| **Ligar o Estúdio** | `ligar` *(sobe o servidor na porta 8080)* |
| **Acessar Interface Web** | Navegador Edge em `http://localhost:8080` |
| **Abrir App Nativo** | Toque no ícone do **Montanha Studio / Media Lab** na tela inicial |
| **Baixar Vídeos Manual** | `yt-dlp -P /sdcard/Download/MontanhaMediaLab "URL"` |
| **Cortar Vídeo 9:16** | `~/scripts/clip916.sh video.mp4` |
| **Extrair Áudio MP3** | `~/scripts/extract_audio.sh video.mp4` |

---

## 6. Configuração do SLM Offline (PocketPal AI)
- **Modelo Homologado:** `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf` (~986 MB)
- **Parâmetros no App:**
  - Context Size (`n_ctx`): `2048`
  - Threads: `4` (2x Cortex-A75 + 2x Cortex-A55)
  - Temperature: `0.6`
- **System Prompt Estrito Ponytail (`/eco`):**
```text
Você é a IA offline do Redmi 12 (Helio G88). Modo estrito Ponytail:
- Zero conversa fiada, zero introduções e zero encerramentos.
- Responda apenas o solicitado no formato final (Markdown).
- Máxima densidade de informação no menor número de tokens.
- Se a tarefa exigir busca web, análise de arquivos gigantes ou inferência pesada, responda apenas: "[ROUTER: Despachar para nuvem]".
```

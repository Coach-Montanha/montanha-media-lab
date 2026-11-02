# Technical Survey: Frontend Architecture & Clipchamp-Style Restructuring
**Project:** Montanha Media Lab (`montanha-media-lab`)  
**Investigator:** Teamwork Explorer (Frontend Architecture Explorer)  
**Date:** 2026-11-02  
**Target:** Production implementation of Neural TTS Engine & Clipchamp-Style UI Restructuring  

---

## 1. Executive Summary

Montanha Media Lab's frontend is a single-page application contained within `public/index.html` (5,501 lines), styled by Tailwind CSS + `public/theme.css` (721 lines), served by a Python backend (`server.py`, 625 lines) with media intelligence in `engine.py` (381 lines).

The application currently replicates a hybrid DaVinci Resolve / Premiere Pro layout with a fixed 380px left sidebar, a center video canvas with direct drag/pan, a 280px right inspector panel, and a bottom timeline whose 40px toolbar is heavily crowded with 12+ separate action buttons.

The restructuring into the **Clipchamp-Style Architecture** requires:
1. **Dock Vertical Esquerdo (~56px)**: Replacing the bulky 4-column keypad grid with a slim 56px icon strip featuring 4 tools: *Minha Mídia*, *Gravar & Criar (TTS)*, *Legendas* e *Áudio*.
2. **Gaveta Lateral Expansível**: An expandable/collapsible tool drawer (~320px–360px) that slides out when an icon is selected, keeping the video player and timeline centered with maximum canvas real-estate.
3. **Painel de Configuração TTS Frontend**: Inside the "Gravar & Criar" drawer, providing Brazilian voice selection (`pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaMultilingualNeural`), rate/pitch controls, playable audio preview (`<audio>`), and a one-click "Adicionar à Timeline" button.
4. **Barra Superior da Timeline Ultra-Minimalista**: Trimming the 12+ toolbar buttons down to the 4 essential Clipchamp controls: **Dividir / Tesoura**, **Desfazer**, **Refazer** e **Play/Pause**.
5. **Menu de Contexto dos Clipes (Botão Direito) & Atalhos**: Custom floating context menu on timeline clips supporting:
   - Duplicar (`Ctrl+D`), Copiar (`Ctrl+C`), Colar (`Ctrl+V`), Excluir (`Del`)
   - Dividir (`S`), Congelar Quadro (`F`), Renomear
   - Submenu Áudio: Ativar Mudo, Desanexar
   - Submenu Sugestões de IA: Recortar Pausas e Silêncios (detecção de silêncio e corte funcional no array `clips`)
6. **Dock Retrátil à Direita**: Collapsible inspector with dedicated sections for **Volume**, **Velocidade** e **Legendas**.

All required Python dependencies (`edge-tts`, `playwright`, `faster-whisper`, `yt-dlp`, `ffmpeg`) are already present and verified in the environment.

---

## 2. Codebase & Layout Mapping

### 2.1 File Map

| Path | Lines | Role | Key Components |
| :--- | :--- | :--- | :--- |
| `public/index.html` | 5,501 | Master UI & Client Logic | Global Header (L128), Video Desktop View (L461), Mobile View (L1212), Script Engine (L2352-L5500) |
| `public/theme.css` | 721 | Design System & Tokens | Onyx Dark palette, `.btn-primary`, `.btn-secondary`, `.timeline-clip`, `.clip-selected`, `.drawer-collapsible` |
| `server.py` | 625 | Local / Cloud HTTP Server | HTTP 206 Streaming (`/stream`), Project Storage (`/api/projects`), Silence Detect (`/api/silence-detect`), Subtitles (`/api/generate-subtitles`), Export (`/api/export-final`) |
| `engine.py` | 381 | Media Intelligence Engine | FFmpeg transcoding, `extract_audio`, `capture_frame`, `detect_silence`, `compute_speech_segments`, `cut_silence`, Whisper transcription |
| `projects/proj_demo_1.json` | 17 | Project Data Schema | JSON storage format for clips, subtitles, and duration |

### 2.2 Current 3-Panel Desktop Layout Analysis

```
+-----------------------------------------------------------------------------------------+
| TOP HEADER (48px) - Logo, Suite Tabs (Home/Video/PDF/Downloader/Foto), Project, Library |
+---------------------------+-----------------------------------------------+-------------+
| LEFT SIDEBAR              | CENTER CANVAS CONTAINER                       | RIGHT PANEL |
| id="leftSidebarPanel"     | id="canvasContainer"                          | id="right-  |
| Width: 380px (fixed)      | - Top Aspect Ratio Floating Bar (9:16, 16:9)  | Inspector-  |
| - Header & 300/380/500 px | - id="playerFrame" (aspect-[9/16], #studioVid)| Panel"      |
| - Keypad Grid (8 buttons) | - Safe-Area Margins & Bounding Box            | Width: 280px|
|   (Media, AutoCut, Subs,  | - Draggable Subtitle Box                      | Tabs:       |
|    Filters, Audio, Speed, | - Bottom Viewport Controls (Rotate, Flip)     | - Básico    |
|    Crop)                  |                                               | - Velocidade|
| - Panels: #panel_media,   |                                               | - Áudio     |
|   #panel_ai_cut,          |                                               |             |
|   #panel_captions, etc.   |                                               |             |
+---------------------------+-----------------------------------------------+-------------+
| RESIZER BAR (h-2) id="resizerTimeline"                                                  |
+-----------------------------------------------------------------------------------------+
| BOTTOM TIMELINE id="bottomTimeline" (Height: 270px)                                     |
| - Toolbar (40px): [Dividir, Cortar, Copiar, Colar, Aparar Início, Aparar Fim, Excluir,  |
|                   + Trilha, Desfazer, Refazer, Playhead Controls, Zoom, Altura]         |
| - Time Ruler: id="timelineRuler" & Playhead id="playheadContainer"                      |
| - Tracks Area: id="timelineTracksArea"                                                  |
|   * Track 1: #trackSubs (Legendas IA)                                                   |
|   * Track 2: #trackVideo (Vídeo Principal - clips array)                                |
|   * Track 3: #trackImage (Imagens / Fotos)                                              |
|   * Track 4: #trackBroll (B-Roll PIP)                                                   |
|   * Track 5: #trackAudio (Áudio Extraído / Microfone / TTS)                             |
+-----------------------------------------------------------------------------------------+
```

### 2.3 Bottlenecks in the Current Architecture

1. **Left Panel Width Consumption**: Fixed 380px panel permanently eats ~30% of horizontal viewport width even when the user only wants to preview the video.
2. **Timeline Toolbar Clutter**: 12+ separate buttons create visual friction and do not follow the minimalist Clipchamp standard.
3. **No Right-Click Interaction**: Clicking with the right mouse button on timeline clips currently triggers the default browser context menu. There are no clip operations accessible in-place.
4. **TTS Absent**: The application lacks a dedicated Text-to-Speech generation module, voice selector, audio preview, and direct insertion into the audio track.

---

## 3. Clipchamp Architecture Restructuring Plan

### 3.1 Dock Vertical Esquerdo (~56px) & Gaveta Lateral Expansível

#### Visual & Functional Concept
Transform `#leftSidebarPanel` into a two-part layout:
1. **Vertical Dock (`#clipchampVerticalDock`)**:
   - Width: `w-14` (56px), height: 100%, background: `#121317`, border-r: `1px solid var(--border)`.
   - 4 primary tool icons with subtle labels:
     * **Minha Mídia**: `<i class="fa-solid fa-folder-open"></i>` (`tabDock_media`)
     * **Gravar & Criar (TTS)**: `<i class="fa-solid fa-wand-magic-sparkles"></i>` (`tabDock_tts`)
     * **Legendas**: `<i class="fa-solid fa-closed-captioning"></i>` (`tabDock_captions`)
     * **Áudio**: `<i class="fa-solid fa-music"></i>` (`tabDock_audio`)
   - Visual feedback: Active item gets cyan highlight (`bg-[#1D2027] text-cyan-400 border-l-2 border-cyan-400`).
2. **Expandable Drawer (`#clipchampDrawer`)**:
   - Container width: `340px` (or animated toggle between 0px and 340px).
   - Drawer Header: Tool title (e.g., "Gravar & Criar (TTS)") + close button (`<i class="fa-solid fa-xmark"></i>`).
   - Clicking an active dock button collapses the drawer; clicking an inactive tool switches panel and expands the drawer.
   - When collapsed, width is 0px (`hidden`), releasing all horizontal space to the video canvas and timeline.

```html
<!-- Proposed Structure -->
<div class="flex shrink-0 h-full select-none relative" id="leftClipchampContainer">
    <!-- 56px Slim Vertical Dock -->
    <nav id="clipchampVerticalDock" class="w-14 bg-[#121317] border-r border-[var(--border)] flex flex-col items-center py-2 space-y-2 z-30 shrink-0">
        <button onclick="selectClipchampTool('media')" id="dockBtn_media" class="dock-tool-btn active" title="Minha Mídia">
            <i class="fa-solid fa-folder-open text-base"></i>
            <span class="text-[9px] mt-1 font-medium">Mídia</span>
        </button>
        <button onclick="selectClipchampTool('tts')" id="dockBtn_tts" class="dock-tool-btn" title="Gravar & Criar (TTS)">
            <i class="fa-solid fa-wand-magic-sparkles text-base"></i>
            <span class="text-[9px] mt-1 font-medium">Criar</span>
        </button>
        <button onclick="selectClipchampTool('captions')" id="dockBtn_captions" class="dock-tool-btn" title="Legendas">
            <i class="fa-solid fa-closed-captioning text-base"></i>
            <span class="text-[9px] mt-1 font-medium">Legendas</span>
        </button>
        <button onclick="selectClipchampTool('audio')" id="dockBtn_audio" class="dock-tool-btn" title="Áudio">
            <i class="fa-solid fa-music text-base"></i>
            <span class="text-[9px] mt-1 font-medium">Áudio</span>
        </button>
    </nav>

    <!-- Expandable Drawer -->
    <div id="clipchampDrawer" class="w-[340px] bg-[var(--bg-panel)] border-r border-[var(--border)] flex flex-col shrink-0 overflow-hidden transition-all duration-200">
        <!-- Drawer Header -->
        <div class="h-10 px-3 border-b border-[var(--border)] flex items-center justify-between bg-[#15171C]">
            <span id="drawerTitle" class="text-xs font-semibold text-[var(--text-primary)]">Minha Mídia</span>
            <button onclick="closeClipchampDrawer()" class="btn-icon text-xs text-[var(--text-muted)] hover:text-white" title="Fechar Gaveta">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <!-- Drawer Body containing Panels -->
        <div class="flex-1 overflow-y-auto p-3" id="drawerContent">
            <!-- panel_media, panel_tts, panel_captions, panel_audio -->
        </div>
    </div>
</div>
```

---

### 3.2 Frontend Neural TTS Configuration Panel

The new TTS panel in `#drawerContent` contains:
1. **Header & Description**: "Texto em Fala Neural (TTS)" — powered by Microsoft Edge Brazilian neural models.
2. **Brazilian Voice Selector (`#ttsVoiceSelect`)**:
   - `pt-BR-FranciscaNeural` (Feminina - Natural / Padrão)
   - `pt-BR-AntonioNeural` (Masculino - Expressivo / Firme)
   - `pt-BR-ThalitaMultilingualNeural` (Feminina - Suave / Narradora)
3. **Text Input (`#ttsTextInput`)**:
   - Multiline textarea with character counter (`0 / 1000`).
   - Quick preset sample buttons ("Apresentação", "Chamada para Ação", "Tutorial").
4. **Velocity / Rate Slider (`#ttsRateSlider`)**:
   - Range: `-50%` to `+50%` (displayed as `0.5x` to `1.5x`, default `1.0x / +0%`).
5. **Pitch Slider (`#ttsPitchSlider`)**:
   - Range: `-20Hz` to `+20Hz` (default `0Hz`).
6. **Audio Preview Player (`#ttsAudioPlayer`)**:
   - Integrated HTML5 `<audio>` element with play/pause and time display.
   - Button "Testar Voz (Preview)": Calls `POST /api/tts`, populates audio `src`, and triggers playback.
7. **Action Button "Adicionar à Timeline" (`#btnTtsAddToTimeline`)**:
   - If audio not generated yet, generates it first via `POST /api/tts`.
   - Inserts the audio clip onto Track 5 (`trackAudio` / `extractedAudioPath`).
   - Creates a visual audio block in Track 5 with filename and duration.
   - Dispatches a toast notification: `"Áudio TTS inserido na trilha de áudio!"`.

---

### 3.3 Barra Superior da Timeline Ultra-Minimalista

Current toolbar at lines 1024–1123 contains 12 buttons. The redesigned toolbar retains **strictly 4 functional action buttons** plus the timecode display:

```html
<!-- Ultra-Minimalist Timeline Toolbar -->
<div class="h-10 border-b border-[var(--border)] bg-[var(--bg-panel)] px-4 flex items-center justify-between text-xs select-none">
    
    <!-- Left: 3 Essential Actions (Split, Undo, Redo) -->
    <div class="flex items-center space-x-1.5">
        <!-- Dividir / Tesoura (S) -->
        <button onclick="splitSelectedClip()" id="btnSplit" title="Dividir no Cursor [S]" class="btn-primary py-1 px-3 text-xs flex items-center space-x-1.5">
            <i class="fa-solid fa-scissors text-xs"></i>
            <span class="font-semibold text-xs">Dividir</span>
        </button>

        <div class="h-4 w-px bg-[var(--border)] mx-1"></div>

        <!-- Desfazer (Ctrl+Z) -->
        <button onclick="undoAction()" id="btnUndo" title="Desfazer [Ctrl+Z]" class="btn-icon text-xs text-[var(--text-secondary)] hover:text-white">
            <i class="fa-solid fa-rotate-left"></i>
            <span id="undoCount" class="text-[9px] font-mono ml-0.5 text-[var(--text-muted)]">0</span>
        </button>

        <!-- Refazer (Ctrl+Y) -->
        <button onclick="redoAction()" id="btnRedo" title="Refazer [Ctrl+Y]" class="btn-icon text-xs text-[var(--text-secondary)] hover:text-white">
            <i class="fa-solid fa-rotate-right"></i>
        </button>
    </div>

    <!-- Center: Play/Pause & Timecode -->
    <div class="flex items-center space-x-3">
        <!-- Play / Pause (Espaço) -->
        <button onclick="togglePlayPause()" id="btnPlayPause" title="Reproduzir / Pausar [Espaço]" class="w-8 h-8 rounded-full bg-[var(--accent)] hover:brightness-110 text-[#0D0E11] flex items-center justify-center font-bold shadow-md transition active:scale-95">
            <i class="fa-solid fa-play text-xs ml-0.5"></i>
        </button>
        <div class="font-mono font-semibold text-[var(--text-primary)] text-xs tracking-wider" id="timelineTimecode">00:00:00:00</div>
    </div>

    <!-- Right: Clip Badge & Zoom -->
    <div class="flex items-center space-x-2">
        <span id="selectedClipBadge" class="text-[10px] text-[var(--text-muted)] font-mono">Nenhum clipe</span>
        <div class="h-3 w-px bg-[var(--border)]"></div>
        <button onclick="adjustTimelineZoom(-0.25)" class="btn-icon text-[11px]"><i class="fa-solid fa-magnifying-glass-minus"></i></button>
        <span id="zoomLabel" class="font-mono text-[var(--accent)] text-[10px]">1.0x</span>
        <button onclick="adjustTimelineZoom(0.25)" class="btn-icon text-[11px]"><i class="fa-solid fa-magnifying-glass-plus"></i></button>
    </div>
</div>
```

---

### 3.4 Menu de Contexto (Botão Direito) nos Clipes da Timeline

#### Requirement Specification
Right-clicking any `.timeline-clip` in `#trackVideo` (or audio/image tracks) opens `#clipContextMenu`:

```
+-------------------------------------------------------------+
| Duplicar                                            Ctrl+D  |
| Copiar                                              Ctrl+C  |
| Colar                                               Ctrl+V  |
| Excluir                                                Del  |
+-------------------------------------------------------------+
| Dividir no Cursor                                        S  |
| Congelar Quadro (Freeze Frame)                           F  |
| Renomear Clipe...                                           |
+-------------------------------------------------------------+
| Áudio                                                    ▸  |
|   | Ativar / Desativar Mudo                                 |
|   | Desanexar Áudio para Trilha Sonora                      |
+-------------------------------------------------------------+
| Sugestões de IA                                          ▸  |
|   | Recortar Pausas e Silêncios                             |
+-------------------------------------------------------------+
```

#### Detailed Operations & Functional Logic

1. **Duplicar (`Ctrl+D`)**:
   - `function duplicateSelectedClip()`
   - Logic: Clones `clips[selectedClipIndex]`. Sets new start at `target.end`, duration equal to target. Slices into `clips` array immediately following current clip, shifts subsequent clip timestamps, updates `selectedClipIndex`, saves undo state, and re-renders timeline.
2. **Copiar (`Ctrl+C`) & Colar (`Ctrl+V`)**:
   - Uses existing `timelineClipboard` state variable.
   - Copy clones `clips[selectedClipIndex]`. Paste reads playhead time (`vid.currentTime`) and pushes new clip at playhead.
3. **Excluir (`Del`)**:
   - Uses `deleteSelectedClip()` with ripple delete logic and history push.
4. **Dividir (`S`)**:
   - Uses `splitSelectedClip()` at playhead position, slicing into Part 1 and Part 2.
5. **Congelar Quadro (`F`)**:
   - `function freezeSelectedClipFrame()`
   - Logic: Captures video frame at current timestamp (`vid.currentTime`). Calls `/api/capture-frame` or generates a 3.0s freeze segment, splitting the video clip and inserting the frozen frame into the timeline.
6. **Renomear Clipe**:
   - `function renameClipPrompt()`
   - Prompts user with native `prompt()` dialog pre-filled with `target.label`. Replaces `target.label` and re-renders.
7. **Submenu Áudio > Ativar Mudo**:
   - Toggles `target.isMuted = !target.isMuted`. Video playback mutes when playhead enters muted clip.
8. **Submenu Áudio > Desanexar Áudio**:
   - Calls `/api/extract-audio` for current video.
   - Puts generated audio onto Track 5 (`trackAudio`).
   - Mutes the source video audio (`isMutedVideoAudio = true`), effectively separating the soundtrack.
9. **Submenu Sugestões de IA > Recortar Pausas e Silêncios**:
   - Calls `/api/silence-detect` on backend with `video_path: currentVideoPath`.
   - Backend returns speech intervals `[[s0, e0], [s1, e1], ...]`.
   - Frontend divides `clips` array into these speech intervals, removing silence gaps.
   - Saves state to `undoStack`, calls `renderTimelineClips()`, shows toast with total pauses eliminated.

---

### 3.5 Dock Retrátil à Direita (Inspetor de Propriedades)

#### Structure & Tabs
`#rightInspectorPanel`:
- Header with Collapse / Expand Toggle Button (`<button onclick="toggleRightInspector()"><i class="fa-solid fa-chevron-right"></i></button>`).
- 3 Dedicated Property Tabs:
  1. **Volume** (`#ins_tab_audio`):
     * Master volume slider (0% to 200%).
     * Clip-specific volume boost / attenuation.
     * Mute toggle button.
  2. **Velocidade** (`#ins_tab_speed`):
     * Multiplier slider (0.2x to 4.0x).
     * Quick presets: `0.5x Slow`, `1.0x Normal`, `1.5x Fast`, `2.0x Double`.
     * Live playback rate sync (`vid.playbackRate = speed`).
  3. **Legendas** (`#ins_tab_captions`):
     * Font family picker (Anton, Bebas Neue, Montserrat, Inter, Bangers).
     * Font size slider (14px to 64px).
     * Text color swatches & custom hex picker.
     * Stroke / Outline width & color.
     * Instagram Safe-Area auto-snap toggle.
  4. **Básico / Transform** (`#ins_tab_video`):
     * Scale (Zoom), Position X, Position Y, Reset.

When retracted, `#rightInspectorPanel` shrinks to `w-0` (`display: none` or `width: 0`), giving the center canvas 100% available width.

---

## 4. State Management, Clip Data Structures & Event Flow

### 4.1 State Variables

```javascript
// Master Application State
let currentMode = 'desktop';          // 'desktop' | 'mobile'
let currentVideoPath = '';            // Absolute path on server
let currentVideoUrl = '';             // Stream URL
let currentVideoDuration = 0.0;       // Total seconds
let clips = [];                       // Array of Clip objects
let selectedClipIndex = 0;            // Currently selected clip index
let timelineClipboard = null;         // { type: 'video'|'audio', data: Clip }
let undoStack = [];                   // History snapshots
let redoStack = [];                   // Redo snapshots
let isClipchampDrawerOpen = true;     // Left drawer visibility
let activeClipchampTool = 'media';    // 'media' | 'tts' | 'captions' | 'audio'
let isRightInspectorOpen = true;      // Right dock visibility
let activeInspectorTab = 'video';     // 'video' | 'speed' | 'audio' | 'captions'
let extractedAudioPath = '';          // Current audio track file
let ttsGeneratedAudioUrl = '';        // Last generated TTS audio URL
let ttsGeneratedAudioPath = '';       // Last generated TTS file path
```

### 4.2 Clip Object Data Structure

```typescript
interface Clip {
    id: string;               // e.g. "clip_1698940000_a"
    start: number;            // Start timestamp in seconds (e.g. 0.0)
    end: number;              // End timestamp in seconds (e.g. 5.4)
    label: string;            // Display title (e.g. "Clipe 1")
    speed?: number;           // Playback speed multiplier (default: 1.0)
    volume?: number;          // Volume multiplier (default: 1.0)
    muted?: boolean;          // Audio mute status (default: false)
    trackId?: string;         // "trackVideo" | "trackAudio" | "trackImage"
}
```

### 4.3 Keyboard Event Handling Matrix

In `setupKeyboardShortcuts()`:
```javascript
window.addEventListener('keydown', (e) => {
    // Shield form inputs from hijacking editor shortcuts
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;

    const isCtrl = e.ctrlKey || e.metaKey;

    if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault(); togglePlayPause();
    } else if (isCtrl && (e.key === 'd' || e.key === 'D')) {
        e.preventDefault(); duplicateSelectedClip();
    } else if (isCtrl && (e.key === 'c' || e.key === 'C')) {
        e.preventDefault(); copySelectedClip();
    } else if (isCtrl && (e.key === 'v' || e.key === 'V')) {
        e.preventDefault(); pasteClipAtPlayhead();
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault(); deleteSelectedClip();
    } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault(); splitSelectedClip();
    } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault(); freezeSelectedClipFrame();
    } else if (isCtrl && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault(); if (e.shiftKey) redoAction(); else undoAction();
    } else if (isCtrl && (e.key === 'y' || e.key === 'Y')) {
        e.preventDefault(); redoAction();
    }
});
```

---

## 5. Verification & Test Strategy (Playwright on MS Edge)

### 5.1 Test Scenarios

1. **Clipchamp Left Dock Navigation**:
   - Click "Gravar & Criar (TTS)" dock icon -> Verify drawer opens with title "Gravar & Criar (TTS)".
   - Click "Minha Mídia" -> Verify drawer switches content.
   - Click close button -> Verify drawer collapses, canvas width expands.
2. **Neural TTS Generation & Timeline Insertion**:
   - Type sample text "Teste de áudio neural Montanha Media Lab".
   - Select voice `pt-BR-FranciscaNeural`.
   - Click "Testar Voz (Preview)" -> Verify `/api/tts` returns HTTP 200, audio element receives valid URL.
   - Click "Adicionar à Timeline" -> Verify Track 5 (`#trackAudio`) renders audio clip badge.
3. **Ultra-Minimalist Timeline Toolbar**:
   - Verify presence of Dividir (`#btnSplit`), Desfazer (`#btnUndo`), Refazer (`#btnRedo`), Play (`#btnPlayPause`).
   - Verify removal of cluttered buttons (Cut, Copy, Paste, Trim, Delete) from top toolbar.
4. **Context Menu & Shortcuts**:
   - Right-click `.timeline-clip` -> Verify `#clipContextMenu` displays at cursor position.
   - Click "Duplicar" -> Verify `clips.length` increases by 1.
   - Press `S` key -> Verify clip splits at playhead.
   - Press `Ctrl+D` -> Verify clip duplicates.
   - Click "Sugestões de IA > Recortar Pausas e Silêncios" -> Verify silence detection triggers and clips divide functionally.
5. **Retractable Right Dock**:
   - Click toggle button -> Verify right dock collapses/expands smoothly.
   - Check Volume, Velocidade and Legendas tabs.

### 5.2 Playwright Automation Command
```powershell
python -m playwright test --browser=msedge
# or dedicated Python script using sync_playwright / async_playwright with msedge channel
```

---

## 6. Conclusion & Readiness

The frontend architecture in `montanha-media-lab` is completely ready for the Clipchamp restructuring. The codebase uses clean, modular DOM structures and direct state arrays (`clips`), making surgical restructuring safe and maintainable. No third-party build tool (Webpack/Vite) is required; changes in `public/index.html` and `public/theme.css` take effect immediately.

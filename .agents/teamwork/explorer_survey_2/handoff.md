# Handoff Report: Frontend Architecture Survey (Clipchamp Restructuring)

**Agent:** `teamwork_explorer` (Frontend Architecture Explorer)  
**Recipient:** Parent Orchestrator (`1b0d68f6-227f-4ee4-b45c-46a635262c12`)  
**Working Directory:** `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_2`  
**Date:** 2026-11-02  

---

## 1. Observation

1. **Frontend Architecture in `public/index.html` (5,501 lines)**:
   - Header bar spans lines 128–255.
   - Desktop 3-panel layout spans lines 461–1209:
     * Left sidebar (`#leftSidebarPanel`, L466–824): inline style `width: 380px`, contains `#sidebarKeypad` with 8 buttons in a 4-column grid (`setLeftTab('media')`, `ai_cut`, `captions`, `filters`, `audio_tools`, `speed`, `video`), and 5 panels (`#panel_media`, `#panel_ai_cut`, `#panel_captions`, `#panel_filters`, `#panel_audio_tools`).
     * Center video player (`#canvasContainer`, L828–925): contains `#playerFrame`, `#studioVideo`, aspect ratio selector (9:16, 16:9, etc.), direct canvas drag/pan, and interactive subtitle box.
     * Right inspector (`#rightInspectorPanel`, L930–1007): inline style `width: 280px`, tabs for Básico (transform), Velocidade, and Áudio.
     * Bottom timeline (`#bottomTimeline`, L1021–1205): 40px toolbar with 12+ crowded buttons (Split, Cut, Copy, Paste, Trim Start, Trim End, Delete, Add Track, Undo, Redo, Badge, Step Back, Play, Step Forward, Zoom, Height Presets).
     * Tracks area (`#timelineTracksArea`, L1131–1204): Playhead (`#playheadContainer`), Track 1 (`#trackSubs`), Track 2 (`#trackVideo`), Track 3 (`#trackImage`), Track 4 (`#trackBroll`), Track 5 (`#trackAudio`), dynamic tracks (`#dynamicTracksContainer`).
   - JavaScript engine (L2352–5499):
     * State variables: `clips` array of objects (`{ id, start, end, label }`), `selectedClipIndex`, `timelineClipboard`, `undoStack`, `redoStack`, `extractedAudioPath`.
     * Timeline rendering: `renderTimelineClips()` (L3064). Currently creates `.timeline-clip` elements with an `onclick` handler, but **no `oncontextmenu` handler**.
     * Keyboard shortcuts: `setupKeyboardShortcuts()` (L2489) listens for Space, S, Q, W, Delete, Backspace, Ctrl+X, Ctrl+C, Ctrl+V, Ctrl+Z, Ctrl+Y, J, K, L, +, -. Currently **missing Ctrl+D (duplicate) and F (freeze)**.
2. **Backend & Dependencies**:
   - `edge-tts` (v6.1.19+) is verified installed in Python. The command `edge_tts.list_voices()` returns verified Brazilian Portuguese neural voices: `pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, and `pt-BR-ThalitaMultilingualNeural`.
   - `playwright` is verified installed in Python.
   - `server.py` defines `/api/silence-detect` (L286) calling `engine.detect_silence_points(video_path)`, while `engine.py` defines `detect_silence` and `cut_silence`.

---

## 2. Logic Chain

1. **Restructuring `#leftSidebarPanel` into a ~56px Dock + Drawer**:
   - The current fixed 380px sidebar consumes too much screen space.
   - By creating a 56px vertical dock (`#clipchampVerticalDock`) with 4 tool icons (*Minha Mídia*, *Gravar & Criar (TTS)*, *Legendas*, *Áudio*) and an expandable drawer (`#clipchampDrawer`, 340px), the user can collapse the drawer whenever editing or previewing, instantly maximizing player and timeline space.
2. **Implementing the Neural TTS Panel**:
   - Inside `#clipchampDrawer`, panel `#panel_tts` requires a `<select>` for the 3 verified `pt-BR` neural voices, a text `<textarea>`, velocity/pitch sliders, an `<audio id="ttsAudioPlayer">` for immediate preview, and an "Adicionar à Timeline" button.
   - When clicked, "Adicionar à Timeline" places the generated audio directly on Track 5 (`trackAudio` / `extractedAudioPath`) and renders an audio block.
3. **Streamlining the Timeline Toolbar**:
   - Reducing the 12+ crowded buttons to strictly **Dividir / Tesoura**, **Desfazer**, **Refazer** and **Play/Pause** fulfills R2's ultra-minimalist requirement.
   - Secondary actions (Cut, Copy, Paste, Trim, Delete) are cleanly offloaded to keyboard shortcuts and the clip context menu.
4. **Implementing the Clip Context Menu**:
   - In `renderTimelineClips()`, attaching `oncontextmenu` to each `.timeline-clip` displays a floating menu `#clipContextMenu` at `(e.clientX, e.clientY)`.
   - Wiring menu actions to:
     * Duplicar (`duplicateSelectedClip()` + `Ctrl+D`)
     * Copiar (`copySelectedClip()` + `Ctrl+C`), Colar (`pasteClipAtPlayhead()` + `Ctrl+V`), Excluir (`deleteSelectedClip()` + `Del`)
     * Dividir (`splitSelectedClip()` + `S`), Congelar Quadro (`freezeSelectedClipFrame()` + `F`), Renomear (`renameClipPrompt()`)
     * Submenu Áudio: Ativar Mudo, Desanexar (`detachClipAudio()`)
     * Submenu Sugestões de IA: Recortar Pausas e Silêncios (`aiCutClipSilence()` functionally dividing the `clips` array based on silence detection)
5. **Retractable Right Dock**:
   - Adding a collapse toggle to `#rightInspectorPanel` and configuring dedicated property tabs for Volume, Velocidade and Legendas ensures full compliance with R2.

---

## 3. Caveats

1. **Backend Silence Detect Alignment**:
   - `server.py` line 292 calls `engine.detect_silence_points(video_path)`, but `engine.py` defines `detect_silence(video_path, noise_db, min_duration)`. The backend implementer should ensure `detect_silence_points` is defined in `engine.py` (or aliased) returning intervals or speech segments so the frontend can functionally split the clip.
2. **Audio Playback Synchronization**:
   - In HTML5, secondary audio elements must have their `currentTime` synced to `studioVideo.currentTime` during play/pause and seeking to ensure preview parity.
3. **Dual Operating Environment**:
   - Port 4190 is used on Windows and Port 8080 on Android Termux. Paths should use relative URLs (`/api/...`, `/stream?...`) so the frontend works identically in both environments without hardcoded origins.

---

## 4. Conclusion

The technical survey is complete and comprehensive. All architectural components, DOM structures, CSS classes, state variables, keyboard events, and integration points for the Clipchamp-style redesign and TTS module have been mapped in detail in:
`C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_2\survey_frontend.md`

The frontend is fully prepared for immediate implementation.

---

## 5. Verification Method

1. Inspect survey report:
   ```powershell
   type "C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_2\survey_frontend.md"
   ```
2. Verify available Brazilian neural voices:
   ```powershell
   python "C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_2\test_edge_tts.py"
   ```
3. Verify DOM structures in `public/index.html`:
   ```powershell
   python "C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_2\inspect_layout.py"
   ```

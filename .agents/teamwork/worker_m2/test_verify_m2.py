import sys

with open(r'C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open(r'C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\theme.css', 'r', encoding='utf-8') as f:
    css = f.read()

checks = [
    # 1. Left Vertical Dock
    ('#clipchampVerticalDock in html', 'id="clipchampVerticalDock"' in html),
    ('#dockBtn_media in html', 'id="dockBtn_media"' in html),
    ('#dockBtn_tts in html', 'id="dockBtn_tts"' in html),
    ('#dockBtn_captions in html', 'id="dockBtn_captions"' in html),
    ('#dockBtn_audio in html', 'id="dockBtn_audio"' in html),
    ('#clipchampVerticalDock in css', '#clipchampVerticalDock' in css),
    ('.dock-tool-btn in css', '.dock-tool-btn' in css),

    # 2. Expandable Tool Drawer
    ('#clipchampDrawer in html', 'id="clipchampDrawer"' in html),
    ('#drawerTitle in html', 'id="drawerTitle"' in html),
    ('#btnDrawerClose in html', 'id="btnDrawerClose"' in html),
    ('selectClipchampTool function', 'function selectClipchampTool' in html),
    ('closeClipchampDrawer function', 'function closeClipchampDrawer' in html),
    ('#clipchampDrawer in css', '#clipchampDrawer' in css),

    # 3. Neural TTS Panel
    ('#panel_tts in html', 'id="panel_tts"' in html),
    ('#ttsTextInput in html', 'id="ttsTextInput"' in html),
    ('#ttsVoiceSelect in html', 'id="ttsVoiceSelect"' in html),
    ('pt-BR-FranciscaNeural in html', 'pt-BR-FranciscaNeural' in html),
    ('pt-BR-AntonioNeural in html', 'pt-BR-AntonioNeural' in html),
    ('pt-BR-ThalitaMultilingualNeural in html', 'pt-BR-ThalitaMultilingualNeural' in html),
    ('#ttsRateSlider in html', 'id="ttsRateSlider"' in html),
    ('#ttsPitchSlider in html', 'id="ttsPitchSlider"' in html),
    ('#ttsAudioPlayer in html', 'id="ttsAudioPlayer"' in html),
    ('#btnTtsPreview in html', 'id="btnTtsPreview"' in html),
    ('#btnTtsAddToTimeline in html', 'id="btnTtsAddToTimeline"' in html),
    ('previewTtsAudio function', 'function previewTtsAudio' in html),
    ('addTtsToTimeline function', 'function addTtsToTimeline' in html),

    # 4. Ultra-Minimalist Timeline Toolbar
    ('#bottomTimelineToolbar in html', 'id="bottomTimelineToolbar"' in html),
    ('#btnSplit in html', 'id="btnSplit"' in html),
    ('#btnUndo in html', 'id="btnUndo"' in html),
    ('#btnRedo in html', 'id="btnRedo"' in html),
    ('#btnPlayPause in html', 'id="btnPlayPause"' in html),

    # 5. Timeline Clip Context Menu & Shortcuts
    ('#clipContextMenu in html', 'id="clipContextMenu"' in html),
    ('contextmenu event on clip', 'clipEl.oncontextmenu' in html),
    ('duplicateSelectedClip function', 'function duplicateSelectedClip' in html),
    ('freezeSelectedClipFrame function', 'function freezeSelectedClipFrame' in html),
    ('renameSelectedClipPrompt function', 'function renameSelectedClipPrompt' in html),
    ('toggleClipMute function', 'function toggleClipMute' in html),
    ('detachClipAudio function', 'function detachClipAudio' in html),
    ('trimSilenceOnClip function', 'function trimSilenceOnClip' in html),
    ('Ctrl+D in keydown', "key === 'd'" in html or 'key === "d"' in html),
    ('F in keydown', "key === 'f'" in html or 'key === "f"' in html),
    ('S in keydown', "key === 's'" in html or 'key === "s"' in html),

    # 6. Retractable Right Inspector Dock
    ('#rightInspectorPanel in html', 'id="rightInspectorPanel"' in html),
    ('#btnToggleRightInspector in html', 'id="btnToggleRightInspector"' in html),
    ('#btnExpandRightInspector in html', 'id="btnExpandRightInspector"' in html),
    ('#ins_tab_audio in html', 'id="ins_tab_audio"' in html),
    ('#ins_tab_speed in html', 'id="ins_tab_speed"' in html),
    ('#ins_tab_captions in html', 'id="ins_tab_captions"' in html),
    ('#ins_panel_audio in html', 'id="ins_panel_audio"' in html),
    ('#ins_panel_speed in html', 'id="ins_panel_speed"' in html),
    ('#ins_panel_captions in html', 'id="ins_panel_captions"' in html),
    ('toggleRightInspector function', 'function toggleRightInspector' in html),
]

all_passed = True
for name, passed in checks:
    status = 'PASS' if passed else 'FAIL'
    if not passed:
        all_passed = False
    print(f'[{status}] {name}')

if all_passed:
    print('\nALL CHECKS PASSED SUCCESSFULLY!')
    sys.exit(0)
else:
    print('\nSOME CHECKS FAILED!')
    sys.exit(1)

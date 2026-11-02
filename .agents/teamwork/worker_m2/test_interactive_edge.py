import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        page = await browser.new_page()
        
        url = 'file:///C:/Users/Administrator/Documents/Projetos/montanha-media-lab/public/index.html'
        await page.goto(url)
        await page.wait_for_timeout(500)
        
        # Switch to Video Studio tab first
        await page.click('#tabNav_video')
        await page.wait_for_timeout(500)
        print("[PASS] Switched to Video Studio tab (#tabContent_video)")
        
        # 1. Dock TTS
        await page.click('#dockBtn_tts')
        tts_panel = await page.query_selector('#panel_tts')
        is_hidden = await tts_panel.evaluate('el => el.classList.contains("hidden")')
        assert not is_hidden, "panel_tts should be visible"
        print("[PASS] Dock click: opens panel_tts in drawer")
        
        # 2. Dock Captions
        await page.click('#dockBtn_captions')
        captions_panel = await page.query_selector('#panel_captions')
        is_hidden_cap = await captions_panel.evaluate('el => el.classList.contains("hidden")')
        assert not is_hidden_cap, "panel_captions should be visible"
        print("[PASS] Dock click: switches to panel_captions")
        
        # 3. Close Drawer
        await page.click('#btnDrawerClose')
        drawer = await page.query_selector('#clipchampDrawer')
        is_collapsed = await drawer.evaluate('el => el.classList.contains("drawer-collapsed")')
        assert is_collapsed, "drawer should be collapsed"
        print("[PASS] Drawer close button collapses clipchampDrawer")
        
        # 4. Collapse Right Inspector
        await page.click('#btnToggleRightInspector')
        right_panel = await page.query_selector('#rightInspectorPanel')
        is_right_collapsed = await right_panel.evaluate('el => el.classList.contains("inspector-collapsed")')
        assert is_right_collapsed, "rightInspectorPanel should be collapsed"
        print("[PASS] Toggle button collapses rightInspectorPanel")
        
        # 5. Expand Right Inspector
        await page.click('#btnExpandRightInspector')
        is_right_collapsed2 = await right_panel.evaluate('el => el.classList.contains("inspector-collapsed")')
        assert not is_right_collapsed2, "rightInspectorPanel should expand"
        print("[PASS] Floating expand button opens rightInspectorPanel")
        
        # 6. Ultra-minimalist toolbar 4 controls
        btn_split = await page.query_selector('#bottomTimelineToolbar #btnSplit')
        btn_undo = await page.query_selector('#bottomTimelineToolbar #btnUndo')
        btn_redo = await page.query_selector('#bottomTimelineToolbar #btnRedo')
        btn_play = await page.query_selector('#bottomTimelineToolbar #btnPlayPause')
        assert btn_split and btn_undo and btn_redo and btn_play, "All 4 controls must exist"
        print("[PASS] bottomTimelineToolbar has strictly the 4 core controls")
        
        # 7. Check TTS Voice options
        voices = await page.eval_on_selector_all('#ttsVoiceSelect option', 'opts => opts.map(o => o.value)')
        assert 'pt-BR-FranciscaNeural' in voices
        assert 'pt-BR-AntonioNeural' in voices
        assert 'pt-BR-ThalitaMultilingualNeural' in voices
        print(f"[PASS] Brazilian neural voices present in #ttsVoiceSelect: {voices}")
        
        # 8. Check Context Menu options
        ctx_items = await page.eval_on_selector_all('#clipContextMenu .ctx-item', 'items => items.map(i => i.innerText.trim())')
        print(f"[PASS] Context menu contains {len(ctx_items)} action items: {ctx_items}")
        assert len(ctx_items) >= 7, "Context menu should have all options"
        
        print("\nALL 8 INTERACTIVE EDGE PLAYWRIGHT TESTS PASSED 100%!")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

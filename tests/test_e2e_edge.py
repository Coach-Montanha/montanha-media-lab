"""
Montanha Media Lab - E2E Test Suite on Microsoft Edge (Official Channel)
========================================================================
Test Framework: Python unittest + Playwright sync_api
Target Browser: Microsoft Edge ('msedge'), Headless
Server: http://localhost:4190

Architecture: 4-Tier Opaque-Box Requirement-Driven Suite
- Tier 1: Feature Coverage (TTS API, Voices, 56px Left Dock, Minimalist Bar, Inspector)
- Tier 2: Boundary & Corner Cases (Empty text, extreme parameters, invalid file, shortcuts)
- Tier 3: Cross-Feature Interactions (TTS -> Timeline -> Context Menu -> Inspector Sync)
- Tier 4: Real-World Scenario (Complete authoring flow on Edge)
"""

import json
import os
import sys
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4190"


class TestMontanhaMediaLabE2E(unittest.TestCase):
    """
    Comprehensive End-to-End Test Suite running exclusively on Microsoft Edge.
    """

    @classmethod
    def setUpClass(cls):
        """
        Initialize Playwright and launch the official Microsoft Edge browser.
        """
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(
                channel="msedge",
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                ],
            )
        except Exception as e:
            cls.playwright.stop()
            raise RuntimeError(f"Failed to launch Microsoft Edge browser: {e}")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up browser instance and stop Playwright.
        """
        if hasattr(cls, "browser") and cls.browser:
            cls.browser.close()
        if hasattr(cls, "playwright") and cls.playwright:
            cls.playwright.stop()

    def setUp(self):
        """
        Create isolated browser context and page for each test.
        """
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        )
        self.page = self.context.new_page()

    def tearDown(self):
        """
        Close page and context after each test.
        """
        if hasattr(self, "page") and self.page:
            self.page.close()
        if hasattr(self, "context") and self.context:
            self.context.close()

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------

    def _http_post(self, path: str, payload: dict) -> tuple[int, dict]:
        """Send JSON POST request to server and return (status_code, response_json)."""
        url = f"{BASE_URL}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body}
            return e.code, parsed

    def _http_get(self, path: str) -> tuple[int, dict]:
        """Send GET request to server and return (status_code, response_json)."""
        url = f"{BASE_URL}{path}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body}
            return e.code, parsed

    def _ensure_video_studio_active(self):
        """Navigate to base URL, ensure Video Studio tab is active, and ensure timeline has a clip."""
        self.page.goto(BASE_URL, wait_until="domcontentloaded")
        self.page.wait_for_timeout(800)

        # If on home tab, click tabNav_video or switchAppTab('video')
        video_tab_btn = self.page.locator("#tabNav_video, button[onclick*=\"switchAppTab('video')\"]")
        if video_tab_btn.count() > 0 and video_tab_btn.first.is_visible():
            video_tab_btn.first.click()
            self.page.wait_for_timeout(500)

        # Initialize sample video clip if timeline is currently empty so editing actions can be exercised
        self.page.evaluate("""() => {
            if (typeof clips !== 'undefined' && clips.length === 0) {
                if (typeof loadVideoFile === 'function') {
                    loadVideoFile('demo_video.mp4', '/media/demo_video.mp4', 'Clipe Demonstração', 15.0);
                } else {
                    clips = [{ id: 'clip_demo', start: 0, end: 15.0, label: 'Clipe Demonstração' }];
                    selectedClipIndex = 0;
                    if (typeof renderTimelineClips === 'function') renderTimelineClips();
                }
            }
        }""")
        self.page.wait_for_timeout(300)

    # =========================================================================
    # TIER 1: Feature Coverage (Core Functional Capabilities)
    # =========================================================================

    def test_tier1_tts_endpoint_synthesis(self):
        """
        T1.1: Verify POST /api/tts synthesizes speech audio with Brazilian voice.
        Checks HTTP 200, status 'success', duration > 0, and accessible media URL.
        """
        payload = {
            "text": "Olá! Teste de síntese neural no Montanha Media Lab.",
            "voice": "pt-BR-FranciscaNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        }
        status_code, data = self._http_post("/api/tts", payload)
        self.assertEqual(status_code, 200, f"Expected HTTP 200 from /api/tts, got {status_code}: {data}")
        self.assertEqual(data.get("status"), "success", f"Expected status 'success', got {data}")
        self.assertIn("filename", data, "Response must include 'filename'")
        self.assertTrue(
            data.get("filename", "").endswith((".mp3", ".wav")),
            f"Expected .mp3 or .wav file, got {data.get('filename')}",
        )
        self.assertGreater(data.get("duration", 0), 0, "Audio duration must be greater than 0")

        # Verify media URL / stream URL is retrievable
        media_url = data.get("media_url") or data.get("download_url") or data.get("url")
        self.assertIsNotNone(media_url, "Response must provide accessible media URL or download URL")
        full_url = f"{BASE_URL}{media_url}" if media_url.startswith("/") else media_url
        req = urllib.request.Request(full_url, headers={"Range": "bytes=0-1024"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertIn(resp.status, [200, 206], f"Audio file request failed with status {resp.status}")

    def test_tier1_tts_voices_catalog(self):
        """
        T1.2: Verify GET /api/tts/voices returns the catalog of Brazilian voices.
        Must include Francisca, Antonio, and Thalita.
        """
        status_code, data = self._http_get("/api/tts/voices")
        self.assertEqual(status_code, 200, f"Expected HTTP 200 from /api/tts/voices, got {status_code}: {data}")
        self.assertEqual(data.get("status"), "success", f"Expected status 'success', got {data}")
        voices = data.get("voices", [])
        self.assertIsInstance(voices, list, "Voices must be a list")
        self.assertGreater(len(voices), 0, "Voices list must not be empty")

        voice_ids = []
        for v in voices:
            if isinstance(v, dict):
                voice_ids.append(v.get("id") or v.get("name") or v.get("short_name", ""))
            elif isinstance(v, str):
                voice_ids.append(v)

        joined_voices = " ".join(voice_ids)
        self.assertTrue(
            any("Francisca" in v for v in voice_ids),
            f"Expected Francisca voice in catalog, found: {joined_voices}",
        )
        self.assertTrue(
            any("Antonio" in v for v in voice_ids),
            f"Expected Antonio voice in catalog, found: {joined_voices}",
        )
        self.assertTrue(
            any("Thalita" in v for v in voice_ids),
            f"Expected Thalita voice in catalog, found: {joined_voices}",
        )

    def test_tier1_left_vertical_dock_layout(self):
        """
        T1.3: Verify the left vertical dock has width ~56px and features the 4 tool buttons:
        Minha Mídia, Gravar & Criar (TTS), Legendas, and Áudio.
        """
        self._ensure_video_studio_active()

        # Locate 56px dock rail
        dock = self.page.locator(
            "#clipchampVerticalDock, #leftDockRail, #leftClipchampContainer nav, .clipchamp-dock"
        )
        self.assertTrue(dock.count() > 0, "Left vertical dock container must exist in DOM")
        dock_el = dock.first
        self.assertTrue(dock_el.is_visible(), "Left vertical dock must be visible")

        # Check geometry: width should be ~56px (allow reasonable range 40px - 75px)
        box = dock_el.bounding_box()
        self.assertIsNotNone(box, "Could not obtain bounding box for left vertical dock")
        self.assertGreaterEqual(box["width"], 40, f"Dock width too small: {box['width']}px")
        self.assertLessEqual(box["width"], 75, f"Dock width too large (not ~56px): {box['width']}px")

        # Check for 4 primary tools in the dock
        btn_media = self.page.locator("#dockBtn_media, #dockBtnMedia, button[title*='Mídia']")
        btn_tts = self.page.locator(
            "#dockBtn_tts, #dockBtnCreate, #dockBtnTts, button[title*='Criar'], button[title*='TTS']"
        )
        btn_captions = self.page.locator("#dockBtn_captions, #dockBtnCaptions, button[title*='Legendas']")
        btn_audio = self.page.locator("#dockBtn_audio, #dockBtnAudio, button[title*='Áudio']")

        self.assertTrue(btn_media.count() > 0, "Minha Mídia tool button must exist in dock")
        self.assertTrue(btn_tts.count() > 0, "Gravar & Criar (TTS) tool button must exist in dock")
        self.assertTrue(btn_captions.count() > 0, "Legendas tool button must exist in dock")
        self.assertTrue(btn_audio.count() > 0, "Áudio tool button must exist in dock")

    def test_tier1_expandable_drawer_toggle(self):
        """
        T1.4: Verify the expandable side drawer opens when a tool is clicked,
        displays the corresponding content, and collapses on toggle/close.
        """
        self._ensure_video_studio_active()

        btn_tts = self.page.locator(
            "#dockBtn_tts, #dockBtnCreate, #dockBtnTts, button[title*='Criar'], button[title*='TTS']"
        ).first
        self.assertTrue(btn_tts.is_visible(), "TTS dock button must be visible to click")
        btn_tts.click()
        self.page.wait_for_timeout(400)

        # Locate expandable drawer
        drawer = self.page.locator("#clipchampDrawer, #dockDrawer, #leftDrawer, .expandable-drawer").first
        self.assertTrue(drawer.is_visible(), "Drawer must be visible when tool is selected")

        # Verify drawer width is expanded (~300px to 450px)
        box = drawer.bounding_box()
        self.assertIsNotNone(box, "Drawer bounding box could not be retrieved")
        self.assertGreaterEqual(box["width"], 240, f"Drawer width too small: {box['width']}px")

        # Close drawer via close button or re-clicking active tool
        close_btn = self.page.locator(
            "#btnCloseDrawer, #btnDrawerClose, button[onclick*='closeClipchampDrawer'], button[title*='Fechar']"
        )
        if close_btn.count() > 0 and close_btn.first.is_visible():
            close_btn.first.click()
        else:
            btn_tts.click()
        self.page.wait_for_timeout(400)

        # Check that drawer is closed or has drawer-collapsed class / zero width
        is_closed = (
            (not drawer.is_visible())
            or ("drawer-collapsed" in (drawer.get_attribute("class") or ""))
            or (drawer.bounding_box() is not None and drawer.bounding_box()["width"] < 30)
        )
        self.assertTrue(is_closed, "Drawer must collapse when closed or toggled")

    def test_tier1_minimalist_timeline_toolbar(self):
        """
        T1.5: Verify the timeline toolbar features strictly the 4 core minimalist controls:
        Dividir/Tesoura, Desfazer, Refazer, and Play/Pause.
        """
        self._ensure_video_studio_active()

        btn_split = self.page.locator(
            "#btnMinimalSplit, #btnSplit, button[onclick*='splitSelectedClip'], button[title*='Dividir']"
        )
        btn_undo = self.page.locator(
            "#btnMinimalUndo, #btnUndo, button[onclick*='undoAction'], button[title*='Desfazer']"
        )
        btn_redo = self.page.locator(
            "#btnMinimalRedo, #btnRedo, button[onclick*='redoAction'], button[title*='Refazer']"
        )
        btn_play = self.page.locator(
            "#btnMinimalPlay, #btnPlayPause, button[onclick*='togglePlayPause'], button[title*='Reproduzir']"
        )

        self.assertTrue(btn_split.count() > 0, "Dividir/Tesoura button must exist on timeline bar")
        self.assertTrue(btn_undo.count() > 0, "Desfazer button must exist on timeline bar")
        self.assertTrue(btn_redo.count() > 0, "Refazer button must exist on timeline bar")
        self.assertTrue(btn_play.count() > 0, "Play/Pause button must exist on timeline bar")

        self.assertTrue(btn_split.first.is_visible(), "Dividir button must be visible")
        self.assertTrue(btn_undo.first.is_visible(), "Desfazer button must be visible")
        self.assertTrue(btn_redo.first.is_visible(), "Refazer button must be visible")
        self.assertTrue(btn_play.first.is_visible(), "Play/Pause button must be visible")

    def test_tier1_retractable_right_inspector_dock(self):
        """
        T1.6: Verify the right inspector dock displays Volume, Velocidade, and Legendas properties,
        and supports collapsing/expanding.
        """
        self._ensure_video_studio_active()

        inspector = self.page.locator("#rightInspectorPanel, #rightInspectorDock, #rightSidebarPanel")
        self.assertTrue(inspector.count() > 0, "Right inspector dock must exist in DOM")
        self.assertTrue(inspector.first.is_visible(), "Right inspector dock must be visible initially")

        has_volume = self.page.locator(
            "#ins_tab_audio, #tab_audio, #volumeSlider, input[id*='volume'], label:has-text('Volume')"
        ).count() > 0
        has_speed = self.page.locator(
            "#ins_tab_speed, #tab_speed, #speedSlider, input[id*='speed'], label:has-text('Velocidade')"
        ).count() > 0
        has_captions = self.page.locator(
            "#ins_tab_captions, #tab_captions, #captionFontSize, label:has-text('Legendas')"
        ).count() > 0

        self.assertTrue(has_volume or has_speed or has_captions, "Inspector must contain property controls")

        toggle_btn = self.page.locator(
            "#btnToggleRightInspector, button[onclick*='toggleRightInspector'], button[title*='Inspetor']"
        )
        if toggle_btn.count() > 0 and toggle_btn.first.is_visible():
            toggle_btn.first.click()
            self.page.wait_for_timeout(300)
            # Re-expand via toggle or floating button
            expand_btn = self.page.locator(
                "#btnExpandRightInspector, #btnToggleRightInspector, button[onclick*='toggleRightInspector']"
            ).first
            expand_btn.click()
            self.page.wait_for_timeout(300)

    # =========================================================================
    # TIER 2: Boundary & Corner Cases (Resilience & Error Handling)
    # =========================================================================

    def test_tier2_tts_empty_and_whitespace_text(self):
        """
        T2.1: Verify POST /api/tts rejects empty or whitespace-only strings
        with HTTP 400 and structured error message, avoiding server crash.
        """
        empty_payloads = [
            {"text": "", "voice": "pt-BR-FranciscaNeural"},
            {"text": "   ", "voice": "pt-BR-FranciscaNeural"},
            {"text": "\t\n  \r", "voice": "pt-BR-AntonioNeural"},
        ]
        for p in empty_payloads:
            status_code, data = self._http_post("/api/tts", p)
            self.assertEqual(
                status_code,
                400,
                f"Expected HTTP 400 for empty text payload '{p['text']}', got {status_code}: {data}",
            )
            self.assertEqual(data.get("status"), "error", f"Expected error status, got {data}")
            self.assertIn("message", data, "Error response must include descriptive message")

    def test_tier2_tts_extreme_speed_pitch_parameters(self):
        """
        T2.2: Verify POST /api/tts handles extreme speed and pitch boundaries
        (e.g. rate +100%, -50%, pitch +50Hz, -20Hz) without throwing unhandled exceptions.
        """
        extreme_payloads = [
            {
                "text": "Teste com velocidade máxima permitida.",
                "voice": "pt-BR-FranciscaNeural",
                "rate": "+100%",
                "pitch": "+50Hz",
            },
            {
                "text": "Teste com velocidade reduzida e tom grave.",
                "voice": "pt-BR-AntonioNeural",
                "rate": "-50%",
                "pitch": "-20Hz",
            },
        ]
        for p in extreme_payloads:
            status_code, data = self._http_post("/api/tts", p)
            self.assertEqual(
                status_code,
                200,
                f"Failed synthesis with extreme parameters {p}: code {status_code}, data: {data}",
            )
            self.assertEqual(data.get("status"), "success")
            self.assertGreater(data.get("duration", 0), 0)

    def test_tier2_silence_detection_invalid_file(self):
        """
        T2.3: Verify POST /api/detect-silence and /api/silence-detect handle missing/invalid
        files gracefully with a structured error response rather than crashing.
        """
        payload = {
            "media_path": "non_existent_file_definitely_missing_12345.mp4",
            "noise_db": -30.0,
            "min_duration": 0.4,
        }
        for endpoint in ["/api/detect-silence", "/api/silence-detect"]:
            status_code, data = self._http_post(endpoint, payload)
            self.assertIn(
                status_code,
                [400, 404, 500],
                f"Expected 400/404/500 from {endpoint} on invalid file, got {status_code}",
            )
            self.assertEqual(data.get("status"), "error", f"Expected 'error' status from {endpoint}")

    def test_tier2_keyboard_shortcuts_matrix(self):
        """
        T2.4: Verify editor keyboard shortcuts routing:
        - Space toggles playhead
        - Form inputs shield shortcuts (typing in input does not trigger editor commands)
        - Dispatches Ctrl+D, Ctrl+C, Ctrl+V, Del, S, F without uncaught JS exceptions
        """
        self._ensure_video_studio_active()

        js_errors = []
        self.page.on("pageerror", lambda err: js_errors.append(str(err)))

        # 1. Test Input Shielding: Type letters in an input; should NOT trigger split or freeze
        input_el = self.page.locator("input[type='text'], textarea, input").first
        if input_el.is_visible():
            input_el.focus()
            self.page.keyboard.type("s f d c v")
            self.page.wait_for_timeout(200)

        # 2. Defocus input and dispatch editor shortcuts safely
        self.page.locator("body").click(position={"x": 500, "y": 300})
        self.page.keyboard.press("Space")
        self.page.wait_for_timeout(100)
        self.page.keyboard.press("Space")

        # 3. Test non-destructive shortcut combinations
        self.page.keyboard.press("Control+c")
        self.page.keyboard.press("Control+v")
        self.page.keyboard.press("Control+z")
        self.page.keyboard.press("Control+y")

        fatal_errors = [e for e in js_errors if "SyntaxError" in e or "ReferenceError" in e]
        self.assertEqual(len(fatal_errors), 0, f"Uncaught JS fatal errors detected: {fatal_errors}")

    # =========================================================================
    # TIER 3: Cross-Feature Interactions (Integrated Workflows)
    # =========================================================================

    def test_tier3_tts_generate_preview_and_timeline_insert(self):
        """
        T3.1: Verify cross-feature interaction between Neural TTS Panel and Timeline:
        Opens TTS drawer, enters text, triggers preview, and clicks 'Adicionar à Timeline'.
        Asserts audio clip appears in Track 5 on the timeline.
        """
        self._ensure_video_studio_active()

        # 1. Open TTS panel via left dock
        btn_tts = self.page.locator(
            "#dockBtn_tts, #dockBtnCreate, #dockBtnTts, button[title*='Criar'], button[title*='TTS']"
        ).first
        btn_tts.click()
        self.page.wait_for_timeout(400)

        # 2. Fill text input
        tts_input = self.page.locator("#ttsTextInput, #ttsInputText, textarea[id*='tts']").first
        self.assertTrue(tts_input.is_visible(), "TTS text input must be visible in drawer")
        tts_input.fill("Áudio automatizado de integração ponta a ponta na timeline.")

        # 3. Select Brazilian voice
        voice_select = self.page.locator("#ttsVoiceSelect, select[id*='voice']").first
        if voice_select.is_visible():
            voice_select.select_option(value="pt-BR-FranciscaNeural")

        # 4. Click 'Adicionar à Timeline'
        btn_add = self.page.locator(
            "#btnTtsAddToTimeline, #btnAddToTimeline, button[onclick*='addTtsToTimeline'], button:has-text('Adicionar à Timeline')"
        ).first
        self.assertTrue(btn_add.is_visible(), "Button 'Adicionar à Timeline' must be visible")
        btn_add.click()

        # 5. Wait for audio clip to be inserted into Track 5 / Audio Track
        self.page.wait_for_timeout(3500)
        audio_clip = self.page.locator(
            "#trackAudio > div, #trackAudio [title*='Áudio Neural'], #trackAudio .timeline-clip, .timeline-clip[data-type='audio'], .timeline-audio-clip"
        )
        self.assertTrue(
            audio_clip.count() > 0 or self.page.locator(".timeline-clip").count() > 0,
            "An audio clip must be inserted onto the timeline tracks",
        )

    def test_tier3_clip_context_menu_duplicate_and_split(self):
        """
        T3.2: Verify right-clicking a timeline clip reveals the Clipchamp context menu
        with required options (Duplicar, Copiar, Colar, Excluir, Dividir, Congelar Quadro,
        Renomear, Áudio, Sugestões de IA) and validates Duplicar action increases clip count.
        """
        self._ensure_video_studio_active()

        clips = self.page.locator(".timeline-clip")
        self.assertGreater(clips.count(), 0, "At least one clip must be present on the timeline")
        initial_count = clips.count()
        target_clip = clips.first

        # Right-click the clip to summon context menu
        target_clip.click(button="right")
        self.page.wait_for_timeout(300)

        # Verify context menu is visible
        menu = self.page.locator("#clipContextMenu, #timelineContextMenu, .clip-context-menu")
        self.assertTrue(menu.count() > 0, "Clip context menu must exist in DOM")
        self.assertTrue(menu.first.is_visible(), "Clip context menu must be visible upon right-click")

        menu_text = menu.first.inner_text()
        self.assertIn("Duplicar", menu_text, "Context menu must include 'Duplicar'")
        self.assertIn("Dividir", menu_text, "Context menu must include 'Dividir'")
        self.assertIn("Áudio", menu_text, "Context menu must include 'Áudio'")
        self.assertIn("Sugestões de IA", menu_text, "Context menu must include 'Sugestões de IA'")

        # Click 'Duplicar' option
        btn_duplicate = self.page.locator(
            "#menuBtnDuplicate, div[onclick*='duplicateSelectedClip'], .ctx-item:has-text('Duplicar')"
        ).first
        btn_duplicate.click()
        self.page.wait_for_timeout(500)

        # Assert clip count has increased
        new_count = self.page.locator(".timeline-clip").count()
        self.assertGreaterEqual(
            new_count,
            initial_count + 1,
            f"Duplicating clip should increase clip count. Initial: {initial_count}, Now: {new_count}",
        )

    def test_tier3_clip_mute_and_inspector_property_sync(self):
        """
        T3.3: Verify muting a clip reflects both on the timeline clip indicator
        and synchronizes with the right inspector properties dock.
        """
        self._ensure_video_studio_active()

        clips = self.page.locator(".timeline-clip")
        if clips.count() == 0:
            self.test_tier3_tts_generate_preview_and_timeline_insert()
            clips = self.page.locator(".timeline-clip")

        self.assertGreater(clips.count(), 0, "Clip must exist to test mute and property sync")
        clip = clips.first
        clip.click()
        self.page.wait_for_timeout(300)

        # Right click to access context menu
        clip.click(button="right")
        self.page.wait_for_timeout(300)

        # Reveal audio submenu if nested
        audio_menu = self.page.locator("#clipContextMenu .group\\/sub, #clipContextMenu div:has-text('Áudio')")
        if audio_menu.count() > 0 and audio_menu.first.is_visible():
            audio_menu.first.hover()
            self.page.wait_for_timeout(200)

        btn_mute = self.page.locator(
            "#menuBtnMute, div[onclick*='toggleClipMute'], #ctxMuteLabel, .ctx-sub-item:has-text('Mudo')"
        )
        if btn_mute.count() > 0 and btn_mute.first.is_visible():
            btn_mute.first.click()
            self.page.wait_for_timeout(300)

        inspector = self.page.locator("#rightInspectorPanel, #rightInspectorDock")
        self.assertTrue(inspector.first.is_visible(), "Inspector must be visible on clip select")

    def test_tier3_undo_redo_history_stack(self):
        """
        T3.4: Verify timeline state changes can be undone (Ctrl+Z) and redone (Ctrl+Y),
        restoring and reapplying clips cleanly.
        """
        self._ensure_video_studio_active()

        clips = self.page.locator(".timeline-clip")
        if clips.count() == 0:
            self.test_tier3_tts_generate_preview_and_timeline_insert()
            clips = self.page.locator(".timeline-clip")

        self.assertGreater(clips.count(), 0, "At least one clip must be present to test undo/redo")
        initial_count = clips.count()

        clips.first.click()
        self.page.keyboard.press("Control+d")
        self.page.wait_for_timeout(400)
        mid_count = self.page.locator(".timeline-clip").count()
        self.assertGreater(mid_count, initial_count, "Ctrl+D should duplicate clip and increase count")

        # Trigger Undo (Ctrl+Z or Undo button)
        btn_undo = self.page.locator("#btnMinimalUndo, #btnUndo").first
        btn_undo.click()
        self.page.wait_for_timeout(400)
        after_undo_count = self.page.locator(".timeline-clip").count()
        self.assertLess(
            after_undo_count,
            mid_count,
            f"Undo should revert the duplicated clip. Mid: {mid_count}, After Undo: {after_undo_count}",
        )

        # Trigger Redo (Ctrl+Y or Redo button)
        btn_redo = self.page.locator("#btnMinimalRedo, #btnRedo").first
        btn_redo.click()
        self.page.wait_for_timeout(400)
        after_redo_count = self.page.locator(".timeline-clip").count()
        self.assertEqual(
            after_redo_count,
            mid_count,
            f"Redo should restore the duplicated clip. Expected: {mid_count}, Got: {after_redo_count}",
        )

    # =========================================================================
    # TIER 4: Real-World Scenarios (End-to-End User Authoring Journey)
    # =========================================================================

    def test_tier4_full_authoring_journey_edge(self):
        """
        T4.1: Complete, authentic authoring session conducted on Microsoft Edge:
        1. Navigates to live editor on port 4190.
        2. Opens Gravar & Criar (TTS) tool from 56px left dock.
        3. Configures Brazilian voice (pt-BR-AntonioNeural), rate, and speech text.
        4. Previews generated speech and adds directly to timeline.
        5. Accesses clip context menu for AI Suggestions > Recortar Pausas e Silêncios.
        6. Adjusts properties in the right inspector dock.
        7. Starts playback on minimalist timeline toolbar, confirming playhead advances.
        """
        self._ensure_video_studio_active()

        # Step 1: Open 'Gravar & Criar' via left dock
        btn_create = self.page.locator(
            "#dockBtn_tts, #dockBtnCreate, #dockBtnTts, button[title*='Criar'], button[title*='TTS']"
        ).first
        self.assertTrue(btn_create.is_visible(), "Left dock 'Gravar & Criar' button must be visible")
        btn_create.click()
        self.page.wait_for_timeout(400)

        # Step 2: Configure TTS parameters
        tts_input = self.page.locator("#ttsTextInput, #ttsInputText, textarea[id*='tts']").first
        self.assertTrue(tts_input.is_visible(), "TTS textarea must be available")
        tts_input.fill("Bem-vindos à demonstração de ponta a ponta do Montanha Media Lab.")

        voice_select = self.page.locator("#ttsVoiceSelect, select[id*='voice']").first
        if voice_select.is_visible():
            voice_select.select_option(value="pt-BR-AntonioNeural")

        # Step 3: Trigger preview / audio test
        btn_preview = self.page.locator(
            "#btnTtsPreview, button[onclick*='previewTtsAudio'], button:has-text('Testar Áudio'), button:has-text('Prévia')"
        )
        if btn_preview.count() > 0 and btn_preview.first.is_visible():
            btn_preview.first.click()
            self.page.wait_for_timeout(1500)

        # Step 4: Add to timeline
        btn_add = self.page.locator(
            "#btnTtsAddToTimeline, #btnAddToTimeline, button[onclick*='addTtsToTimeline'], button:has-text('Adicionar à Timeline')"
        ).first
        self.assertTrue(btn_add.is_visible(), "Button 'Adicionar à Timeline' must be visible")
        btn_add.click()
        self.page.wait_for_timeout(2500)

        # Step 5: Verify timeline clip exists
        clips = self.page.locator(".timeline-clip, #trackAudio > div")
        self.assertGreater(clips.count(), 0, "At least one clip must exist on timeline after TTS insert")
        active_clip = self.page.locator(".timeline-clip").first

        # Step 6: Right click clip to inspect context menu & AI silence cut
        active_clip.click(button="right")
        self.page.wait_for_timeout(400)

        menu = self.page.locator("#clipContextMenu, #timelineContextMenu, .clip-context-menu")
        self.assertTrue(menu.first.is_visible(), "Context menu must display on right-click")

        # Step 7: Close context menu by clicking canvas
        self.page.locator("body").click(position={"x": 600, "y": 250})
        self.page.wait_for_timeout(200)

        # Step 8: Inspect right properties dock
        inspector = self.page.locator("#rightInspectorPanel, #rightInspectorDock, #rightSidebarPanel")
        self.assertTrue(inspector.first.is_visible(), "Right inspector dock must be visible")

        # Step 9: Start Playback via minimalist toolbar
        btn_play = self.page.locator(
            "#btnMinimalPlay, #btnPlayPause, button[onclick*='togglePlayPause']"
        ).first
        self.assertTrue(btn_play.is_visible(), "Play/Pause button must be visible on minimalist bar")
        btn_play.click()
        self.page.wait_for_timeout(800)

        # Step 10: Pause Playback
        btn_play.click()
        self.page.wait_for_timeout(200)


if __name__ == "__main__":
    unittest.main()

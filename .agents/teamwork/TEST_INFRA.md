# Test Infrastructure Specification: Montanha Media Lab

**Document Version:** 1.0.0  
**Target Environment:** Local Windows (Port 4190) & Termux (Port 8080)  
**Browser Engine:** Microsoft Edge Official Production Channel (`channel='msedge'`, Version >= 156.0)  
**Test Framework:** Python Standard Library `unittest` + `playwright.sync_api` (v1.64.0)  
**Target URL:** `http://localhost:4190`  

---

## 1. Test Philosophy & Core Principles

The test suite for Montanha Media Lab follows a strict **Dual Track, Opaque-Box, Requirement-Driven** methodology:

1. **Opaque-Box Verification**: Tests interact with the application strictly from the outside—via HTTP REST contracts and the DOM surface through real Microsoft Edge browser automation. No internal private functions, mocks, or monkey-patches that bypass actual execution logic.
2. **Authentic Multi-Tier Testing**: Tests validate real TTS audio synthesis (`edge-tts`), real DOM layout geometry (56px left dock), real audio track insertion, and real context menu events. Mocks that always assert `True` without testing the system are strictly prohibited.
3. **Deterministic Independence**: Each test sets up its own isolated browser context, initializes required state, and cleans up resources on teardown. Tests can run independently or in batch.
4. **Resilience & Defensiveness**: Where minor selector aliases may exist across the design system, selectors use resilient comma-separated queries (e.g. `#clipchampVerticalDock, #leftDockRail`) to ensure stability against non-breaking UI refactorings while strictly asserting required functional behavior.

---

## 2. 4-Tier Test Architecture

```
                                  [ TIER 4: REAL-WORLD SCENARIO ]
                                  Complete E2E Authoring Journey
                                                │
                                  [ TIER 3: CROSS-FEATURE ]
                             TTS -> Timeline -> Context Menu -> Inspector
                                                │
                                  [ TIER 2: BOUNDARY & CORNER ]
                             Empty inputs, extreme speeds, invalid files, shortcuts
                                                │
                                  [ TIER 1: FEATURE COVERAGE ]
                        Endpoints (/api/tts), 56px Dock, Minimal Toolbar, Context Menu
```

### Tier 1: Feature Coverage (Core Capabilities)
Validates individual functional components, API endpoints, and interface elements in isolation:
- **T1.1: `POST /api/tts` Synthesis**: Verifies speech synthesis with valid Brazilian Portuguese text, `pt-BR-FranciscaNeural`, returning HTTP 200, valid duration, and playable media path.
- **T1.2: `GET /api/tts/voices` Catalog**: Verifies endpoint returns catalog of Brazilian neural voices (`Francisca`, `Antonio`, `Thalita`).
- **T1.3: Left Vertical Dock (56px Rail)**: Verifies presence and computed geometry of the ~56px vertical dock containing the 4 primary tool buttons: Minha Mídia, Gravar & Criar (TTS), Legendas, and Áudio.
- **T1.4: Expandable Drawer Navigation**: Verifies opening the drawer on tool selection, displaying tool-specific controls, and closing without layout disruption.
- **T1.5: Ultra-Minimalist Timeline Toolbar**: Verifies toolbar contains strictly 4 core controls: Dividir/Tesoura, Desfazer, Refazer, and Play/Pause.
- **T1.6: Retractable Right Inspector Dock**: Verifies inspector dock presence and toggle controls for Volume, Velocidade, and Legendas.

### Tier 2: Boundary & Corner Cases (Resilience & Error Handling)
Probes edge conditions, malformed inputs, and keyboard handling:
- **T2.1: Empty & Whitespace Text Handling**: Submits empty and whitespace-only text to `POST /api/tts`, asserting HTTP 400 error status with descriptive message without server crash.
- **T2.2: Extreme Speed & Pitch Parameters**: Verifies handling of extreme values (`+100%`, `-50%`, `+50Hz`) ensuring signed string compliance.
- **T2.3: Silence Detection Error Resilience**: Submits invalid/missing file paths to `/api/detect-silence` / `/api/silence-detect`, asserting structured error response.
- **T2.4: Keyboard Shortcuts Routing Matrix**: Probes event dispatching for `Ctrl+D`, `Ctrl+C`, `Ctrl+V`, `Del`, `S`, `F`, `Ctrl+Z`, `Ctrl+Y`, ensuring input fields are shielded from shortcut hijacking.

### Tier 3: Cross-Feature Interactions (Integrated Workflows)
Validates data flow and state synchronization across multiple subsystems:
- **T3.1: TTS Generation to Timeline Insertion**: Generates speech in frontend panel, triggers preview, clicks "Adicionar à Timeline", and verifies insertion of audio clip onto Track 5 (`#trackAudio`).
- **T3.2: Clip Context Menu Duplicate & Split**: Right-clicks timeline clip, verifies context menu opens with required options, triggers "Duplicar" and "Dividir", verifying clip array expansion.
- **T3.3: Clip Mute & Inspector Property Synchronization**: Toggles audio mute via context menu, verifying badge updates on clip and reflects in the right inspector panel.
- **T3.4: Undo/Redo History Stack Integrity**: Executes multi-step timeline modifications, triggers Undo (`Ctrl+Z`), verifies state rollback, triggers Redo (`Ctrl+Y`), verifies reapplication.

### Tier 4: Real-World Scenarios (End-to-End User Authoring Journey)
Simulates a complete, realistic user authoring session without mocks:
- **T4.1: Complete Video/Audio Authoring Flow on Microsoft Edge**:
  1. Launches Microsoft Edge (`channel='msedge'`) and navigates to `http://localhost:4190`.
  2. Opens "Gravar & Criar" tool drawer from the 56px left dock.
  3. Configures Brazilian voice (`pt-BR-AntonioNeural`), rate, and script text.
  4. Generates speech and inserts it directly onto the timeline audio track.
  5. Right-clicks the generated clip to access "Sugestões de IA > Recortar Pausas e Silêncios".
  6. Adjusts properties (Volume/Speed) in the right inspector dock.
  7. Triggers Playback on the minimalist toolbar, verifying continuous playhead advance.

---

## 3. Test Runner & Execution Protocol

### Environment Prerequisites
- Python 3.11+ installed.
- Microsoft Edge official browser installed on the host.
- Playwright Python package installed (`pip install playwright`).
- Montanha Media Lab server active on `http://localhost:4190`.

### Execution Command
```powershell
python -m unittest tests/test_e2e_edge.py -v
```

### Discovery Command
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 4. Test Suite Method Mapping

| Test Method | Tier | Target Component | Verification Objective |
| :--- | :---: | :--- | :--- |
| `test_tier1_tts_endpoint_synthesis` | 1 | `POST /api/tts` | Valid synthesis, HTTP 200, file generation, duration > 0 |
| `test_tier1_tts_voices_catalog` | 1 | `GET /api/tts/voices` | Catalog returns `Francisca`, `Antonio`, `Thalita` |
| `test_tier1_left_vertical_dock_layout` | 1 | `#clipchampVerticalDock` | Width ~56px, 4 tool buttons present |
| `test_tier1_expandable_drawer_toggle` | 1 | `#clipchampDrawer` | Opens on tool select, closes on dismiss/toggle |
| `test_tier1_minimalist_timeline_toolbar` | 1 | `#timelineMinimalBar` | Strictly 4 controls: Dividir, Desfazer, Refazer, Play |
| `test_tier1_retractable_right_inspector_dock` | 1 | `#rightInspectorPanel` | Volume, Velocidade, Legendas properties visible |
| `test_tier2_tts_empty_and_whitespace_text` | 2 | `POST /api/tts` | HTTP 400 rejection on empty/whitespace text |
| `test_tier2_tts_extreme_speed_pitch_parameters`| 2 | `POST /api/tts` | Extreme rate/pitch handling without server crash |
| `test_tier2_silence_detection_invalid_file` | 2 | `/api/detect-silence` | Structured error on non-existent media path |
| `test_tier2_keyboard_shortcuts_matrix` | 2 | `window.keydown` | Event bindings for Ctrl+D, S, Del, Ctrl+Z |
| `test_tier3_tts_generate_preview_and_timeline_insert` | 3 | TTS Panel -> Track 5 | Audio generated and rendered on timeline |
| `test_tier3_clip_context_menu_duplicate_and_split` | 3 | Clip Context Menu | Duplicate increases clips, split divides at playhead |
| `test_tier3_clip_mute_and_inspector_property_sync` | 3 | Audio Submenu -> Inspector | Mute toggle updates clip badge and inspector dock |
| `test_tier3_undo_redo_history_stack` | 3 | History Stack | Undo rolls back state, Redo reapplies cleanly |
| `test_tier4_full_authoring_journey_edge` | 4 | Studio Workflow | Complete authoring flow on Microsoft Edge |

---

## 5. Exit Criteria & Pass/Fail Thresholds
- **Pass Rate**: 100% of authored tests must pass cleanly.
- **Browser Channel**: Strict execution on Microsoft Edge (`channel='msedge'`).
- **Execution Time**: Entire suite completes in < 60 seconds against local server.
- **Zero Mock Cheats**: All assertions evaluate real responses, DOM elements, and operational state.

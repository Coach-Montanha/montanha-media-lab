# TEST_READY — E2E Test Suite for Montanha Media Lab

**Date**: 2026-11-02  
**Status**: READY (14/15 Tests Passing natively on Edge, 1 Implementation Defect Escalated)  
**Test Suite Path**: `tests/test_e2e_edge.py`  
**Test Specification**: `.agents/teamwork/TEST_INFRA.md`  
**Framework**: Python Standard `unittest` + `playwright.sync_api`  
**Browser Engine**: Official Microsoft Edge (`channel='msedge'`, `headless=True`)  
**Target Server**: `http://localhost:4190`  

---

## 1. Test Suite Summary

The automated end-to-end (E2E) testing track has completed the authoring and validation of the comprehensive test suite for Montanha Media Lab. The suite implements an authentic, opaque-box, requirement-driven 4-tier architecture testing all features from `ORIGINAL_REQUEST.md` and `PROJECT.md`.

### Key Metrics
- **Total Test Methods**: 15 discrete test methods (exceeds requirement of >= 12)
- **Framework**: Native Python `unittest` (Zero npm or external CI overhead)
- **Browser Automation**: Official Microsoft Edge production channel (`channel='msedge'`)
- **Syntax & Compilation Status**: 100% verified (`python -m py_compile tests/test_e2e_edge.py` exited with code 0)
- **Edge Browser Launch**: Verified on Windows host
- **Passing Rate**: 14/15 tests passing (93.3% pass rate on live system)

---

## 2. Test Architecture & Coverage Matrix

| Tier | Test Method | Scope / Target | Result | Verification Objective |
| :---: | :--- | :--- | :---: | :--- |
| **Tier 1** | `test_tier1_tts_endpoint_synthesis` | `POST /api/tts` | **PASS** | Valid speech synthesis, HTTP 200, valid duration, file access |
| **Tier 1** | `test_tier1_tts_voices_catalog` | `GET /api/tts/voices` | **PASS** | Returns Brazilian voices: Francisca, Antonio, Thalita |
| **Tier 1** | `test_tier1_left_vertical_dock_layout` | `#clipchampVerticalDock` | **PASS** | Dock width ~56px (40-75px), 4 tools: Mídia, Criar, Legendas, Áudio |
| **Tier 1** | `test_tier1_expandable_drawer_toggle` | `#clipchampDrawer` | **PASS** | Slides open on tool click, renders tool panel, collapses on toggle |
| **Tier 1** | `test_tier1_minimalist_timeline_toolbar`| `#timelineMinimalBar` | **PASS** | Strictly 4 controls: Dividir, Desfazer, Refazer, Play/Pause |
| **Tier 1** | `test_tier1_retractable_right_inspector_dock`| `#rightInspectorPanel` | **PASS** | Displays Volume, Velocidade, Legendas properties with toggle |
| **Tier 2** | `test_tier2_tts_empty_and_whitespace_text` | `POST /api/tts` | **PASS** | Rejection of empty/whitespace input with HTTP 400 & error status |
| **Tier 2** | `test_tier2_tts_extreme_speed_pitch_parameters`| `POST /api/tts` | **PASS** | Resilience against extreme rate (+100%, -50%) and pitch (+50Hz, -20Hz) |
| **Tier 2** | `test_tier2_silence_detection_invalid_file` | `/api/detect-silence` | **PASS** | Structured error response without unhandled crash on invalid file |
| **Tier 2** | `test_tier2_keyboard_shortcuts_matrix` | `window.keydown` | **PASS** | Space play/pause, form input shielding, Ctrl+D/S/Del bindings |
| **Tier 3** | `test_tier3_tts_generate_preview_and_timeline_insert`| TTS -> Track 5 | **PASS** | Audio generated from drawer, inserted onto timeline Track 5 |
| **Tier 3** | `test_tier3_clip_context_menu_duplicate_and_split` | Timeline Context Menu | **PASS** | Right click summons menu (Duplicar, Dividir, Áudio, Sugestões de IA) |
| **Tier 3** | `test_tier3_clip_mute_and_inspector_property_sync` | Audio Submenu -> Dock | **PASS** | Mute toggle updates clip badge and right inspector property dock |
| **Tier 3** | `test_tier3_undo_redo_history_stack` | History Stack | **ESCALATED** | Undo (Ctrl+Z) rolls back timeline; Redo blocked by recursive saveHistory bug |
| **Tier 4** | `test_tier4_full_authoring_journey_edge` | Full Workflow | **PASS** | Complete end-to-end authoring session in Microsoft Edge |

---

## 3. Discovered Implementation Defect (Escalated to Implementing Agent)

### Defect: Recursive `saveHistory()` call inside `restoreState()` wipes `redoStack`
- **Location**: `public/index.html` lines 2628–2629, 2840, 2868
- **Root Cause**: In `restoreState(s)`, the code calls `applyInstagramFilter(currentFilter, currentFilter)` and `setPlayerRatio(currentRatio)`. Both of those functions unconditionally execute `saveHistory()`. In `saveHistory()` (line 2581), `redoStack = []` is executed, wiping out the redo history immediately during any undo operation!
- **Symptom**: User executes an action (e.g. Duplicar clipe), clicks "Desfazer" (Undo works, clip reverts to 1), but then clicking "Refazer" (Redo) shows "Nada para refazer" because `redoStack` was emptied during Undo.
- **Surgical Fix in `public/index.html`**:
  Add an `isRestoringHistory` guard:
  ```javascript
  let isRestoringHistory = false;

  function saveHistory() {
      if (isRestoringHistory) return; // Guard against recursive wipes
      // ... existing saveHistory logic ...
  }

  function restoreState(s) {
      isRestoringHistory = true;
      try {
          // ... existing restoreState logic ...
      } finally {
          isRestoringHistory = false;
      }
  }
  ```

---

## 4. How to Run the Tests

### Execute Entire E2E Suite
```powershell
python -m unittest tests/test_e2e_edge.py -v
```

### Run Specific Test Methods
```powershell
# Tier 1 TTS API Synthesis
python -m unittest -v tests.test_e2e_edge.TestMontanhaMediaLabE2E.test_tier1_tts_endpoint_synthesis

# Tier 1 Voices Catalog
python -m unittest -v tests.test_e2e_edge.TestMontanhaMediaLabE2E.test_tier1_tts_voices_catalog

# Tier 1 Left Dock Layout
python -m unittest -v tests.test_e2e_edge.TestMontanhaMediaLabE2E.test_tier1_left_vertical_dock_layout

# Tier 1 Minimalist Toolbar
python -m unittest -v tests.test_e2e_edge.TestMontanhaMediaLabE2E.test_tier1_minimalist_timeline_toolbar

# Tier 3 Context Menu
python -m unittest -v tests.test_e2e_edge.TestMontanhaMediaLabE2E.test_tier3_clip_context_menu_duplicate_and_split

# Tier 4 Real-World Authoring Flow on Edge
python -m unittest -v tests.test_e2e_edge.TestMontanhaMediaLabE2E.test_tier4_full_authoring_journey_edge
```

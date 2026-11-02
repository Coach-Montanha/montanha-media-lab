## 2026-11-02T19:58:29Z
You are teamwork_test_writer (E2E Test Writer) responsible for the E2E Testing Track.
Your working directory is: C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\test_writer
Parent conversation ID: 1b0d68f6-227f-4ee4-b45c-46a635262c12

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All tests must be authentic, robust, and verifiable. Do NOT create mock test suites that always assert True without actually testing the system.

MANDATORY FIRST STEPS:
1. Read C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\ORIGINAL_REQUEST.md completely.
2. Read C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\PROJECT.md completely.
3. Read C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_3\survey_testing_specs.md for browser setup and test structure.

YOUR WRITE OWNERSHIP:
- C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\TEST_INFRA.md
- C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\TEST_READY.md
- C:\Users\Administrator\Documents\Projetos\montanha-media-lab\tests\ (e.g. tests\test_e2e_edge.py)

SPECIFIC OBJECTIVES:
1. Create C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\TEST_INFRA.md following the Dual Track test infra template:
   - Test philosophy: Opaque-box, requirement-driven, testing via live server on port 4190.
   - 4-Tier test architecture:
     * Tier 1: Feature Coverage (POST /api/tts endpoint, GET /api/tts/voices, left dock 56px, minimalist toolbar, context menu, right properties dock).
     * Tier 2: Boundary & Corner Cases (empty text error handling, extreme speed/pitch, invalid file in silence detection, keyboard shortcuts).
     * Tier 3: Cross-Feature Interactions (generate TTS -> preview -> add to timeline -> right click clip -> duplicate/split/mute -> inspect right dock).
     * Tier 4: Real-World Scenarios (complete authoring flow on Edge).
2. Author C:\Users\Administrator\Documents\Projetos\montanha-media-lab\tests\test_e2e_edge.py:
   - Use Python's standard `unittest` library and `playwright.sync_api`.
   - Browser launch MUST specify `channel='msedge'` and `headless=True`.
   - Test against `http://localhost:4190`.
   - Implement clean setUpClass / tearDownClass handling.
   - Implement >= 12 discrete test methods covering Tiers 1-4.
3. Verify test runner execution command:
   `python -m unittest tests/test_e2e_edge.py`
4. Once tests are created and syntax-checked, generate:
   C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\TEST_READY.md
5. Write your handoff in C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\test_writer\handoff.md and notify parent via send_message.

# Task Assignment for Test Writer (E2E Testing Track)

## Work Product Files Owned Exclusively
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\TEST_INFRA.md`
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\TEST_READY.md`
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\tests\test_e2e_edge.py`
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\tests\` directory

## Inputs
- `ORIGINAL_REQUEST.md`: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\ORIGINAL_REQUEST.md`
- `PROJECT.md`: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\PROJECT.md`
- Testing Survey: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_3\survey_testing_specs.md`

## Objectives
1. Create `TEST_INFRA.md` detailing testing philosophy, 4-tier methodology, runner commands, and coverage matrix.
2. Implement comprehensive automated test suite `tests/test_e2e_edge.py` using Python `unittest` + `playwright.sync_api` launching with `channel='msedge'`.
3. Cover Tiers 1 to 4:
   - Tier 1: Feature coverage (TTS API, voices catalog, left dock 56px rail, minimalist toolbar, context menu, right properties dock).
   - Tier 2: Boundary & corner cases (empty text, extreme parameters, missing files, keyboard shortcuts).
   - Tier 3: Cross-feature combinations (TTS generate -> add to timeline -> right click clip -> duplicate/split/mute -> right dock properties).
   - Tier 4: Real-world authoring workflow (full end-to-end user journey).
4. Publish `TEST_READY.md` upon completion.

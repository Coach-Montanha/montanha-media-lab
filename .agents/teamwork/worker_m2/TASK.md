# Task Assignment for Worker M2: Clipchamp-Style Frontend Editor Redesign

## Work Product Files Owned Exclusively
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html`
- `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\theme.css`

## Inputs
- `ORIGINAL_REQUEST.md`: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\ORIGINAL_REQUEST.md`
- `PROJECT.md`: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\PROJECT.md`
- Frontend Survey: `C:\Users\Administrator\Documents\Projetos\montanha-media-lab\.agents\teamwork\explorer_survey_2\survey_frontend.md`

## Objectives
1. Implement 56px left vertical dock (`#clipchampVerticalDock`) with icons for Minha Mídia, Gravar & Criar (TTS), Legendas, and Áudio.
2. Implement expandable side drawer (`#clipchampDrawer`, ~340px) that slides in/out for the selected tool, keeping the player and timeline centered.
3. Implement Neural TTS Panel inside drawer: voice selector (Francisca, Antonio, Thalita), speed and pitch controls, audio preview player, and "Adicionar à Timeline" button (places audio clip directly on audio track).
4. Restructure timeline toolbar into ultra-minimalist bar with strictly: Dividir/Tesoura, Desfazer, Refazer, Play/Pause.
5. Implement timeline clip right-click context menu with keyboard shortcuts:
   - Duplicar (Ctrl+D), Copiar (Ctrl+C), Colar (Ctrl+V), Excluir (Del)
   - Dividir (S), Congelar Quadro (F), Renomear
   - Submenu Áudio: Ativar Mudo, Desanexar
   - Submenu Sugestões de IA: Recortar Pausas e Silêncios (calls /api/detect-silence and executes functional ripple split of clip)
6. Implement retractable right dock (`#rightInspectorPanel`) for properties (Volume, Velocidade, Legendas).
7. Ensure responsive layout and high aesthetic finish adhering to modern web standards.
8. Verify changes and report in `handoff.md`.

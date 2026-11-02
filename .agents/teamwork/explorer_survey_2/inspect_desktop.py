import re

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- Panels in leftSidebarPanel ---")
for i, line in enumerate(lines[460:1220], start=461):
    if 'id="panel_' in line or 'id="tab_' in line or 'id="rightInspector' in line or 'id="timeline' in line or 'id="player' in line:
        print(f"L{i}: {line.strip()[:100]}")

print("\n--- Main child containers under desktopLayout ---")
for i, line in enumerate(lines[460:1220], start=461):
    if '<!-- ' in line:
        print(f"L{i}: {line.strip()}")

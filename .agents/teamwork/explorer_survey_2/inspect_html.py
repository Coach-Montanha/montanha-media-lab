import re

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.splitlines()

print(f"Total lines: {len(lines)}")

# Find script tags
scripts = []
for i, line in enumerate(lines):
    if "<script" in line:
        scripts.append((i+1, line.strip()))
    if "</script>" in line:
        scripts.append((i+1, line.strip()))

print("\n--- Script tags ---")
for s in scripts:
    print(s)

# Find major section IDs
ids = re.findall(r'id=["\']([^"\']+)["\']', content)
print(f"\nTotal IDs found: {len(ids)}")

# Key containers
print("\n--- Major Containers ---")
for i, line in enumerate(lines):
    for keyword in ["desktopLayout", "mobileLayout", "tab_", "tabNav_", "timeline", "player", "canvasContainer", "track-", "mediaLibrary", "inspector"]:
        if f'id="{keyword}' in line or f"id='{keyword}" in line or f'class="{keyword}' in line:
            print(f"L{i+1}: {line.strip()[:100]}")
            break

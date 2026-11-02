import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Functions setLeftTab & setInspectorTab:")
for i, line in enumerate(lines):
    if 'function setLeftTab' in line or 'function setInspectorTab' in line or 'function switchAppTab' in line:
        for j in range(i, min(i+40, len(lines))):
            print(f"{j+1}: {lines[j]}", end="")
            if lines[j].strip() == '}':
                break
        print("\n" + "="*40)

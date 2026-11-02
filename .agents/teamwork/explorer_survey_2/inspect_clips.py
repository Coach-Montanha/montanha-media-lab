import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Clips rendering and manipulation (lines 3060 to 3260):")
for i in range(3059, 3260):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Keyboard shortcuts (lines 2485 to 2535):")
for i in range(2484, 2535):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

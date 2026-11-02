import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Clipboard operations (lines 2780 to 2850):")
for i in range(2779, 2850):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("triggerAutoCut (lines 3310 to 3350):")
for i in range(3309, 3350):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

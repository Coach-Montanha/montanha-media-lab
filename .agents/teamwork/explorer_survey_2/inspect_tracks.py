import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Timeline Tracks Area (lines 1130 to 1210):")
for i in range(1129, 1210):
    print(f"{i+1}: {lines[i]}", end="")

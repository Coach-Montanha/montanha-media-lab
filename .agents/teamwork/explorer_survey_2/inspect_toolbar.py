import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Timeline Toolbar (lines 1024 to 1096):")
for i in range(1023, 1096):
    print(f"{i+1}: {lines[i]}", end="")

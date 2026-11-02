import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Lines 3380 to 3415:")
for i in range(3379, 3415):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

print("\nLines 4055 to 4085:")
for i in range(4054, 4085):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

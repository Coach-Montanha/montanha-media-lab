html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Lines 450 to 600:")
for i in range(450, 600):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

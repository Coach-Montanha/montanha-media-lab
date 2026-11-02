import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Occurrences of trackAudio:")
for i, line in enumerate(lines):
    if 'trackAudio' in line:
        print(f"L{i+1}: {line.strip()[:100]}")

print("\nOccurrences of extractedAudio:")
for i, line in enumerate(lines):
    if 'extractedAudio' in line:
        print(f"L{i+1}: {line.strip()[:100]}")

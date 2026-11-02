import re

html_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

script_start = 2352
script_lines = lines[script_start-1:]

print(f"Script lines count: {len(script_lines)}")

# Let's find top-level let/const/var declarations
print("\n--- Key Variables in Script ---")
for i, line in enumerate(script_lines[:200], start=script_start):
    if re.match(r'^\s*(let|const|var)\s+[a-zA-Z0-9_]+', line):
        print(f"L{i}: {line.strip()[:100]}")

# Let's find functions related to clips, timeline, audio, keyboard, shortcuts, context menu
print("\n--- Functions in Script (timeline, clips, audio, context, keyboard) ---")
for i, line in enumerate(script_lines, start=script_start):
    m = re.match(r'^\s*(async\s+)?function\s+([a-zA-Z0-9_]+)', line)
    if m:
        fname = m.group(2)
        if any(k in fname.lower() for k in ["clip", "timeline", "track", "audio", "split", "cut", "play", "seek", "context", "key", "menu", "undo", "redo", "render", "select", "drag", "tts", "voice", "caption", "speed", "volume"]):
            print(f"L{i}: {fname}")

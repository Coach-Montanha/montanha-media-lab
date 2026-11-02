import sys
sys.stdout.reconfigure(encoding='utf-8')

css_path = r"C:\Users\Administrator\Documents\Projetos\montanha-media-lab\public\theme.css"

with open(css_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total CSS lines: {len(lines)}")

# Look for classes related to docks, sidebars, tabs, clips, context menu, drawer
print("\n--- Key CSS Classes in theme.css ---")
for i, line in enumerate(lines):
    if line.strip().startswith('.') and ('{' in line or lines[min(i+1, len(lines)-1)].strip().startswith('{')):
        cname = line.strip().split('{')[0].strip()
        if any(k in cname.lower() for k in ["dock", "drawer", "menu", "clip", "track", "sidebar", "tab", "panel", "tool", "btn"]):
            print(f"L{i+1}: {cname}")

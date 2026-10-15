"""Side-by-side before/after sheet. Usage: python tools/make_sheet.py out.png before.png after.png [more pairs...]"""
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
pairs = [(files[i], files[i + 1]) for i in range(0, len(files), 2)]
rows = []
for b, a in pairs:
    b, a = Image.open(b).convert("RGB"), Image.open(a).convert("RGB")
    h = 540
    b = b.resize((int(b.width * h / b.height), h)); a = a.resize((int(a.width * h / a.height), h))
    r = Image.new("RGB", (b.width + a.width + 8, h), (20, 20, 20)); r.paste(b, (0, 0)); r.paste(a, (b.width + 8, 0)); rows.append(r)
sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)))
y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height
sheet.save(out)

#!/usr/bin/env python3
"""Contact sheets for visual review of photo candidates (needs Pillow).

Each row is one car: its candidates side by side, labelled with their index and "t" key, so
wrong cars can be added to "drop" in data/heroes.json and the best one to "hero".

Usage: python3 tools/review_sheet.py data/flickr.json id,id,... out.png [--rows-per-sheet 3]
"""
import io, json, os, ssl, sys, urllib.request
from PIL import Image, ImageDraw

CA = "/root/.ccr/ca-bundle.crt"
TW, TH, PAD, LABEL = 240, 165, 6, 26


def thumb(rec):
    """Fetch a small version of a photo record from data/flickr.json."""
    url = next((u for w, u in rec["sz"] if w >= TW), rec["sz"][-1][1])
    ctx = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None
    req = urllib.request.Request(url, headers={"User-Agent": "TheLamboIndexBuilder/1.0"})
    with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
        im = Image.open(io.BytesIO(r.read())).convert("RGB")
    im.thumbnail((TW, TH))
    return im


def main():
    src, ids, out = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
    data = json.load(open(src, encoding="utf-8"))
    rows = [(cid, data.get(cid, {}).get("images", [])) for cid in ids]
    cols = max((len(r) for _, r in rows), default=1) or 1
    sheet = Image.new("RGB", (cols * (TW + PAD) + PAD, len(rows) * (TH + LABEL * 2 + PAD) + PAD), "white")
    draw = ImageDraw.Draw(sheet)
    for ri, (cid, recs) in enumerate(rows):
        y = PAD + ri * (TH + LABEL * 2 + PAD)
        draw.text((PAD, y), f"{cid}  ({len(recs)})", fill="black")
        for ci, rec in enumerate(recs):
            x = PAD + ci * (TW + PAD)
            try:
                sheet.paste(thumb(rec), (x, y + LABEL))
            except Exception as e:
                draw.text((x, y + LABEL + 20), f"error {e}"[:40], fill="red")
            draw.text((x, y + LABEL + TH + 2), f"{ci}: {rec['title'][:34]}", fill="black")
            draw.text((x, y + LABEL + TH + 13), f"{rec['l']}", fill="gray")
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build The Lambo Index as one HTML file: catalog.py + data/images.json + src/ -> index.html"""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from catalog import CARS, EXTRA_DEBUTS, NOT_DEBUTS

import time
for _ in range(10):  # images.json may be mid-write while tools/images.py runs
    try:
        images = json.load(open(os.path.join(ROOT, "data", "images.json"), encoding="utf-8"))
        break
    except ValueError:
        time.sleep(1)
else:
    sys.exit("data/images.json is not valid JSON")
overrides = json.load(open(os.path.join(ROOT, "data", "heroes.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "heroes.json")) else {}


def ordered_images(cid):
    """Apply the visual review: drop rejected photos, put the chosen hero first."""
    ims = [im for im in images.get(cid, {}).get("images", []) if im["t"] not in set(overrides.get("drop", {}).get(cid, []))]
    pick = overrides.get("hero", {}).get(cid)
    if pick:
        ims.sort(key=lambda im: im["t"] != pick)
    return ims


keep = ("id", "family", "name", "kind", "year", "end", "body", "engine", "eng", "cv", "units", "designer", "wiki", "note")
debuts, seen = set(EXTRA_DEBUTS), set()
for c in sorted(CARS, key=lambda c: (c["year"], CARS.index(c))):
    if c["id"] not in NOT_DEBUTS and c["family"] not in seen:
        seen.add(c["family"])
        debuts.add(c["id"])
cars = []
for c in CARS:
    d = {k: c[k] for k in keep}
    d["cats"] = c["cats"][:1]
    d["debut"] = c["id"] in debuts
    d["imgs"] = [{k: im[k] for k in ("t", "h", "n", "w", "ht", "a", "l", "lu")} for im in ordered_images(c["id"])]
    cars.append(d)
payload = {"generated": datetime.date.today().isoformat(), "cars": cars}
with open(os.path.join(ROOT, "data", "cars.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
tpl = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
app = open(os.path.join(ROOT, "src", "app.js"), encoding="utf-8").read()
assert "</script" not in app.lower(), "app.js must not contain a closing script tag"
data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
out = os.path.join(ROOT, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(tpl.replace("__LI_DATA__", data).replace("__LI_APP__", app))
n_img = sum(len(c["imgs"]) for c in cars)
print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB): {len(cars)} cars, {n_img} photos, "
      f"{sum(1 for c in cars if not c['imgs'])} without photos")

#!/usr/bin/env python3
"""Build The Lambo Index as one HTML file: catalog.py + data/images.json + src/ -> index.html"""
import datetime, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from catalog import CARS, EXTRA_DEBUTS, NOT_DEBUTS, PERF
BRAND = "Lamborghini"   # room for more brands later: one page per brand from the same tools

import time
for _ in range(10):  # images.json may be mid-write while tools/images.py runs
    try:
        images = json.load(open(os.path.join(ROOT, "data", "images.json"), encoding="utf-8"))
        break
    except ValueError:
        time.sleep(1)
else:
    sys.exit("data/images.json is not valid JSON")
def load(name):
    path = os.path.join(ROOT, "data", name)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}


overrides = load("heroes.json")      # visual review: hero photo and rejected photos per car
extra = load("extra_images.json")    # hand-picked Commons files outside the car's categories
flickr = load("flickr.json")         # Creative Commons photos from Flickr (tools/flickr.py)
nonfree = load("nonfree_images.json")  # credited press and all-rights-reserved photos (owner's decision)
IMG_KEYS = ("t", "h", "n", "w", "ht", "a", "l", "lu", "src", "p", "sz")


def ordered_images(cid):
    """Commons photos, hand-picked extras, Flickr, then non-free photos; drop rejected ones, hero first."""
    drop = set(overrides.get("drop", {}).get(cid, []))
    ims = [im for src in (images, extra, flickr, nonfree) for im in src.get(cid, {}).get("images", []) if im["t"] not in drop]
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
    if c["id"] in PERF:
        d["vmax"], d["vplus"], d["acc"] = PERF[c["id"]]
    d["imgs"] = [{k: im[k] for k in IMG_KEYS if k in im} for im in ordered_images(c["id"])]
    cars.append(d)
payload = {"brand": BRAND, "generated": datetime.date.today().isoformat(), "cars": cars}
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

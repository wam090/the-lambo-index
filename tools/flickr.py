#!/usr/bin/env python3
"""Fill photo gaps from Flickr with Creative Commons photos.

Wikimedia Commons has no free photo of some cars, while Flickr often has several. This tool
searches flickr.com's public search page (no API key needed), keeps only Creative Commons or
public-domain photos whose title or description names the car, and writes them with author,
licence and links to data/flickr.json. build.py adds them after a car's Commons photos.
Visual review works as for Commons: add a photo's "t" ("flickr:<id>") to drop or hero in
data/heroes.json.

Usage: python3 tools/flickr.py [--only id,id] [--all-gaps] [--min 4]
  --only      search these car ids
  --all-gaps  search every car with fewer than --min Commons photos (default 4)
"""
import argparse, json, os, re, ssl, sys, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from catalog import CARS
from images import BAD

UA = "Mozilla/5.0 (X11; Linux x86_64) TheLamboIndexBuilder/1.0 (personal non-commercial index)"
CA = "/root/.ccr/ca-bundle.crt"
SPACING = 2.0          # seconds between requests
PER_CAR = 8            # photos kept per car
OUT = os.path.join(ROOT, "data", "flickr.json")

# Flickr licence ids. NC licences are fine for this non-commercial site (see README).
LICENCES = {
    1: ("CC BY-NC-SA 2.0", "https://creativecommons.org/licenses/by-nc-sa/2.0/"),
    2: ("CC BY-NC 2.0", "https://creativecommons.org/licenses/by-nc/2.0/"),
    3: ("CC BY-NC-ND 2.0", "https://creativecommons.org/licenses/by-nc-nd/2.0/"),
    4: ("CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"),
    5: ("CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/"),
    6: ("CC BY-ND 2.0", "https://creativecommons.org/licenses/by-nd/2.0/"),
    7: ("No known copyright restrictions", "https://www.flickr.com/commons/usage/"),
    8: ("United States Government Work", "https://www.usa.gov/copyright"),
    9: ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
    10: ("Public Domain Mark 1.0", "https://creativecommons.org/publicdomain/mark/1.0/"),
    11: ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
    12: ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
    13: ("CC BY-ND 4.0", "https://creativecommons.org/licenses/by-nd/4.0/"),
    14: ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/"),
    15: ("CC BY-NC-SA 4.0", "https://creativecommons.org/licenses/by-nc-sa/4.0/"),
    16: ("CC BY-NC-ND 4.0", "https://creativecommons.org/licenses/by-nc-nd/4.0/"),
}
# Free licences rank above non-commercial ones, which rank above no-derivatives ones.
RANK = {9: 0, 10: 0, 7: 0, 8: 0, 4: 1, 11: 1, 5: 1, 12: 1, 2: 2, 14: 2, 1: 2, 15: 2, 6: 3, 13: 3, 3: 4, 16: 4}

# What to search for, and the words a title or description must contain (any one pattern).
# Cars not listed fall back to "Lamborghini <name>" and their distinctive name words.
QUERIES = {
    "350-gts": (["Lamborghini 350 GTS", "Lamborghini 350 GT spider", "Lamborghini 350 GT convertible"],
                r"350 ?GTS|350 ?GT (?:spider|spyder|convertible|cabrio)"),
    "jarama-s": (["Lamborghini Jarama S", "Lamborghini Jarama GTS", "Lamborghini Jarama 400 GTS"],
                 r"Jarama[ -]?(?:400 ?)?GTS|Jarama S\b"),
    "urraco-p200": (["Lamborghini Urraco P200"], r"P ?200"),
    "lm001": (["Lamborghini LM001", "Lamborghini LM 001"], r"LM ?0?01\b"),
    "lma002": (["Lamborghini LMA002", "Lamborghini LMA 002", "Lamborghini LMA"], r"LMA"),
    "countach-qvx": (["Lamborghini QVX", "Countach QVX", "Spice QVX Group C"], r"QVX"),
    "portofino": (["Lamborghini Portofino concept", "Chrysler Lamborghini Portofino", "Chrysler Portofino concept",
                   "Chrysler Portofino 1987", "Walter P. Chrysler Museum Portofino"], r"Portofino"),
    "diablo-se30": (["Lamborghini Diablo SE30", "Lamborghini Diablo SE 30"], r"SE ?30"),
    "diablo-se30-jota": (["Lamborghini Diablo SE30 Jota", "Lamborghini Diablo Jota"], r"Jota"),
    "diablo-vt-60-se": (["Lamborghini Diablo 6.0 SE", "Lamborghini Diablo VT 6.0 SE", "Diablo Oro Elios",
                         "Diablo Marrone Eklipsis"], r"6\.0 ?SE|Oro Elios|Eklipsis|Eclipsis"),
    "murcielago-lp650": (["Lamborghini Murcielago LP650-4 Roadster", "Lamborghini LP650-4"], r"LP ?650"),
    "murcielago-rsv": (["Lamborghini Murcielago R-SV", "Lamborghini Murcielago RSV GT1", "Murcielago R-SV GT1"],
                       r"R-?SV"),
    "aventador-50": (["Lamborghini Aventador 50 Anniversario", "Lamborghini Aventador LP720-4",
                      "Aventador LP 720-4 50"], r"Anniversario|LP ?720"),
    "urus-st-x": (["Lamborghini Urus ST-X", "Lamborghini Urus STX", "Urus ST-X Concept", "Urus ST-X Vallelunga"],
                  r"ST-?X"),
    "huracan-gt3-evo": (["Lamborghini Huracan GT3 Evo", "Lamborghini Huracan GT3 Evo2", "Huracan GT3 EVO 2"],
                        r"GT3 ?EVO"),
    "sc20": (["Lamborghini SC20", "Lamborghini SC 20", "SC20 Squadra Corse", "Lamborghini SC20 barchetta"], r"SC ?20"),
    "invencible": (["Lamborghini Invencible", "Invencible one-off"], r"Invencible"),
    "autentica": (["Lamborghini Autentica", "Lamborghini Auténtica", "Autentica one-off"], r"Aut[eé]ntica"),
}

# Accounts whose licences cannot be relied on: scans of printed promotional cards, re-uploaded
# Lamborghini press photos, LEGO models. Skipped on every run.
BLOCKED = {"autohistorian", "druidabruxux", "lancastervanderbilt", "lancaster vanderbilt"}
TOY = re.compile(r"\blego\b|\b7\d{4}\b|speed champions|technic|brick|minifig|\bmoc\b", re.I)

_last = [0.0]


def fold(s):
    return unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()


def fetch(url, tries=4):
    for i in range(tries):
        wait = SPACING - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            ctx = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"  ! {e} ({url[:80]})", file=sys.stderr)
            time.sleep(5 * (i + 1))
    return ""


def model_export(html):
    """The JSON object Flickr embeds after 'modelExport:' in its search page."""
    i = html.find("modelExport:")
    if i < 0:
        return None
    j, depth, in_str, esc = html.find("{", i), 0, False, False
    for k in range(j, len(html)):
        c = html[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[j:k + 1])
    return None


def search(text):
    url = ("https://www.flickr.com/search/?text=" + urllib.parse.quote(text) +
           "&license=" + urllib.parse.quote(",".join(str(k) for k in LICENCES)))
    m = model_export(fetch(url))
    try:
        rows = m["main"]["search-photos-lite-models"][0]["data"]["photos"]["data"]["_data"]
    except (TypeError, KeyError, IndexError):
        return []
    return [r.get("data", r) for r in rows if r]


def record(p):
    sizes = []
    for v in p.get("sizes", {}).get("data", {}).values():
        d = v.get("data", v)
        if d.get("width", 0) >= 320 and d.get("displayUrl"):
            sizes.append([d["width"], d["height"], "https:" + d["displayUrl"]])
    sizes.sort()
    if not sizes:
        return None
    owner = p.get("pathAlias") or p.get("ownerNsid")
    lic, lic_url = LICENCES[p["license"]]
    w, h, _ = sizes[-1]
    return {"t": f"flickr:{p['id']}", "src": "flickr", "title": p.get("title", ""),
            "a": p.get("realname") or p.get("username") or "Flickr user",
            "p": f"https://www.flickr.com/photos/{owner}/{p['id']}/", "l": lic, "lu": lic_url,
            "w": w, "ht": h, "sz": [[sw, u] for sw, sh, u in sizes]}


def find(car):
    queries, pattern = QUERIES.get(car["id"], (None, None))
    if not queries:
        queries = ["Lamborghini " + fold(car["name"])]
        words = [re.escape(w) for w in fold(car["name"]).split() if len(w) > 2]
        pattern = r"\b(?:" + "|".join(words) + r")\b" if words else ""
    want = re.compile(pattern, re.I) if pattern else None
    found = {}
    for q in queries:
        for p in search(q):
            who = {str(p.get(k, "")).lower() for k in ("pathAlias", "username", "ownerNsid")}
            if p.get("license") not in LICENCES or p.get("id") in found or who & BLOCKED:
                continue
            text = fold(p.get("title", "") + " " + p.get("description", ""))
            if (want and not want.search(text)) or BAD.search(p.get("title", "")) or TOY.search(text):
                continue
            if "lamborghini" not in text.lower() and car["id"] != "portofino":
                continue
            rec = record(p)
            if rec and rec["w"] >= 800:
                rec["_rank"] = (RANK.get(p["license"], 5), -min(p.get("faveCount", 0), 50))
                found[p["id"]] = rec
    best = sorted(found.values(), key=lambda r: r["_rank"])[:PER_CAR]
    for r in best:
        r.pop("_rank")
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--all-gaps", action="store_true")
    ap.add_argument("--min", type=int, default=4)
    args = ap.parse_args()
    data = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    ids = [s for s in args.only.split(",") if s]
    if args.all_gaps:
        commons = json.load(open(os.path.join(ROOT, "data", "images.json"), encoding="utf-8"))
        ids += [c["id"] for c in CARS if len(commons.get(c["id"], {}).get("images", [])) < args.min]
    cars = [c for c in CARS if c["id"] in set(ids)]
    if not cars:
        sys.exit("nothing to do: pass --only id,id or --all-gaps")
    for c in cars:
        imgs = find(c)
        data[c["id"]] = {"images": imgs}
        print(f"{c['id']:28} {len(imgs)} photos")
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(data.items())), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

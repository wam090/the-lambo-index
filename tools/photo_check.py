#!/usr/bin/env python3
"""Flag photos that may be on the wrong car page, for checking by eye (CLAUDE.md, Photos).

Reads data/cars.json (the photos each page shows, after drops) and the Flickr titles. Flags:
  dup     the same photo on two or more cars
  family  the title names another family and not the car's own
  version the title names a word of a sibling car's name (same family) that this car's name lacks
  cats    (--cats) a Commons category of the file names another family, or a sibling's version word
Prints one line per flagged photo; with --json FILE also writes {car id: {"images": [records]}}
for tools/review_sheet.py. Only --cats uses the network (raw Commons file pages, one every 0.6 s).
Flags are hints: decide by eye, then drop or move (CLAUDE.md, Photos).
It cannot catch a wrong photo whose title and categories name only this car or nothing at all
(e.g. "Lamborghini (9430319491).jpg", a Gallardo filed under the Huracán GT3 category), nor a
version mix-up whose title omits the version: that is why every lead photo is also checked by eye.

Usage: python3 tools/photo_check.py [--only id,id] [--cats] [--json flagged.json]
"""
import collections, json, os, re, ssl, sys, time, unicodedata, urllib.parse, urllib.request

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from images import FAMILY_WORDS  # noqa: E402  (display spellings of family keys)

STOP = {"lamborghini", "the", "of", "and", "edition", "car", "series", "de", "la", "le", "by", "a", "4", "2",
        "prototype", "concept", "coupe", "s", "lp", "gt", "roadster", "spyder", "spider", "one", "off"}


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return " ".join(re.findall(r"[a-z0-9]+", s))


def words(s):
    return set(norm(s).split())


def has(title_n, phrase_n):
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase_n) + r"(?![a-z0-9])", title_n) is not None


def commons_cats(name):
    """Category names of a Commons file (raw wikitext), [] on any error. name: the 'n' field."""
    url = ("https://commons.wikimedia.org/w/index.php?title=File:" + name + "&action=raw")
    ca = "/root/.ccr/ca-bundle.crt"
    ctx = ssl.create_default_context(cafile=ca) if os.path.exists(ca) else None
    for wait in (0, 5, 20):
        time.sleep(0.6 + wait)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TheLamboIndexBuilder/1.0"})
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                return re.findall(r"\[\[Category:([^\]|]+)", r.read().decode("utf-8", "replace"))
        except Exception:
            continue
    return []


def main():
    arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    out_json, only, with_cats = arg("--json"), arg("--only"), "--cats" in sys.argv
    cars = json.load(open(os.path.join(ROOT, "data", "cars.json"), encoding="utf-8"))["cars"]
    titles = {}
    for name in ("flickr.json", "nonfree_images.json"):
        p = os.path.join(ROOT, "data", name)
        if os.path.exists(p):
            for entry in json.load(open(p, encoding="utf-8")).values():
                for im in (entry.get("images", []) if isinstance(entry, dict) else []):
                    titles[im["t"]] = im.get("title") or ""
    fam_names = {}
    for c in cars:
        f = c["family"]
        names = {norm(f), norm(FAMILY_WORDS.get(f, f))}
        if f in ("350", "400"):                      # bare numbers: only "350 gt", "400 gt"
            names = {norm(f) + " gt"}
        fam_names[f] = names
    by_family = collections.defaultdict(list)
    for c in cars:
        by_family[c["family"]].append(c)
    where = collections.defaultdict(list)
    for c in cars:
        for im in c["imgs"]:
            where[im["t"]].append(c["id"])

    flagged, n = collections.OrderedDict(), 0
    for c in cars:
        if only and c["id"] not in only.split(","):
            continue
        own_fam = fam_names[c["family"]]
        own_words = words(c["name"]) | {w for x in own_fam for w in x.split()}
        sib_words = set()
        for s in by_family[c["family"]]:
            if s["id"] != c["id"]:
                sib_words |= words(s["name"]) - own_words - STOP
        sib_words = {w for w in sib_words if len(w) >= 2 and not w.isdigit() or len(w) >= 3}
        for i, im in enumerate(c["imgs"]):
            n += 1
            t = im["t"]
            text = t.rsplit(".", 1)[0] if not t.startswith("flickr:") else titles.get(t, "")
            tn = norm(text)
            why = []
            if len(where[t]) > 1:
                why.append("dup:" + "+".join(x for x in where[t] if x != c["id"]))
            others = [f for f, ns in fam_names.items() if f != c["family"] and any(has(tn, x) for x in ns)]
            if others and not any(has(tn, x) for x in own_fam):
                why.append("family:" + "+".join(others))
            vw = sorted(w for w in sib_words if has(tn, w))
            if vw:
                why.append("version:" + "+".join(vw))
            if with_cats and "n" in im:
                for cat in commons_cats(im["n"]):
                    cn = norm(cat)
                    if not cn.startswith("lamborghini") and "lamborghini" not in cn:
                        continue
                    of = [f for f, ns in fam_names.items() if f != c["family"] and any(has(cn, x) for x in ns)]
                    cw = sorted(w for w in sib_words if has(cn, w))
                    if of or cw:
                        why.append("cats:" + cat.replace(" ", "_"))
            if why:
                flagged.setdefault(c["id"], []).append((i, im, why, text))
    total = sum(len(v) for v in flagged.values())
    for cid, rows in flagged.items():
        for i, im, why, text in rows:
            print(f"{cid}\t{i + 1}\t{' '.join(why)}\t{text[:90]}")
    print(f"checked {n} photos; flagged {total} on {len(flagged)} cars", file=sys.stderr)
    if out_json:
        json.dump({cid: {"images": [im for _, im, _, _ in rows]} for cid, rows in flagged.items()},
                  open(out_json, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()

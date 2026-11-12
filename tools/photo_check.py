#!/usr/bin/env python3
"""Flag photos that may be on the wrong car page, for checking by eye (CLAUDE.md, Photos).

Reads data/cars.json (the photos each page shows, after drops) and the Flickr titles. Flags:
  dup     the same photo on two or more cars
  family  the title names another family and not the car's own
  version the title names a word of a sibling car's name (same family) that this car's name lacks
Prints one line per flagged photo; with --json FILE also writes {car id: {"images": [records]}}
for tools/review_sheet.py. No network. Flags are hints: decide by eye, then drop or move.

Usage: python3 tools/photo_check.py [--json flagged.json]
"""
import collections, json, os, re, sys, unicodedata

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


def main():
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
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
            if why:
                flagged.setdefault(c["id"], []).append((i, im, why, text))
    total = sum(len(v) for v in flagged.values())
    for cid, rows in flagged.items():
        for i, im, why, text in rows:
            print(f"{cid}\t{i + 1}\t{' '.join(why)}\t{text[:90]}")
    print(f"checked {n} photos on {len(cars)} cars; flagged {total} on {len(flagged)} cars", file=sys.stderr)
    if out_json:
        json.dump({cid: {"images": [im for _, im, _, _ in rows]} for cid, rows in flagged.items()},
                  open(out_json, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()

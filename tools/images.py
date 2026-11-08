#!/usr/bin/env python3
"""Pick the best freely licensed photos for every car in catalog.py from Wikimedia Commons.

Writes data/images.json: {car_id: {"source": ..., "images": [...]}} with author and
licence for each photo, so the site can credit every image. Photos are not downloaded;
the site loads them from Wikimedia at standard thumbnail widths.

Usage: python3 tools/images.py [--only id,id] [--out data/images.json]
"""
import argparse, json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from catalog import CARS

API = "https://commons.wikimedia.org/w/api.php"
UA = "TheLamboIndexBuilder/1.0 (personal non-commercial index; polite single-threaded)"
CA = "/root/.ccr/ca-bundle.crt"
SPACING = 0.6   # seconds between requests
MAX_IMAGES = 10

BAD = re.compile(
    r"interior|innenraum|interieur|cockpit|dashboard|armaturen|\bdash\b|\bseats?\b|steering|lenkrad|"
    r"\bengines?\b|\bmotor\b|moteur|engine ?bay|\bbadges?\b|\blogo|emblem|\bwheels?\b|\brims?\b|felge|"
    r"\btyres?\b|\btires?\b|caliper|headlight|taillight|\blamps?\b|\bdetail|close.?up|\bchassis\b|"
    r"\bframe\b|schematic|drawing|sketch|blueprint|diecast|die.?cast|model ?car|scale ?model|modell|"
    r"\b1[ _:/-](?:8|10|12|18|24|43|64|87)\b|\blego\b|hot ?wheels|bburago|maisto|kyosho|autoart|"
    r"\btoy\b|poster|brochure|\bstamp|plaque|\bkeys?\b|exhaust|gauge|speedo|signature|"
    r"door ?handle|\bmirror|crash|wreck|damaged|burn|accident|\bsimulat|render|screenshot|"
    r"gran ?turismo ?sport|\bgts\b screenshot|\bcutaway|\bx-?ray|\bshifter|gear ?lever|\bpedal",
    re.I)
SOFT = re.compile(r"\brear\b|\bheck\b|\bback\b|\btail\b|\bside\b|seitenansicht|\bblur", re.I)
STOP = {"lamborghini", "the", "of", "and", "prototype", "concept", "edition", "car", "series", "s", "i",
        "ii", "iii", "4", "2", "de", "la", "le"}

_last = [0.0]


def api(params, tries=6):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        wait = SPACING - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            import ssl
            ctx = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None
            with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
                body = r.read()
            data = json.loads(body)
            if "error" in data and data["error"].get("code") == "maxlag":
                time.sleep(5 * (i + 1))
                continue
            return data
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After")
            time.sleep(float(ra) if ra and ra.isdigit() else 4 * (i + 1))
        except Exception:
            time.sleep(4 * (i + 1))
    print(f"  ! giving up on {params.get('gcmtitle') or params.get('srsearch') or params.get('titles')}", file=sys.stderr)
    return {}


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


IIPROP = dict(prop="imageinfo", iiprop="url|size|mime|extmetadata",
              iiextmetadatafilter="Artist|LicenseShortName|LicenseUrl|DateTimeOriginal")


def pages_to_files(data):
    out = []
    for p in (data.get("query") or {}).get("pages", []):
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
            continue
        out.append((p["title"], ii))
    return out


PAGE = "https://commons.wikimedia.org/wiki/"


def fetch_html(url, tries=5):
    for i in range(tries):
        wait = SPACING - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            import ssl
            ctx = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            ra = e.headers.get("Retry-After")
            time.sleep(float(ra) if ra and ra.isdigit() else 6 * (i + 1))
        except Exception:
            time.sleep(6 * (i + 1))
    return ""


def category_page(cat, pages=2):
    """Files (title, info) and subcategories listed on a Commons category page."""
    files, subs = [], []
    url = PAGE + "Category:" + urllib.parse.quote(cat.replace(" ", "_"))
    for _ in range(pages):
        s = fetch_html(url)
        if not s or 'class="noarticletext' in s:
            break
        m = re.search(r'<div id="mw-subcategories">(.*?)</div>\s*</div>\s*</div>', s, re.S)
        if m and not subs:
            subs = [urllib.parse.unquote(x).replace("_", " ") for x in re.findall(r'href="/wiki/Category:([^"#?]+)"', m.group(1))]
        for box in re.findall(r'<li class="gallerybox".*?</li>\s*(?=<li class="gallerybox"|</ul>)', s, re.S):
            name = re.search(r'href="/wiki/File:([^"]+)"', box)
            dims = re.search(r'([\d,]+)\s*(?:×|&#215;|x)\s*([\d,]+)', html_unescape(box))
            img = re.search(r'/thumb/([0-9a-f]/[0-9a-f]{2})/([^/]+)/', box) or re.search(r'/commons/([0-9a-f]/[0-9a-f]{2})/([^/"?]+)', box)
            if not (name and dims and img):
                continue
            title = "File:" + urllib.parse.unquote(name.group(1)).replace("_", " ")
            ext = title.rsplit(".", 1)[-1].lower()
            if ext not in ("jpg", "jpeg", "png", "webp"):
                continue
            files.append((title, {"width": int(dims.group(1).replace(",", "")), "height": int(dims.group(2).replace(",", "")),
                                  "hash": img.group(1), "enc": img.group(2)}))
        nxt = re.search(r'href="([^"]*filefrom=[^"]*)"[^>]*>next page', s)
        if not nxt:
            break
        url = "https://commons.wikimedia.org" + html_unescape(nxt.group(1))
    return files, subs


def html_unescape(t):
    import html as _h
    return _h.unescape(t)


LIC = [(r"cc-by-sa-(\d\.\d)", "CC BY-SA {}", "https://creativecommons.org/licenses/by-sa/{}/"),
       (r"cc-by-(\d\.\d)", "CC BY {}", "https://creativecommons.org/licenses/by/{}/"),
       (r"cc-zero|cc0", "CC0", "https://creativecommons.org/publicdomain/zero/1.0/"),
       (r"pd-|public ?domain", "Public domain", ""),
       (r"gfdl", "GFDL", "https://www.gnu.org/licenses/fdl-1.3.html"),
       (r"\bfal\b|free art", "Free Art License", "https://artlibre.org/licence/lal/en/")]
QUOTES = re.compile("'{2,}")


def wiki_text_to_plain(t):
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\]", "", t)
    t = re.sub(r"\{\{\s*(?:Creator|User):([^|}]+)[^}]*\}\}", r"\1", t, flags=re.I)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = QUOTES.sub("", re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\s+", " ", t).strip(" ,;-")


def raw_credit(title):
    txt = fetch_html("https://commons.wikimedia.org/w/index.php?" + urllib.parse.urlencode({"title": title, "action": "raw"}))
    if not txt:
        return None
    m = re.search(r"^\s*\|\s*(?:author|photographer|artist)\s*=\s*(.+)$", txt, re.I | re.M)
    author = wiki_text_to_plain(m.group(1)) if m else ""
    low = txt.lower()
    lic, url = "", ""
    for pat, name, u in LIC:
        mm = re.search(r"\{\{[^}]*?(" + pat + ")", low)
        if mm:
            ver = mm.group(2) if mm.re.groups >= 2 and mm.group(2) else ""
            lic, url = name.format(ver).strip(), u.format(ver)
            break
    return (author[:90] or "Unknown author", lic, url)


def credits(titles, on_progress=None):
    out = {}
    for i, t in enumerate(titles, 1):
        r = raw_credit(t)
        if r:
            out[t] = r
        if i % 50 == 0:
            print(f"  credits {i}/{len(titles)}", flush=True)
            if on_progress:
                on_progress(out)
    return out


def credits_via_api(titles):
    """Author and licence for chosen files, 50 per API call; tolerant of rate limits."""
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        data = api(dict(titles="|".join(batch), prop="imageinfo", iiprop="extmetadata",
                        iiextmetadatafilter="Artist|LicenseShortName|LicenseUrl"), tries=8)
        for p in (data.get("query") or {}).get("pages", []):
            em = ((p.get("imageinfo") or [{}])[0]).get("extmetadata") or {}
            out[p["title"]] = (clean_artist((em.get("Artist") or {}).get("value")),
                               (em.get("LicenseShortName") or {}).get("value", ""),
                               (em.get("LicenseUrl") or {}).get("value", ""))
        print(f"  credits {min(i + 50, len(titles))}/{len(titles)} ({len(out)} found)", flush=True)
    return out


def variant_phrase(car):
    """Distinctive words of a variant name; single letters join the previous word (LP400 S -> lp400s)."""
    fam = set(norm(car["family"]).split()) | set(norm(FAMILY_WORDS.get(car["family"], "")).split())
    words = []
    for w in norm(car["name"]).split():
        if w in fam or w in ("lamborghini", "the", "of", "and", "edition", "car", "series", "de", "la", "le"):
            continue
        if len(w) == 1 and w.isalpha() and words:
            words[-1] += w
        elif w not in ("4", "2", "prototype", "concept"):
            words.append(w)
    return words


FAMILY_WORDS = {"Murcielago": "Murciélago", "Huracan": "Huracán", "Reventon": "Reventón", "Sian": "Sián",
                "350": "350 GT", "400": "400 GT", "Autentica": "Auténtica", "Cala": "Calà"}


def code_hit(code_words, spaced, compact):
    """True when a variant's words appear in a file name (short codes need word boundaries)."""
    if not code_words:
        return False
    joined = "".join(code_words)
    if len(joined) >= 4:
        return joined in compact
    return re.search(r"\b" + r"\s?".join(map(re.escape, joined)) + r"\b", spaced) is not None


def score(title, ii, own, siblings, need_own, minw=1000):
    name = title.split(":", 1)[1].rsplit(".", 1)[0]
    spaced = norm(name)
    compact = spaced.replace(" ", "")
    if BAD.search(name) or BAD.search(spaced):
        return None
    w, h = ii.get("width", 0), ii.get("height", 0)
    if w < minw or h < minw * 0.48:
        return None
    r = w / h
    if r < 1.0 or r > 2.9:
        return None
    own_hit = code_hit(own, spaced, compact) or any(
        code_hit([w], spaced, compact) for w in own if len(w) >= 3 and not w.isdigit())
    if need_own and own:
        distinct = [x for x in own if len(x) >= 3 and not x.isdigit()]
        ok = all(code_hit([x], spaced, compact) for x in distinct) if distinct else code_hit(own, spaced, compact)
        if not ok:
            return None
    s = min(math.log2(max(w * h / 1e6, 1)), 4.0)
    s += 2.0 if 1.3 <= r <= 1.85 else 1.0 if 1.15 <= r <= 2.3 else 0
    if own_hit:
        s += 2.5
    for sib in siblings:
        if not sib or set(sib) <= set(own):
            continue
        if code_hit(sib, spaced, compact):
            s -= 3.0
            break
    if SOFT.search(spaced):
        s -= 1.0
    return s


def clean_artist(html):
    t = re.sub(r"<[^>]+>", " ", html or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:90] + ("…" if len(t) > 90 else "") if t else "Unknown author"


def record(title, ii):
    return {"t": title.split(":", 1)[1], "h": ii["hash"], "n": ii["enc"], "w": ii["width"], "ht": ii["height"],
            "a": "", "l": "", "lu": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--credits-only", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "images.json"))
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    out = json.load(open(a.out)) if os.path.exists(a.out) else {}
    used_heroes = {v["images"][0]["t"] for k, v in out.items() if v.get("images") and k not in only}
    by_family = {}
    for c in CARS:
        by_family.setdefault(c["family"], []).append(c)

    for c in ([] if a.credits_only else CARS):
        if only and c["id"] not in only:
            continue
        if not only and c["id"] in out:
            continue
        own = variant_phrase(c)
        own_req = own or [w for w in norm(c["name"]).split() if len(w) >= 3 and w != "lamborghini"]
        sibs = [variant_phrase(s) for s in by_family[c["family"]] if s is not c]
        cands, source = {}, None
        for i, cat in enumerate(c["cats"]):
            files, subs = category_page(cat)
            fallback = i > 0
            got = 0
            for t, ii in files:
                s_ = score(t, ii, own_req if fallback else own, sibs, need_own=fallback)
                if s_ is not None and t not in cands:
                    cands[t] = (s_, ii); got += 1
            if got < 8 and i == 0:
                for sc in subs[:6]:
                    for t, ii in category_page(sc, pages=1)[0]:
                        s_ = score(t, ii, own, sibs, need_own=False)
                        if s_ is not None and t not in cands:
                            cands[t] = (s_ - 0.3, ii); got += 1
            if got:
                source = source or "Category:" + cat
            if len(cands) >= 6:
                break
        if not cands:
            for i, cat in enumerate(c["cats"]):
                for t, ii in category_page(cat, pages=1)[0]:
                    s_ = score(t, ii, own_req if i > 0 else own, sibs, need_own=i > 0, minw=600)
                    if s_ is not None:
                        cands[t] = (s_ - 1.0, ii)
                if cands:
                    source = "Category:" + cat + " (smaller photos)"
                    break
        ranked = sorted(cands.items(), key=lambda kv: -kv[1][0])
        hero = next((kv for kv in ranked if kv[0] not in used_heroes), ranked[0] if ranked else None)
        chosen = ([hero] if hero else []) + [kv for kv in ranked if hero is None or kv[0] != hero[0]][: MAX_IMAGES - 1]
        imgs = [r for r in (record(t, ii) for t, (s, ii) in chosen) if r]
        if imgs:
            used_heroes.add(imgs[0]["t"])
        out[c["id"]] = {"source": source, "images": imgs}
        print(f"{c['id']:<34} {len(imgs):>2} photos  {source or '-'}", flush=True)
        with open(a.out, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=0)
    todo = sorted({"File:" + im["t"] for v in out.values() for im in v.get("images", []) if not im.get("l")})
    def apply(cr):
        for v in out.values():
            for im in v.get("images", []):
                got = cr.get("File:" + im["t"])
                if got:
                    im["a"], im["l"], im["lu"] = got
        with open(a.out + ".tmp", "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=0)
        os.replace(a.out + ".tmp", a.out)
    if todo:
        apply(credits(todo, on_progress=apply))
    missing = [c["id"] for c in CARS if not out.get(c["id"], {}).get("images")]
    print(f"done: {sum(1 for c in CARS if out.get(c['id'], {}).get('images'))}/{len(CARS)} cars have photos; missing: {missing}")


if __name__ == "__main__":
    main()

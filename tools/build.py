#!/usr/bin/env python3
"""Build The Lambo Index as one HTML file: catalog.py + data/images.json + src/ -> index.html"""
import base64, datetime, hashlib, html, json, math, os, re, sys
from html.parser import HTMLParser
from urllib.parse import quote, urlsplit
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from catalog import CARS, EXTRA_DEBUTS, FAMILY_NAME, NOT_DEBUTS, PERF
BRAND = "Lamborghini"   # room for more brands later: one page per brand from the same tools
SITE = "https://wam090.github.io/the-lambo-index/"   # the live site: canonical URLs, sitemap, Open Graph
# Every photo, licence and source URL must be https on one of these hosts, or the build fails.
# Add a host only for a real new source (security review, 2026-11-10).
URL_HOSTS = {
    "p": {"www.flickr.com"},                                        # source page of a Flickr or press photo
    "sz": {"live.staticflickr.com"},                                # Flickr image sizes
    "lu": {"creativecommons.org", "www.gnu.org", "artlibre.org",    # licence pages
           "commons.wikimedia.org", "www.flickr.com", "www.usa.gov"},
}
IMG_HOSTS = "https://thumb.wikimedia.org https://upload.wikimedia.org https://live.staticflickr.com https://thelamboindex.goatcounter.com"  # last: visit-count pixel (2026-11-12)

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
bad = []
for c in cars:
    for im in c["imgs"]:
        for field, url in [("p", im.get("p")), ("lu", im.get("lu"))] + [("sz", s[1]) for s in im.get("sz", [])]:
            u = urlsplit(url or "")
            if url and (u.scheme != "https" or u.hostname not in URL_HOSTS[field]):
                bad.append(f"{c['id']} {field}: {url}")
        if "h" in im and not re.fullmatch(r"[0-9a-f]/[0-9a-f]{2}", im["h"]):
            bad.append(f"{c['id']} h: {im['h']}")
if bad:   # explicit checks, not assert: python3 -O would skip those
    sys.exit("URLs outside URL_HOSTS in build.py:\n" + "\n".join(bad))
payload = {"brand": BRAND, "generated": datetime.date.today().isoformat(), "famNames": FAMILY_NAME, "cars": cars}
with open(os.path.join(ROOT, "data", "cars.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
tpl = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
app = open(os.path.join(ROOT, "src", "app.js"), encoding="utf-8").read()
if "</script" in app.lower():
    sys.exit("app.js must not contain a closing script tag")
if "\r" in app:
    sys.exit("app.js must use LF line endings (the CSP hash is taken over it as written)")
# every "<" escaped: no data can close the script element or open a comment inside it
data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
app_hash = base64.b64encode(hashlib.sha256(app.encode("utf-8")).digest()).decode()
csp = (f"default-src 'none'; script-src 'sha256-{app_hash}'; style-src 'unsafe-inline'; font-src 'self'; "
       f"img-src {IMG_HOSTS} data:; base-uri 'none'; form-action 'none'")
# one pass: a placeholder name inside the data (say, a scraped credit) is never substituted again
page = re.sub(r"__LI_(CSP|DATA|APP|SITE)__", lambda m: {"CSP": csp, "DATA": data, "APP": app, "SITE": SITE}[m.group(1)], tpl)
tags = re.findall(r"<script\b[^>]*>", page, re.I)
if len(tags) != 2 or any(re.search(r"\bsrc\s*=", t, re.I) for t in tags):
    sys.exit(f"expected 2 inline scripts, got {tags}")
out = os.path.join(ROOT, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(page)

# ---------- Static car pages for search engines (design: tools/STATIC_PAGES.md; Cyber, 2026-11-22) ----------
# One page per car at m/<id>/, an index of all cars at m/, sitemap.xml and the IndexNow key file.
# No JavaScript: the pages are checked below and fail the build on anything outside the rules.
# Changing PAGE_CSP or the markup checks needs Cyber's review.
INDEXNOW_KEY = "c1856620fb371faad479a07e2dcf9ac2"   # public by design: served as <key>.txt (IndexNow)
OG_LICENCES = re.compile(r"Public domain|CC0|CC BY(-SA)? \d\.\d")   # og:image licences, fullmatch; no NC until the user decides
PAGE_CSP = (f"default-src 'none'; style-src {SITE}src/page.css; font-src {SITE}fonts/; "
            f"img-src https://thumb.wikimedia.org https://live.staticflickr.com https://thelamboindex.goatcounter.com "
            f"{SITE}favicon.svg; base-uri 'none'; form-action 'none'")
FORBIDDEN_TAGS = {"script", "style", "iframe", "object", "embed", "form", "base", "frame", "frameset",
                  "svg", "math", "template", "noscript", "applet", "portal"}
URL_ATTRS = {"href", "src"}
BAD_ATTRS = {"style", "srcset", "action", "formaction", "background", "poster", "ping", "xlink:href"}
LINK_RELS = {"stylesheet", "canonical", "icon"}
IMG_SRC_HOSTS = {"thumb.wikimedia.org", "live.staticflickr.com", "thelamboindex.goatcounter.com"}
PAGE_HOSTS = ({"wam090.github.io", "commons.wikimedia.org", "en.wikipedia.org", "github.com"} | IMG_SRC_HOSTS
              | URL_HOSTS["p"] | URL_HOSTS["lu"])
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
NOTES = ("Unofficial fan site, not affiliated with Automobili Lamborghini",
         "Photos credited to their authors, under their licences", "Visits counted anonymously, no cookies")
THUMB = "https://thumb.wikimedia.org/wikipedia/commons/thumb/"
STD = (330, 500, 960, 1280, 1920, 3840)   # the only widths Wikimedia serves thumbnails at
COUNT_URL = "https://thelamboindex.goatcounter.com/count"
REPORT = "https://github.com/wam090/the-lambo-index/issues/new"


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def jround(x):   # JavaScript's Math.round (half up), so the pages show what the app shows
    return math.floor(x + 0.5)


def hp(cv): return jround(cv * 0.98632)
def kw(cv): return jround(cv * 0.7355)
def fmt(n): return f"{n:,}"
def fam_name(f): return FAMILY_NAME.get(f, f)


def years_long(c):
    return f"{c['year']}–present" if c["end"] == 0 else f"{c['year']}–{c['end']}" if c["end"] and c["end"] != c["year"] else f"{c['year']}"


def img_url(im, want):
    """(url, width) as the app picks it: Flickr's fixed sizes, or a standard Commons thumbnail."""
    if im.get("sz"):
        s = next((s for s in im["sz"] if s[0] >= want), im["sz"][-1])
        return s[1], s[0]
    fits = [s for s in STD if s < im["w"]]   # thumbnails must be narrower than the original
    w = next((s for s in fits if s >= want), fits[-1] if fits else None)
    return (f"{THUMB}{im['h']}/{im['n']}/{w}px-{im['n']}", w) if w else (None, None)


def dims(im, w):
    """Width and height of the size picked by img_url (Flickr sizes are the longest edge)."""
    if im.get("sz") and im["ht"] > im["w"]:
        return jround(w * im["w"] / im["ht"]), w
    return w, jround(w * im["ht"] / im["w"])


def file_page(im): return im.get("p") or f"https://commons.wikimedia.org/wiki/File:{im['n']}"
def source(im): return "Flickr" if im.get("src") in ("flickr", "press") else "Wikimedia Commons"
def ext_link(url, inner): return f'<a href="{esc(url)}">{inner}</a>' if (url or "").lower().startswith("https://") else inner


def credit_html(im):   # the app's creditHTML
    who = ext_link(file_page(im), esc(im.get("a") or f"{source(im)} contributor"))
    lic = f" · {ext_link(im.get('lu'), esc(im['l']))}" if im.get("l") else ""
    return f"{'Press photo' if im.get('src') == 'press' else 'Photo'}: {who}{lic} · {source(im)}"


def report_html(c, im):   # the app's reportHTML; the query is URL-encoded, then the whole URL escaped
    body = (f"Car: {c['name']}\nPage: {SITE}m/{c['id']}/\nPhoto: {file_page(im)}\n\n"
            "What is wrong with this photo (wrong car, wrong credit, should be removed)?")
    title = quote("Photo report: " + c["name"], safe="")
    url = f"{REPORT}?title={title}&body={quote(body, safe='')}"
    return f" · {ext_link(url, 'Report a photo')}"


def pixel(path, title):
    url = f"{COUNT_URL}?p={quote(path)}&t={quote(title, safe='')}"
    return f'<img class="px" src="{esc(url)}" alt="" width="1" height="1">'


def og_photo(c):
    return next((im for im in c["imgs"] if OG_LICENCES.fullmatch(im.get("l") or "") and not im["t"].startswith("nonfree:")), None)


def shorten(s, n=160):
    return s if len(s) <= n else s[:s.rfind(" ", 0, n - 1)].rstrip(" ,;.") + "…"


def head(title, desc, canon, rel, og_title, og_desc, og_img=None):
    tags = [f'<meta property="og:{k}" content="{esc(v)}">' for k, v in
            (("type", "website"), ("site_name", "The Lambo Index"), ("title", og_title), ("description", og_desc), ("url", canon))]
    if og_img:
        tags += [f'<meta property="og:image{k}" content="{esc(v)}">' for k, v in og_img]
    tags.append(f'<meta name="twitter:card" content="{"summary_large_image" if og_img else "summary"}">')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{esc(PAGE_CSP)}">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canon)}">
<link rel="stylesheet" href="{rel}src/page.css">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0c0b0a">
{chr(10).join(tags)}
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="{rel}"><img src="{rel}favicon.svg" alt="" width="24" height="24">The <b>Lambo</b> Index</a>{'' if rel == '../' else '<nav><a href="../">All cars</a></nav>'}</div></header>
"""


def foot(path, title):
    notes = "".join(f"<li>{esc(n)}</li>" for n in NOTES)
    return f'<footer class="foot"><div class="wrap"><ul class="notes">{notes}</ul></div></footer>\n{pixel(path, title)}\n</body>\n</html>\n'


def car_page(c, family):
    name, cid, n = c["name"], c["id"], len(c["imgs"])
    yrs = years_long(c)
    title = f"Lamborghini {name} ({yrs}) · The Lambo Index"
    canon = f"{SITE}m/{cid}/"
    facts = f"{c['kind']}, {yrs}" + (f", {c['engine']}" if c["engine"] else "") + (f", {fmt(hp(c['cv']))} hp" if c["cv"] else "")
    if c["units"]:
        facts += ", one of one" if c["units"] == 1 else f", {fmt(c['units'])} built"
    note = (c["note"] or "").strip()
    desc = shorten(f"{note}{'' if not note or note[-1] in '.!?' else '.'} {facts}.".strip())
    og = og_photo(c)
    og_img, og_desc = None, desc
    if og:
        u, w = img_url(og, 1280)
        if u:
            ow, oh = dims(og, w)
            og_img = (("", u), (":width", ow), (":height", oh), (":alt", f"Lamborghini {name}"))
            og_desc = f"{desc} Photo: {og.get('a') or source(og) + ' contributor'}, {og['l']}."
    out = [head(title, desc, canon, "../../", f"Lamborghini {name} ({yrs})", og_desc, og_img)]
    lead = c["imgs"][0] if c["imgs"] else None
    u, w = img_url(lead, 960) if lead else (None, None)
    if u:
        pw, ph = dims(lead, w)
        photo = (f'<figure class="photo"><a href="../../#/m/{cid}"><img src="{esc(u)}" width="{pw}" height="{ph}" '
                 f'alt="{esc(f"Lamborghini {name}")}" fetchpriority="high"></a>'
                 f'<figcaption>{credit_html(lead)}{report_html(c, lead)}</figcaption></figure>')
    else:
        photo = '<div class="empty">No freely licensed photo yet</div>'
    power = (f'<dt>Power</dt><dd><span class="mono">{fmt(hp(c["cv"]))} hp</span> <span class="hint">{fmt(kw(c["cv"]))} kW</span></dd>'
             if c["cv"] else "")
    one = ' <span class="hint">one of one</span>' if c["units"] == 1 else ""
    built = f'<span class="mono">{fmt(c["units"])}</span>{one}' if c["units"] else '<span class="hint">not reliably known</span>'
    wiki_url = "https://en.wikipedia.org/wiki/" + quote((c["wiki"] or "").replace(" ", "_"), safe="")
    wiki = f' <a class="btn" href="{esc(wiki_url)}">Read on Wikipedia</a>' if c["wiki"] else ""
    out.append(f"""<main class="wrap">
<div class="car">
<div>{photo}</div>
<div>
<p class="eyebrow">{esc(yrs)} · {esc(c['kind'])}</p>
<h1>{esc(name)}</h1>
<p class="note">{esc(note)}</p>
<dl class="facts">
<dt>Years</dt><dd>{esc(yrs)}</dd>
<dt>Type</dt><dd>{esc(c['kind'])}</dd>
<dt>Body</dt><dd>{esc(c['body'])}</dd>
<dt>Engine</dt><dd>{esc(c['engine'])}</dd>
{power}
<dt>Built</dt><dd>{built}</dd>
<dt>Designer</dt><dd>{esc(c['designer'] or 'Not credited')}</dd>
<dt>Family</dt><dd>{esc(fam_name(c['family']))} <span class="hint">{fmt(len(family))} in the index</span></dd>
</dl>
<p class="actions"><a class="btn primary" href="../../#/m/{cid}">{f'All {n} photos in The Lambo Index' if n > 1 else 'Open in The Lambo Index'}</a>{wiki}</p>
</div>
</div>
""")
    if len(family) > 1:
        items = "".join(f'<li aria-current="page"><b>{esc(x["name"])}</b><span>{esc(years_long(x))}</span></li>' if x is c else
                        f'<li><a href="../{x["id"]}/">{esc(x["name"])}</a><span>{esc(years_long(x))}</span></li>' for x in family)
        out.append(f'<nav class="list" aria-label="The {esc(fam_name(c["family"]))} family"><h2>The {esc(fam_name(c["family"]))} family</h2><ul>{items}</ul></nav>\n')
    out.append("</main>\n" + foot(f"/m/{cid}/", title))
    return "".join(out)


def all_page(groups):
    title = "All cars · The Lambo Index"
    desc = f"Every Lamborghini in The Lambo Index, by family: {len(cars)} cars, real or concept, with photos and specifications."
    secs = "".join(f'<section class="list"><h2>{esc(fam_name(f))}</h2><ul>' +
                   "".join(f'<li><a href="{x["id"]}/">{esc(x["name"])}</a><span>{esc(years_long(x))}</span></li>' for x in fam) +
                   "</ul></section>\n" for f, fam in groups)
    return (head(title, desc, f"{SITE}m/", "../", "All cars · The Lambo Index", desc) +
            f'<main class="wrap">\n<h1>All cars</h1>\n<p class="lead">{fmt(len(cars))} cars by family. '
            f'<a href="../">Open The Lambo Index</a> to search, filter and compare.</p>\n{secs}</main>\n' + foot("/m/", title))


class PageCheck(HTMLParser):
    """Fails on anything a static page must not hold (case and spacing do not matter: the parser normalises)."""
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.name, self.bad = name, []

    def handle_starttag(self, tag, attrs): self.tag(tag, attrs)
    def handle_startendtag(self, tag, attrs): self.tag(tag, attrs)

    def tag(self, tag, attrs):
        a = dict(attrs)
        if tag in FORBIDDEN_TAGS:
            self.bad.append(f"<{tag}>")
        for k, v in attrs:
            if k.startswith("on") or k in BAD_ATTRS:
                self.bad.append(f"<{tag} {k}=>")
        if tag == "link" and (a.get("rel") or "").lower() not in LINK_RELS:
            self.bad.append(f"<link rel={a.get('rel')}>")
        if tag == "meta" and "http-equiv" in a and (a["http-equiv"] or "").lower() != "content-security-policy":
            self.bad.append(f"<meta http-equiv={a['http-equiv']}>")
        urls = [(k, v) for k, v in attrs if k in URL_ATTRS]
        if tag == "meta" and (a.get("property") or "").lower() in ("og:url", "og:image"):
            urls.append(("content", a.get("content")))
        for k, v in urls:
            self.url(tag, k, v or "")

    def url(self, tag, k, v):
        s = urlsplit(v)
        if not (s.scheme or s.netloc or v.startswith(("/", "\\")) or "\\" in v or ":" in v.split("/")[0]):
            return   # relative, inside the site
        ok = (s.scheme == "https" and s.hostname in PAGE_HOSTS
              and (s.hostname != "wam090.github.io" or v.startswith(SITE))
              and (s.hostname != "github.com" or s.path == "/wam090/the-lambo-index/issues/new")
              and (tag != "img" or s.hostname in IMG_SRC_HOSTS))
        if not ok:
            self.bad.append(f"{tag} {k}={v[:80]}")


def page_problems(text):
    p = PageCheck("")
    p.feed(text)
    p.close()
    if re.search(r"<\s*/?\s*(script|style|iframe|object|embed|form|base)\b", text, re.I):
        p.bad.append("raw forbidden tag")
    for t in re.findall(r"<[^>]*>", text):
        if re.search(r"\s(on\w+|style)\s*=", t, re.I) or re.search(r"(javascript|data)\s*:", t, re.I):
            p.bad.append(f"raw attribute in {t[:80]}")
    return p.bad


def check_page(name, text):
    bad = page_problems(text)
    if bad:
        sys.exit(f"static page {name} breaks the page rules:\n- " + "\n- ".join(bad))


def out_path(cid=None, root=ROOT):
    """m/<id>/index.html or m/index.html, refused if outside <root>/m/ or reached through a symlink."""
    if cid is not None and not ID_RE.fullmatch(cid):
        sys.exit(f"car id {cid!r} is not a safe path (a-z, 0-9, single hyphens)")
    m, real_m = os.path.join(root, "m"), os.path.join(os.path.realpath(root), "m")
    parts = [m] + ([os.path.join(m, cid)] if cid else [])
    p = os.path.join(parts[-1], "index.html")
    if any(os.path.islink(x) for x in parts + [p]) or os.path.realpath(m) != real_m:
        sys.exit(f"refusing to write through a symlink: {p}")
    if not os.path.realpath(p).startswith(real_m + os.sep):
        sys.exit(f"refusing to write outside m/: {p}")
    return p


def self_test(good):
    """Runs on every build: each banned pattern must fail the page checks, bad ids and symlinks the
    path guard; the build stops if one gets through (Cyber, 2026-11-22)."""
    import tempfile
    a, img = '<a href="../x/">', '<img src="https://thumb.wikimedia.org/x.jpg" alt="">'
    bad_pages = {
        "script": "<SCRIPT >x</script>", "spaced script": "< script>x</script>", "style element": "<style>b{}</style>",
        "iframe": '<iframe src="../"></iframe>', "object": "<object></object>", "embed": "<embed>",
        "form": "<form></form>", "base": '<base href="https://evil.example/">', "svg": "<svg></svg>",
        "event handler": img.replace("<img", "<img ONERROR = x"), "style attribute": '<p style="color:red">x</p>',
        "srcset": img.replace("<img", '<img srcset="https://evil.example/x.jpg 2x"'),
        "meta refresh": '<meta http-equiv="refresh" content="0;url=https://evil.example/">',
        "link prefetch": '<link rel="prefetch" href="../x">',
        "javascript url": '<a href="javascript:alert(1)">x</a>', "entity javascript url": '<a href="&#106;avascript:alert(1)">x</a>',
        "data url": '<img src="data:image/svg+xml,x" alt="">', "http": '<a href="http://en.wikipedia.org/">x</a>',
        "other host": '<a href="https://evil.example/">x</a>', "other Pages site": '<a href="https://wam090.github.io/other/">x</a>',
        "root-relative": '<a href="/other-repo/">x</a>', "protocol-relative": '<a href="//evil.example/">x</a>',
        "image from a page host": '<img src="https://en.wikipedia.org/x.jpg" alt="">',
        "og:image elsewhere": '<meta property="og:image" content="https://evil.example/x.jpg">',
        "other github path": '<a href="https://github.com/someone/else">x</a>',
    }
    if page_problems(good):
        sys.exit("self-test: a good page fails the page checks: " + "; ".join(page_problems(good)))
    missed = [k for k, v in bad_pages.items() if not page_problems(good.replace("</main>", v + "</main>"))]
    for cid in ("../x", "a/b", "A", "x--y", "-x", "x-", "x.y", "", " x"):
        try:
            out_path(cid)
            missed.append(f"id {cid!r}")
        except SystemExit:
            pass
    with tempfile.TemporaryDirectory() as tmp:
        root, other = os.path.join(tmp, "repo"), os.path.join(tmp, "other")
        os.makedirs(root)
        os.makedirs(os.path.join(other, "x"))
        os.symlink(other, os.path.join(root, "m"))   # m/ itself a symlink
        try:
            out_path("x", root)
            missed.append("m/ as a symlink")
        except SystemExit:
            pass
        os.remove(os.path.join(root, "m"))
        os.makedirs(os.path.join(root, "m"))
        os.symlink(os.path.join(other, "x"), os.path.join(root, "m", "x"))   # m/<id>/ a symlink
        try:
            out_path("x", root)
            missed.append("m/<id>/ as a symlink")
        except SystemExit:
            pass
    if missed:
        sys.exit("self-test: the page checks let these through: " + ", ".join(missed))
    return len(bad_pages)


def root_path(name):
    p = os.path.join(ROOT, name)
    if os.path.islink(p) or os.path.dirname(os.path.realpath(p)) != os.path.realpath(ROOT):
        sys.exit(f"refusing to write through a symlink or outside the repo: {p}")
    return p


def write_if_changed(p, text):
    old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    if old == text:
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return True


if not re.fullmatch(r"[0-9a-f]{32}", INDEXNOW_KEY):
    sys.exit("INDEXNOW_KEY must be 32 hex characters")
bad_ids = [c["id"] for c in cars if not ID_RE.fullmatch(c["id"])]   # before any page is written or linked
if bad_ids:
    sys.exit(f"car ids not safe as paths (a-z, 0-9, single hyphens): {bad_ids}")
SITEMAP = root_path("sitemap.xml")
old_map = open(SITEMAP, encoding="utf-8").read() if os.path.exists(SITEMAP) else ""
old_mod = dict(re.findall(r"<loc>([^<]+)</loc><lastmod>(\d{4}-\d{2}-\d{2})</lastmod>", old_map))
today = payload["generated"]
order = {c["id"]: i for i, c in enumerate(cars)}
fams = {}
for c in sorted(cars, key=lambda c: (c["year"], order[c["id"]])):
    fams.setdefault(c["family"], []).append(c)
n_tests = self_test(car_page(cars[0], fams[cars[0]["family"]]))
lastmod, changed = {}, []
for c in cars:
    text = car_page(c, fams[c["family"]])
    check_page(f"m/{c['id']}/", text)
    loc = f"{SITE}m/{c['id']}/"
    if write_if_changed(out_path(c["id"]), text) or loc not in old_mod:
        changed.append(c["id"])
        lastmod[loc] = today
    else:
        lastmod[loc] = old_mod[loc]
text = all_page(list(fams.items()))
check_page("m/", text)
loc = f"{SITE}m/"
lastmod[loc] = today if write_if_changed(out_path(), text) or loc not in old_mod else old_mod[loc]
# a car that left the catalogue: delete only the page this build wrote for it (listed in its own sitemap)
ids = {c["id"] for c in cars}
for loc in old_mod:
    m = re.fullmatch(re.escape(SITE) + r"m/([^/]+)/", loc)
    if m and m.group(1) not in ids and ID_RE.fullmatch(m.group(1)):
        p = out_path(m.group(1))
        if os.path.isfile(p):
            os.remove(p)
        d = os.path.dirname(p)
        if os.path.isdir(d) and not os.listdir(d):   # the folder may be gone already (Cyber, 2026-11-22)
            os.rmdir(d)
        print(f"removed stale page m/{m.group(1)}/")
urls = [SITE, f"{SITE}m/"] + [f"{SITE}m/{c['id']}/" for c in cars]
lastmod[SITE] = max(lastmod.values())
write_if_changed(SITEMAP, '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                 "".join(f"<url><loc>{esc(u)}</loc><lastmod>{lastmod[u]}</lastmod></url>\n" for u in urls) + "</urlset>\n")
write_if_changed(root_path(f"{INDEXNOW_KEY}.txt"), INDEXNOW_KEY)

n_img = sum(len(c["imgs"]) for c in cars)
print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB): {len(cars)} cars, {n_img} photos, "
      f"{sum(1 for c in cars if not c['imgs'])} without photos")
print(f"wrote {len(cars)} car pages under m/ ({len(changed)} new or changed), m/, sitemap.xml ({len(urls)} URLs); "
      f"self-test: {n_tests} bad pages, 9 bad ids and 2 symlinks refused")

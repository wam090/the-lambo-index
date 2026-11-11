"""Check the Scout's monthly package and turn it into catalogue rows (tools/REFRESH.md, Dev).

The package is untrusted data written by a chat that read the open web (Cyber's spec, 2026-11-11).
This script never evaluates, executes or imports package text, never opens a URL from it and runs
no shell. It writes rows only as repr() of values that passed every check, verifies them with the
AST, then runs `python3 -I` on the edited catalogue. Any violation rejects the whole package.

  python3 tools/scout_import.py check  PKG.json   # validate only
  python3 tools/scout_import.py apply  PKG.json   # validate, then write rows to tools/catalog.py
  python3 tools/scout_import.py photos PKG.json   # after your own images.py/flickr.py runs: apply
                                                  # drop/hero picks found in those runs only
  python3 tools/scout_import.py report PKG.json   # Markdown for the PR body (package text fenced)
  python3 tools/scout_import.py hunt   PKG.json   # photo hunt: write the checked hints (see below)
  python3 tools/scout_import.py --self-test       # Cyber's hostile cases a-j on a scratch copy

Package ("version": 1): one UTF-8 JSON object of at most 64 KB, keys exactly as below at every level.
{
  "version": 1,
  "window": ["2026-11-01", "2026-12-01"],          # ISO dates searched, from <= to <= today
  "cars": [                                          # at most 20
    {"id": "temerario-gt3", "family": "Temerario", "name": "Temerario GT3", "kind": "Race car",
     "year": 2026, "end": 0, "body": "Coupé", "engine": "4.0 L twin-turbo V8", "eng": "V8",
     "cv": null, "units": null, "designer": "Lamborghini Centro Stile", "wiki": null,
     "note": "One line.", "cats": ["Lamborghini Temerario GT3"],
     "perf": null,                                   # Production/Limited series/One-off only:
                                                     # [top km/h, over?, 0-100 s or null]
     "sources": ["https://en.wikipedia.org/wiki/..."]}  # 1-5, hosts in SOURCE_HOSTS; never opened
  ],
  "photos": {"temerario-gt3": {"drop": ["Some photo.jpg", "flickr:123"], "hero": null}},
  "notes": "One line for the PR: teasers skipped, doubts.",
  "opened": ["https://en.wikipedia.org/wiki/Lamborghini", "https://www.evo.co.uk/lamborghini"],
                                                     # 2-30 pages read in full (not search snippets),
                                                     # hosts in SOURCE_HOSTS; every car source among them
  "unreachable": []                                  # SOURCE_HOSTS hosts that failed to load
}
"opened" must hold an en.wikipedia.org page and a page from one press host, unless that side is
listed in "unreachable" (Wikipedia, or every press host).
A car whose id already exists is a blank-fill: every field equals today's row except fields that are
None today (perf: only if the car has no PERF entry yet). New ids go at the end of CARS. A new family
is never a refresh: it touches src/app.js and tools/images.py, so it is a separate, normal PR.

Photo-hunt package (tools/REFRESH.md, "Photo hunt"): hints for cars that have too few photos. No
URLs, no photo data: only names this tool and the Dev's own runs look up on Commons and Flickr.
{
  "version": 1, "kind": "photo-hunt",
  "ids": ["sc20"],                                   # 1-10 existing car ids: those the fire text named
  "photos": {"sc20": {                               # one entry per id
    "cats":   ["Lamborghini SC20"],                  # 0-3 Commons categories (no "Category:"), each
                                                     # containing the car's name; they go first in cats
    "files":  ["Lamborghini SC20 Goodwood 2021.jpg"],# 0-10 Commons file titles (no "File:") outside
                                                     # those categories; this tool fetches and credits
                                                     # them, free licence only -> data/extra_images.json
    "flickr": ["Lamborghini SC20 Goodwood"],         # 0-5 Flickr search terms -> data/flickr_queries.json
    "hero": "flickr:123", "drop": [],                # picks, applied only if your own runs return them
    "why": ""}},                                     # one line; required when nothing was found
  "notes": ""
}
"""
import ast, atexit, datetime, json, os, re, shutil, subprocess, sys, tempfile, unicodedata, urllib.parse

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CATALOG = os.path.join(ROOT, "tools", "catalog.py")
HEROES = os.path.join(ROOT, "data", "heroes.json")
APP = os.path.join(ROOT, "src", "app.js")
MAX_BYTES = 64 * 1024
MAX_CARS = 20
FIELDS = ["id", "family", "name", "kind", "year", "end", "body", "engine", "eng", "cv", "units",
          "designer", "cats", "wiki", "note"]          # E(...) argument order in catalog.py
CAR_KEYS = set(FIELDS) | {"perf", "sources"}
TOP_KEYS = {"version", "window", "cars", "photos", "notes", "opened", "unreachable"}
PERF_KINDS = {"Production", "Limited series", "One-off"}
SOURCE_HOSTS = {"en.wikipedia.org", "www.autocar.co.uk", "www.caranddriver.com", "www.motor1.com",
                "www.topgear.com", "www.evo.co.uk", "www.carscoops.com"}
ID_RE = re.compile(r"[a-z0-9-]{2,40}")
FAMILY_RE = re.compile(r"[A-Za-z0-9 ]{2,30}")
TEXT_BAD = set("<>{}[]|\\`")
CAT_BAD = set("<>[]{}|#")
TEXT_BAD_WORDS = ("__li_", "javascript:", "http", "://", "www.")
INVISIBLE = {*range(0x200B, 0x2010), *range(0x202A, 0x202F), *range(0x2066, 0x206A), 0xFEFF}


class Bad(Exception):
    pass


def read_order(name):
    m = re.search(r"const %s = \[([^\]]*)\]" % name, open(APP, encoding="utf-8").read())
    return re.findall(r"'([^']*)'", m.group(1))


def one_line(v, where, limit, bad):
    if type(v) is not str or not 1 <= len(v) <= limit:
        raise Bad(f"{where}: must be a string of 1-{limit} characters")
    if unicodedata.normalize("NFC", v) != v:
        raise Bad(f"{where}: not NFC-normalised")
    for ch in v:
        cat = unicodedata.category(ch)
        if ch in bad or cat[0] == "C" or cat in ("Zl", "Zp") or ord(ch) in INVISIBLE:
            raise Bad(f"{where}: character U+{ord(ch):04X} not allowed")
    return v


def text(v, where, limit=200):
    one_line(v, where, limit, TEXT_BAD)
    low = v.lower()
    for w in TEXT_BAD_WORDS:
        if w in low:
            raise Bad(f"{where}: may not contain '{w}'")


def integer(v, where, lo, hi, none=True):
    if v is None and none:
        return
    if type(v) is not int or not lo <= v <= hi:        # type() is int: rejects True/False and floats
        raise Bad(f"{where}: must be an integer {lo}-{hi}" + (" or null" if none else ""))


def source(v, where):
    if type(v) is not str or len(v) > 300 or any(not 33 <= ord(c) <= 126 for c in v) or "`" in v:
        raise Bad(f"{where}: must be printable ASCII, at most 300 characters")
    try:
        u = urllib.parse.urlsplit(v)
        port, host = u.port, u.hostname
    except ValueError:
        raise Bad(f"{where}: not a valid URL")
    # netloc must be exactly the lower-case allowlisted host: no userinfo, port or upper case
    if u.scheme != "https" or port is not None or host not in SOURCE_HOSTS or u.netloc != host:
        raise Bad(f"{where}: must be https on one of {sorted(SOURCE_HOSTS)}")


def strict_keys(obj, keys, where):
    if type(obj) is not dict:
        raise Bad(f"{where}: must be an object")
    if set(obj) != keys:
        raise Bad(f"{where}: unexpected keys {sorted(set(obj) - keys)}, missing {sorted(keys - set(obj))}")


def load(path):
    if os.path.getsize(path) > MAX_BYTES:
        raise Bad(f"package larger than {MAX_BYTES} bytes")
    try:
        s = open(path, "rb").read().decode("utf-8")
    except UnicodeDecodeError:
        raise Bad("package is not UTF-8")

    def pairs(kv):
        keys = [k for k, _ in kv]
        if len(keys) != len(set(keys)):
            raise Bad(f"duplicate keys: {sorted({k for k in keys if keys.count(k) > 1})}")
        return dict(kv)

    def const(c):
        raise Bad(f"{c} is not allowed")

    def num(x):
        f = float(x)
        if f != f or f in (float("inf"), float("-inf")):
            raise Bad(f"number {x[:20]} is out of range")
        return f
    try:
        return json.loads(s, object_pairs_hook=pairs, parse_constant=const, parse_float=num)
    except ValueError as e:
        raise Bad(f"not valid JSON: {e}")


def load_catalog(path=CATALOG):
    """CARS and PERF read with the AST (literals, plus the module's shorthand string constants), so
    checking a package runs no code."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    names, cars, perf = {}, {}, {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            n = node.targets[0].id
            if isinstance(node.value, ast.Constant):
                names[n] = node.value.value
            elif n == "PERF":
                perf = ast.literal_eval(node.value)
            elif n == "CARS":
                for call in node.value.elts:
                    args = [names[a.id] if isinstance(a, ast.Name) else ast.literal_eval(a) for a in call.args]
                    row = dict(zip(FIELDS, args + [None] * (len(FIELDS) - len(args))))
                    for kw in call.keywords:      # e.g. wiki=..., note=...; fills there fail closed
                        row[kw.arg] = ast.literal_eval(kw.value)
                    if not isinstance(row["cats"], list):
                        row["cats"] = [row["cats"]]
                    row["note"] = row["note"] or ""
                    cars[row["id"]] = (row, call)
    return cars, perf


def validate(pkg, cat_path=CATALOG):
    cars, perf = load_catalog(cat_path)
    kinds, engs = read_order("KIND_ORDER"), read_order("ENG_ORDER")
    families = {r["family"] for r, _ in cars.values()}
    today = datetime.date.today()
    errs = []

    strict_keys(pkg, TOP_KEYS, "package")
    if type(pkg["version"]) is not int or pkg["version"] != 1:
        raise Bad("version must be 1")
    w = pkg["window"]
    try:
        if type(w) is not list or len(w) != 2 or not all(type(d) is str and len(d) == 10 for d in w):
            raise ValueError
        a, b = map(datetime.date.fromisoformat, w)
        if a > b or b > today:
            raise ValueError
    except ValueError:
        errs.append("window: two ISO dates, from <= to <= today")
    if pkg["notes"] != "":
        try:
            text(pkg["notes"], "notes", 300)
        except Bad as e:
            errs.append(str(e))
    opened, unreach = pkg["opened"], pkg["unreachable"]
    if type(opened) is not list or not 2 <= len(opened) <= 30 or len(set(map(str, opened))) != len(opened):
        errs.append("opened: 2-30 distinct pages read in full")
        opened = []
    else:
        good = []
        for j, u in enumerate(opened):
            try:
                source(u, f"opened[{j}]")
                good.append(u)
            except Bad as e:
                errs.append(str(e))
        opened = good
    if type(unreach) is not list or len(unreach) > len(SOURCE_HOSTS) or \
            any(type(h) is not str or h not in SOURCE_HOSTS for h in unreach) or len(set(unreach)) != len(unreach):
        errs.append(f"unreachable: distinct hosts from {sorted(SOURCE_HOSTS)}")
        unreach = []
    hosts = {urllib.parse.urlsplit(u).hostname for u in opened}     # only entries that passed source()
    press = SOURCE_HOSTS - {"en.wikipedia.org"}
    if "en.wikipedia.org" not in hosts and "en.wikipedia.org" not in unreach:
        errs.append("opened: no en.wikipedia.org page read, and Wikipedia not listed as unreachable")
    if not hosts & press and not press <= set(unreach):
        errs.append("opened: no press page read, and not every press host listed as unreachable")
    if type(pkg["cars"]) is not list or len(pkg["cars"]) > MAX_CARS:
        raise Bad(f"cars: a list of at most {MAX_CARS}")

    seen = set()
    for i, c in enumerate(pkg["cars"]):
        where = f"cars[{i}]"
        try:
            strict_keys(c, CAR_KEYS, where)
            if type(c["id"]) is not str or not ID_RE.fullmatch(c["id"]):
                raise Bad(f"{where}.id: must match ^[a-z0-9-]{{2,40}}$")
            if c["id"] in seen:
                raise Bad(f"{where}.id: twice in the package")
        except Bad as x:
            errs.append(str(x))
            continue
        seen.add(c["id"])
        where = f"car {c['id']}"
        e = []

        def chk(fn, *a):
            try:
                fn(*a)
            except Bad as x:
                e.append(str(x))
        if type(c["family"]) is not str or not FAMILY_RE.fullmatch(c["family"]):
            e.append(f"{where}.family: must match ^[A-Za-z0-9 ]{{2,30}}$")
        if c["kind"] not in kinds:
            e.append(f"{where}.kind: one of {kinds}")
        if c["eng"] not in engs:
            e.append(f"{where}.eng: one of {engs}")
        chk(integer, c["year"], f"{where}.year", 1963, today.year + 1, False)
        if type(c["end"]) is not int or c["end"] != 0:
            chk(integer, c["end"], f"{where}.end", c["year"] if type(c["year"]) is int else 1963, today.year + 1)
        chk(integer, c["cv"], f"{where}.cv", 50, 2500)
        chk(integer, c["units"], f"{where}.units", 1, 100000)
        for f in ("name", "body", "engine", "note"):
            chk(text, c[f], f"{where}.{f}")
        for f in ("designer", "wiki"):
            if c[f] is not None:
                chk(text, c[f], f"{where}.{f}")
        cats = c["cats"]
        if type(cats) is not list or not 1 <= len(cats) <= 3:
            e.append(f"{where}.cats: 1-3 Commons category names")
        else:
            for j, k in enumerate(cats):
                chk(one_line, k, f"{where}.cats[{j}]", 150, CAT_BAD)
                if type(k) is str and any(w in k.lower() for w in TEXT_BAD_WORDS):
                    e.append(f"{where}.cats[{j}]: may not contain a link or __LI_")
        p = c["perf"]
        if p is not None:
            if not (type(p) is list and len(p) == 3 and type(p[0]) is int and 150 <= p[0] <= 500
                    and type(p[1]) is bool and (p[2] is None or (type(p[2]) in (int, float) and 1.5 <= p[2] <= 15))):
                e.append(f"{where}.perf: [top km/h 150-500, over true/false, 0-100 s 1.5-15 or null]")
            if c["kind"] not in PERF_KINDS:
                e.append(f"{where}.perf: only for {sorted(PERF_KINDS)}")
        src = c["sources"]
        if type(src) is not list or not 1 <= len(src) <= 5:
            e.append(f"{where}.sources: 1-5 links")
        else:
            for j, u in enumerate(src):
                chk(source, u, f"{where}.sources[{j}]")
                if u not in opened:
                    e.append(f"{where}.sources[{j}]: not among the pages listed in opened")
        if c["id"] not in cars and type(c["family"]) is str and c["family"] not in families:
            e.append(f"{where}.family: new family '{c['family']}': a separate, normal PR, not a refresh")
        if c["id"] in cars and not e:          # blank-fill of an existing row
            old = cars[c["id"]][0]
            changed = [f for f in FIELDS if c[f] != old[f]]
            for f in changed:
                if old[f] is not None:
                    e.append(f"{where}.{f}: differs from today's row, which is not blank there")
                elif c[f] is None:
                    pass
            new_perf = p is not None and c["id"] not in perf
            if p is not None and c["id"] in perf and perf_value(p) != perf[c["id"]]:
                e.append(f"{where}.perf: the car already has figures")
            if not changed and not new_perf and not e:
                e.append(f"{where}: an existing car with nothing to fill")
        errs.extend(e)

    ph = pkg["photos"]
    if type(ph) is not dict:
        errs.append("photos: must be an object")
    else:
        for cid, v in ph.items():
            where = f"photos.{cid}"
            try:
                if cid not in cars and cid not in seen:
                    raise Bad(f"{where}: unknown car id")
                strict_keys(v, {"drop", "hero"}, where)
                if type(v["drop"]) is not list or len(v["drop"]) > 20:
                    raise Bad(f"{where}.drop: a list of at most 20 titles")
                for j, t in enumerate(v["drop"] + ([v["hero"]] if v["hero"] is not None else [])):
                    one_line(t, f"{where} title {j}", 200, TEXT_BAD)
            except Bad as x:
                errs.append(str(x))
    if errs:
        raise Bad("\n".join(errs))
    return pkg


def perf_value(p):
    return (p[0], p[1], None if p[2] is None else float(p[2]))


def row_source(c):
    return (f"    E({', '.join(repr(c[f]) for f in FIELDS[:12])},\n"
            f"      {', '.join(repr(c[f]) for f in FIELDS[12:])}),\n")


def apply(pkg, cat_path=CATALOG):
    src = open(cat_path, encoding="utf-8").read()
    cars, perf = load_catalog(cat_path)
    lines = src.splitlines(keepends=True)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l))

    def pos(lineno, col):          # ast columns are UTF-8 byte offsets
        return starts[lineno - 1] + len(lines[lineno - 1].encode("utf-8")[:col].decode("utf-8"))
    tree = ast.parse(src)
    top = {n.targets[0].id: n.value for n in tree.body
           if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
    edits, new_rows, new_perf = [], "", ""
    for c in pkg["cars"]:
        if c["id"] in cars:
            old, call = cars[c["id"]]
            for k, f in enumerate(FIELDS):
                if c[f] == old[f]:
                    continue
                node = call.args[k] if k < len(call.args) else None
                if not (isinstance(node, ast.Constant) and node.value is None):
                    raise Bad(f"{c['id']}.{f}: no literal None to fill in catalog.py; do it by hand")
                edits.append((pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset), repr(c[f])))
        else:
            new_rows += row_source(c)
        if c["perf"] is not None and c["id"] not in perf:
            new_perf += f"    {c['id']!r}: {perf_value(c['perf'])!r},\n"
    for node, add in ((top["CARS"], new_rows), (top["PERF"], new_perf)):
        if add:   # just before the closing bracket's line
            close = pos(node.end_lineno, node.end_col_offset) - 1
            at = src.rindex("\n", 0, close) + 1
            edits.append((at, at, add))
    for a, b, new in sorted(edits, key=lambda x: x[0], reverse=True):
        src = src[:a] + new + src[b:]
    tmpd = tempfile.mkdtemp()
    tmp = os.path.join(tmpd, "catalog.py")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        # Verify with the AST before writing: every package value is back, and only as a literal.
        got, gperf = load_catalog(tmp)
        if set(got) != set(cars) | {c["id"] for c in pkg["cars"]}:
            raise Bad("unexpected rows after the edit")
        before = sum(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in ast.walk(tree))
        after = sum(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in ast.walk(ast.parse(src)))
        if before != after:
            raise Bad("the edit added code")
        for c in pkg["cars"]:
            row, call = got[c["id"]]
            if c["id"] not in cars and not all(isinstance(a, (ast.Constant, ast.List)) for a in call.args):
                raise Bad(f"{c['id']}: written row is not all literals")
            if row != {f: c[f] for f in FIELDS}:
                raise Bad(f"{c['id']}: round trip failed")
            if c["perf"] is not None and c["id"] not in perf and gperf.get(c["id"]) != perf_value(c["perf"]):
                raise Bad(f"{c['id']}: PERF round trip failed")
        r = subprocess.run([sys.executable, "-I", tmp], capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise Bad("python3 -I catalog.py failed:\n" + r.stderr[-2000:])
        shutil.copyfile(tmp, cat_path)
    finally:
        shutil.rmtree(tmpd)
    new = [c["id"] for c in pkg["cars"] if c["id"] not in cars]
    print(f"catalog.py: {len(new)} rows added, {len(pkg['cars']) - len(new)} rows filled, "
          f"{new_perf.count(chr(10))} PERF entries")
    if new:
        print("next: python3 tools/images.py --only " + ",".join(new))


def own_photos():
    own = {}
    for name in ("images.json", "extra_images.json", "flickr.json", "nonfree_images.json"):
        p = os.path.join(ROOT, "data", name)
        if os.path.exists(p):
            for cid, entry in json.load(open(p, encoding="utf-8")).items():
                own.setdefault(cid, set()).update(x["t"] for x in entry.get("images", []))
    return own


def photos(pkg, own=None, heroes_path=HEROES):
    """Apply drop/hero picks only for photos the Dev's own runs put in images.json/flickr.json."""
    own = own_photos() if own is None else own
    h = json.load(open(heroes_path, encoding="utf-8"))
    ignored = []
    for cid, v in pkg["photos"].items():
        mine = own.get(cid, set())
        for t in v["drop"]:
            if t not in mine:
                ignored.append(f"drop {cid}: {t!r} is not in your own run")
            elif t not in h["drop"].get(cid, []):
                h["drop"].setdefault(cid, []).append(t)
        t = v["hero"]
        if t is not None:
            if t not in mine or t in h["drop"].get(cid, []):
                ignored.append(f"hero {cid}: {t!r} is not among your run's kept photos")
            else:
                h["hero"][cid] = t
    with open(heroes_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(h, fh, ensure_ascii=False, indent=1)
    print("heroes.json updated; now look at every photo yourself (tools/REFRESH.md, Dev step 4).")
    for s in ignored:
        print("ignored (report it):", s)
    return ignored


def report(pkg):
    out = ["Scout package (untrusted text, quoted as code):", "", "```text",
           f"window {pkg['window'][0]} to {pkg['window'][1]}"]
    for c in pkg["cars"]:
        out.append(f"{c['id']} | {c['name']} | {c['kind']} | {c['year']}")
        out += [f"    {u}" for u in c["sources"]]
    if pkg["notes"]:
        out.append("notes: " + pkg["notes"])
    out.append("opened:")
    out += [f"    {u}" for u in pkg["opened"]]
    if pkg["unreachable"]:
        out.append("unreachable: " + ", ".join(pkg["unreachable"]))
    out.append("```")
    print("\n".join(out))


def self_test():
    """Cyber's hostile cases a-j, on a scratch copy of catalog.py and heroes.json."""
    good = {"id": "zz-self-test", "family": "Temerario", "name": "Self Test", "kind": "Limited series",
            "year": 2026, "end": 0, "body": "Coupé", "engine": "4.0 L V8", "eng": "V8", "cv": 900,
            "units": None, "designer": None, "wiki": None, "note": "A note.",
            "cats": ["Lamborghini Self Test"], "perf": [340, False, 2.7],
            "sources": ["https://en.wikipedia.org/wiki/Lamborghini"]}
    base = {"version": 1, "window": ["2026-10-01", "2026-11-01"], "cars": [good], "photos": {}, "notes": "",
            "opened": ["https://en.wikipedia.org/wiki/Lamborghini", "https://www.evo.co.uk/lamborghini"],
            "unreachable": []}
    one = lambda **kw: dict(base, cars=[dict(good, **kw)])
    some_id = next(iter(load_catalog()[0]))
    js = json.dumps(base)
    cases = {
        "b newline": one(note="a\nb"), "b CR": one(note="a\rb"), "b bidi": one(note="a‮b"),
        "b zero-width": one(note="a​b"), "c comment-script": one(note="<!--<script x"),
        "c __LI_APP__": one(note="__LI_APP__"), "c javascript:": one(note="javascript:alert(1)"),
        "c template": one(note="{{u|x}}"), "d shell id": one(id="a,b;curl evil|sh"),
        "d path id": one(id="../x"), "d capital id": one(id="Miura"), "d existing id": one(id=some_id),
        "e year true": one(year=True), "e year string": one(year="1971"), "e year float": one(year=1971.5),
        "e year NaN": js.replace('"year": 2026', '"year": NaN'),
        "e year 1e400": js.replace('"year": 2026', '"year": 1e400'),
        "e cv -1": one(cv=-1), "e cv 99999": one(cv=99999),
        "f kind": one(kind="Hypercar"), "f eng": one(eng="W16"),
        "g duplicate key": js.replace('"version": 1', '"version": 1, "version": 1'),
        "g extra key": dict(base, exec="x"), "g extra car key": one(exec="x"),
        "h http": one(sources=["http://en.wikipedia.org/wiki/X"]),
        "h lamborghini.com": one(sources=["https://www.lamborghini.com/x"]),
        "h userinfo": one(sources=["https://en.wikipedia.org@evil.example/"]),
        "c link in name": one(name="Huracan see https://evil.example now"),
        "c www in note": one(note="see www.evil.example"), "c link in cat": one(cats=["a://b"]),
        "e end false": one(end=False), "e end true": one(end=True),
        "h unknown host": one(sources=["https://evil.example/page"]),
        "new family": one(family="Newfamily"),
        "j over 64 KB": js + " " * MAX_BYTES,
        "j 21 cars": dict(base, cars=[dict(good, id=f"zz-{i}") for i in range(21)]),
        "k source not opened": one(sources=["https://www.motor1.com/news/1/"]),
        "k no press opened": dict(base, opened=["https://en.wikipedia.org/wiki/Lamborghini",
                                                "https://en.wikipedia.org/wiki/List_of_Lamborghini_automobiles"]),
        "k no wikipedia opened": dict(base, cars=[], opened=["https://www.evo.co.uk/lamborghini",
                                                            "https://www.carscoops.com/category/lamborghini/"]),
        "k opened off-list": dict(base, opened=base["opened"] + ["https://evil.example/x"]),
        "k unreachable off-list": dict(base, unreachable=["evil.example"]),
        "k missing opened": {k: v for k, v in base.items() if k != "opened"},
        "k opened userinfo": dict(base, opened=base["opened"] + ["https://en.wikipedia.org@evil.example/"]),
        "k opened http": dict(base, opened=base["opened"] + ["http://www.evo.co.uk/x"]),
        "k opened control char": dict(base, opened=base["opened"] + ["https://www.evo.co.uk/a\nb"]),
        "k opened too long": dict(base, opened=base["opened"] + ["https://www.evo.co.uk/" + "a" * 300]),
        "k opened duplicate": dict(base, opened=base["opened"] + [base["opened"][0]]),
        "k unreachable not a list": dict(base, unreachable="en.wikipedia.org"),
        "k unreachable nested": dict(base, unreachable=[["en.wikipedia.org"]]),
        "k opened bad ipv6": dict(base, opened=base["opened"] + ["https://[::1/x"]),
        "k car source bad ipv6": one(sources=["https://[::1/x"]),
        "k opened upper-case host": dict(base, opened=base["opened"] + ["https://EN.WIKIPEDIA.ORG/wiki/X"]),
        "k unreachable dict": dict(base, unreachable=[{"h": "en.wikipedia.org"}]),
        "k opened nested": dict(base, opened=[["https://en.wikipedia.org/wiki/Lamborghini"], "https://www.evo.co.uk/lamborghini"]),
    }
    tmpd = tempfile.mkdtemp()
    cat, pk = os.path.join(tmpd, "catalog.py"), os.path.join(tmpd, "p.json")

    def run(p):
        with open(pk, "w", encoding="utf-8") as fh:
            fh.write(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))
        shutil.copy(CATALOG, cat)
        pkg = validate(load(pk), cat)
        apply(pkg, cat)
        return pkg
    fails = []
    try:
        for name, p in cases.items():
            try:
                run(p)
                fails.append(f"{name}: accepted")
            except Bad:
                pass
        evil = "x'); import os; os.system('id') #"         # (a) must import as an inert string
        run(one(note=evil))
        row, call = load_catalog(cat)[0]["zz-self-test"]
        if row["note"] != evil or not isinstance(call.args[14], ast.Constant):
            fails.append("a: not an inert string constant")
        hp = os.path.join(tmpd, "heroes.json")               # (i) titles not in your own run
        shutil.copy(HEROES, hp)
        pkg = dict(base, photos={"zz-self-test": {"drop": ["Mine.jpg", "Not mine.jpg"], "hero": "flickr:1"}})
        ign = photos(pkg, own={"zz-self-test": {"Mine.jpg"}}, heroes_path=hp)
        h = json.load(open(hp, encoding="utf-8"))
        if len(ign) != 2 or h["drop"].get("zz-self-test") != ["Mine.jpg"] or "zz-self-test" in h["hero"]:
            fails.append("i: picks outside your own run were applied")
        hf, hn = hunt_self_test(tmpd)
        fails += hf
    finally:
        shutil.rmtree(tmpd)
    for f in fails:
        print("FAIL", f)
    print("self-test " + ("FAILED" if fails else f"OK: {len(cases)} hostile packages and {hn} hostile "
                          "photo hunts rejected, (a) imported as an inert string, (i) picks outside your "
                          "run ignored, a good hunt applied"))
    return not fails


# ---- Photo hunt (tools/REFRESH.md, "Photo hunt"): hints only, never photo data ----------------
HUNT_TOP = {"version", "kind", "ids", "photos", "notes"}
HUNT_CAR = {"cats", "files", "flickr", "hero", "drop", "why"}
HUNT_NAME_RE = re.compile(r"[^\W_][\w .,'()&+-]{1,149}")      # Commons category or file name: no / : # etc.
TERM_RE = re.compile(r"[^\W_][\w .'-]{2,59}")                 # Flickr search term (same as flickr.py)
FLICKR_ID_RE = re.compile(r"flickr:[0-9]{1,20}")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
EXTRA = os.path.join(ROOT, "data", "extra_images.json")
FLICKR_Q = os.path.join(ROOT, "data", "flickr_queries.json")


def fold_words(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def names_car(cat, car_name):
    """A hunted category must name the car itself ("Lamborghini SC20 at Goodwood" for SC20),
    so it cannot pull in a whole family's photos."""
    n, k = fold_words(car_name), fold_words(cat)
    return f" {n} " in f" {k} " or n.replace(" ", "") in k.replace(" ", "")


def hunt_name(v, where, ext=False):
    one_line(v, where, 150, CAT_BAD)
    if not HUNT_NAME_RE.fullmatch(v) or ".." in v or any(w in v.lower() for w in TEXT_BAD_WORDS):
        raise Bad(f"{where}: letters, digits, spaces and . , ' ( ) & + - only; no namespace prefix")
    if ext and not v.lower().endswith(IMAGE_EXT):
        raise Bad(f"{where}: must be a {'/'.join(IMAGE_EXT)} file title without 'File:'")


def validate_hunt(pkg, cat_path=CATALOG):
    cars, _ = load_catalog(cat_path)
    strict_keys(pkg, HUNT_TOP, "package")
    if type(pkg["version"]) is not int or pkg["version"] != 1 or pkg["kind"] != "photo-hunt":
        raise Bad("version must be 1 and kind 'photo-hunt'")
    ids = pkg["ids"]
    if type(ids) is not list or not 1 <= len(ids) <= 10 or len(set(map(str, ids))) != len(ids) or \
            any(type(i) is not str or i not in cars for i in ids):
        raise Bad("ids: 1-10 distinct car ids that exist in tools/catalog.py")
    errs = []
    if pkg["notes"] != "":
        try:
            text(pkg["notes"], "notes", 300)
        except Bad as e:
            errs.append(str(e))
    ph = pkg["photos"]
    if type(ph) is not dict or set(ph) != set(ids):
        raise Bad("photos: exactly one entry per id in ids")
    for cid in ids:
        v, where, e = ph[cid], f"photos.{cid}", []
        try:
            strict_keys(v, HUNT_CAR, where)
        except Bad as x:
            errs.append(str(x))
            continue

        def lst(key, n):
            if type(v[key]) is not list or len(v[key]) > n or len(set(map(str, v[key]))) != len(v[key]):
                e.append(f"{where}.{key}: a list of at most {n} distinct entries")
                return []
            return v[key]
        for j, k in enumerate(lst("cats", 3)):
            try:
                hunt_name(k, f"{where}.cats[{j}]")
                if not names_car(k, cars[cid][0]["name"]):
                    raise Bad(f"{where}.cats[{j}]: must contain the car's name '{cars[cid][0]['name']}'")
            except Bad as x:
                e.append(str(x))
        files = lst("files", 10)
        for j, t in enumerate(files):
            try:
                hunt_name(t, f"{where}.files[{j}]", ext=True)
            except Bad as x:
                e.append(str(x))
        for j, t in enumerate(lst("flickr", 5)):
            if type(t) is not str or not TERM_RE.fullmatch(t) or unicodedata.normalize("NFC", t) != t:
                e.append(f"{where}.flickr[{j}]: 3-60 letters, digits, spaces and . ' - only")
        for j, t in enumerate(lst("drop", 20) + ([v["hero"]] if v["hero"] is not None else [])):
            try:
                if type(t) is not str or not FLICKR_ID_RE.fullmatch(t):
                    hunt_name(t, f"{where} pick {j}", ext=True)
            except Bad as x:
                e.append(str(x))
        if v["why"] != "":
            try:
                text(v["why"], f"{where}.why", 200)
            except Bad as x:
                e.append(str(x))
        if not (v["cats"] or v["files"] or v["flickr"]) and v["why"] == "":
            e.append(f"{where}: nothing found needs a one-line 'why'")
        errs.extend(e)
    if errs:
        raise Bad("\n".join(errs))
    return pkg


def is_hunt(pkg):
    return type(pkg) is dict and "kind" in pkg


def commons_file(title, fetch=None, credit=None):
    """Our own record of a Commons file named by the Scout, or (None, reason). Fetched by this tool
    from commons.wikimedia.org only; accepted only with a free licence we recognise and no
    deletion, copyright-violation or missing-permission tag."""
    import hashlib
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import images
    fetch, credit = fetch or images.fetch_html, credit or images.raw_credit
    page = fetch(images.PAGE + "File:" + urllib.parse.quote(title.replace(" ", "_")))
    m = re.search(r'class="fileInfo">[^<]*?([\d,]+)\s*(?:×|&#215;|x)\s*([\d,]+)\s*pixels', page or "")
    if not m:
        return None, "no such file, or not an image"
    w, h = (int(x.replace(",", "")) for x in m.groups())
    raw = fetch("https://commons.wikimedia.org/w/index.php?" +
                urllib.parse.urlencode({"title": "File:" + title, "action": "raw"})) or ""
    if re.search(r"\{\{\s*(?:delete|deletion|speedy|sd\s*\||copyvio|no permission|no license|no source|"
                 r"dw no source|npd|nld|nsd|db-|duplicate|nowcommons)", raw, re.I):
        return None, "tagged for deletion or missing permission on Commons"
    if images.BAD.search(title):
        return None, "title names a detail, toy, render or interior"
    if w < 600:
        return None, f"too small ({w} px wide)"
    cr = credit("File:" + title)
    if not cr or not cr[1]:
        return None, "no free licence recognised"
    name = title.replace(" ", "_")
    md5 = hashlib.md5(name.encode("utf-8")).hexdigest()
    return {"t": title, "h": f"{md5[0]}/{md5[:2]}", "n": urllib.parse.quote(name), "w": w, "ht": h,
            "a": cr[0], "l": cr[1], "lu": cr[2]}, ""


def hunt(pkg, cat_path=CATALOG, extra_path=EXTRA, queries_path=FLICKR_Q, fetch=None, credit=None):
    """Turn checked hints into our own data: categories (front of the car's cats), Flickr search
    terms (data/flickr_queries.json, read by flickr.py) and Commons files fetched and credited by
    this tool (data/extra_images.json). Photos still come only from the Dev's own runs."""
    src = open(cat_path, encoding="utf-8").read()
    cars, _ = load_catalog(cat_path)
    lines = src.splitlines(keepends=True)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l))

    def pos(lineno, col):
        return starts[lineno - 1] + len(lines[lineno - 1].encode("utf-8")[:col].decode("utf-8"))
    edits, want = [], {}
    for cid in pkg["ids"]:
        row, call = cars[cid]
        new = [k for k in pkg["photos"][cid]["cats"] if k not in row["cats"]]
        if not new:
            continue
        node = call.args[12]
        if not isinstance(node, (ast.List, ast.Constant)):
            raise Bad(f"{cid}: cats in catalog.py is not a literal; do it by hand")
        want[cid] = new + row["cats"]
        edits.append((pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset), repr(want[cid])))
    for a, b, new in sorted(edits, key=lambda x: x[0], reverse=True):
        src = src[:a] + new + src[b:]
    if edits:
        tmpd = tempfile.mkdtemp()
        tmp = os.path.join(tmpd, "catalog.py")
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(src)
            got, _ = load_catalog(tmp)
            for cid, (row, call) in got.items():
                expect = dict(cars[cid][0], cats=want.get(cid, cars[cid][0]["cats"]))
                if row != expect or (cid in want and not isinstance(call.args[12], ast.List)):
                    raise Bad(f"{cid}: round trip failed")
            if set(got) != set(cars):
                raise Bad("unexpected rows after the edit")
            r = subprocess.run([sys.executable, "-I", tmp], capture_output=True, text=True, timeout=60)
            if r.returncode:
                raise Bad("python3 -I catalog.py failed:\n" + r.stderr[-2000:])
            shutil.copyfile(tmp, cat_path)
        finally:
            shutil.rmtree(tmpd)
    q = json.load(open(queries_path, encoding="utf-8")) if os.path.exists(queries_path) else {}
    for cid in pkg["ids"]:
        terms = [t for t in pkg["photos"][cid]["flickr"] if t not in q.get(cid, [])]
        if terms:
            q[cid] = (q.get(cid, []) + terms)[-8:]
    with open(queries_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(sorted(q.items())), fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    extra = json.load(open(extra_path, encoding="utf-8")) if os.path.exists(extra_path) else {}
    skipped = []
    for cid in pkg["ids"]:
        have = {im["t"] for im in extra.get(cid, {}).get("images", [])}
        for t in pkg["photos"][cid]["files"]:
            if t in have:
                continue
            rec, why = commons_file(t, fetch, credit)
            if rec is None:
                skipped.append(f"{cid}: {t!r}: {why}")
                continue
            extra.setdefault(cid, {"source": "Commons search (outside the car's categories)", "images": []})
            extra[cid]["images"].append(rec)
    with open(extra_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(extra, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"catalog.py: categories added for {sorted(want)}; flickr_queries.json and extra_images.json updated")
    for s in skipped:
        print("skipped file (report it):", s)
    ids = ",".join(pkg["ids"])
    print(f"next: python3 tools/images.py --only {ids}; python3 tools/flickr.py --only {ids}")
    return skipped


def hunt_report(pkg):
    out = ["Scout photo-hunt hints (untrusted text, quoted as code):", "", "```text"]
    for cid in pkg["ids"]:
        v = pkg["photos"][cid]
        out.append(cid)
        out += [f"    {k}: {x}" for k in ("cats", "files", "flickr", "drop") for x in v[k]]
        if v["hero"]:
            out.append(f"    hero: {v['hero']}")
        if v["why"]:
            out.append(f"    why: {v['why']}")
    if pkg["notes"]:
        out.append("notes: " + pkg["notes"])
    out.append("```")
    print("\n".join(out))


def hunt_self_test(tmpd):
    """Hostile photo-hunt packages, and one good one applied to scratch copies."""
    cars = load_catalog()[0]
    cid = next(i for i, (r, _) in cars.items() if len(fold_words(r["name"])) >= 4)
    name = cars[cid][0]["name"]
    entry = {"cats": [f"Lamborghini {name} at a show"], "files": [f"Lamborghini {name} 2023.jpg"],
             "flickr": [f"Lamborghini {fold_words(name)} show"], "hero": "flickr:123", "drop": [], "why": ""}
    base = {"version": 1, "kind": "photo-hunt", "ids": [cid], "photos": {cid: entry}, "notes": ""}
    one = lambda **kw: dict(base, photos={cid: dict(entry, **kw)})
    cases = {
        "hunt unknown id": dict(base, ids=["no-such-car"], photos={"no-such-car": entry}),
        "hunt id not in ids": dict(base, photos={cid: entry, "zz": entry}),
        "hunt extra key": dict(base, exec="x"), "hunt extra car key": one(url="x"),
        "hunt bad kind": dict(base, kind="refresh"),
        "hunt cat without car name": one(cats=["Lamborghini Aventador"]),
        "hunt cat namespace": one(cats=[f"Category:Lamborghini {name}"]),
        "hunt cat slash": one(cats=[f"Lamborghini {name}/../x"]),
        "hunt cat link": one(cats=[f"https Lamborghini {name}"]),
        "hunt file no ext": one(files=[f"Lamborghini {name}"]),
        "hunt file prefix": one(files=[f"File:Lamborghini {name}.jpg"]),
        "hunt file svg": one(files=["Lamborghini.svg"]),
        "hunt file script": one(files=["<script>.jpg"]),
        "hunt term ampersand": one(flickr=["Lamborghini&license=0"]),
        "hunt term newline": one(flickr=["Lamborghini\nx"]),
        "hunt term long": one(flickr=["Lamborghini " + "x" * 60]),
        "hunt hero url": one(hero="https://evil.example/x.jpg"),
        "hunt hero flickr letters": one(hero="flickr:12a"),
        "hunt too many cats": one(cats=[f"Lamborghini {name} {i}" for i in range(4)]),
        "hunt empty without why": one(cats=[], files=[], flickr=[]),
        "hunt why with link": one(why="see www.evil.example"),
        "hunt 11 ids": dict(base, ids=[cid] * 11),
    }
    fails = []
    for n, p in cases.items():
        try:
            validate_hunt(json.loads(json.dumps(p)))
            fails.append(f"{n}: accepted")
        except Bad:
            pass
    cat, ex, fq = (os.path.join(tmpd, f) for f in ("catalog.py", "extra.json", "fq.json"))
    shutil.copy(CATALOG, cat)
    with open(ex, "w") as fh:
        fh.write("{}")
    page = '<span class="fileInfo">3,000 × 2,000 pixels</span>'
    cc = lambda t: ("Test author", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")
    hunt(validate_hunt(base, cat), cat, ex, fq, fetch=lambda url: page if "/wiki/File:" in url else "{{self|cc-by-4.0}}", credit=cc)
    row = load_catalog(cat)[0][cid][0]
    q, x = json.load(open(fq)), json.load(open(ex))
    if row["cats"][0] != entry["cats"][0] or row["cats"][1:] != cars[cid][0]["cats"]:
        fails.append("hunt: category not put first, or the old ones changed")
    if q.get(cid) != entry["flickr"]:
        fails.append("hunt: flickr terms not written")
    if [im["t"] for im in x.get(cid, {}).get("images", [])] != entry["files"]:
        fails.append("hunt: Commons file not recorded")
    shutil.copy(CATALOG, cat)
    with open(ex, "w") as fh:
        fh.write("{}")
    for tag in ("{{copyvio}}", "{{SD|F1}}", "{{Deletion request|x}}", "{{dw no source since|x}}"):
        with open(ex, "w") as fh:
            fh.write("{}")
        hunt(base, cat, ex, fq, fetch=lambda url: page if "/wiki/File:" in url else "{{self|cc-by-4.0}}" + tag,
             credit=cc)
        if json.load(open(ex)):
            fails.append(f"hunt: a file tagged {tag} was recorded")
    return fails, len(cases)


def main_catalog_copy():
    """After apply or hunt the catalogue differs from main's, so later steps validate against main's."""
    r = subprocess.run(["git", "-C", ROOT, "show", "origin/main:tools/catalog.py"], capture_output=True, text=True)
    if r.returncode:
        raise Bad("cannot read origin/main:tools/catalog.py; run git fetch origin main first")
    d = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, d, True)
    p = os.path.join(d, "catalog.py")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(r.stdout)
    return p


def main():
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(0 if self_test() else 1)
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "apply", "photos", "report", "hunt"):
        sys.exit(__doc__.split("\n\n")[1])
    try:
        pkg = load(sys.argv[2])
        if is_hunt(pkg):
            if sys.argv[1] == "apply":
                raise Bad("a photo-hunt package: use 'hunt', not 'apply'")
            validate_hunt(pkg, main_catalog_copy() if sys.argv[1] in ("photos", "report") else CATALOG)
            if sys.argv[1] == "check":
                print(f"photo-hunt package OK: {len(pkg['ids'])} cars")
            else:
                {"hunt": hunt, "photos": photos, "report": hunt_report}[sys.argv[1]](pkg)
            return
        if sys.argv[1] == "hunt":
            raise Bad("not a photo-hunt package")
        if sys.argv[1] in ("check", "apply"):
            validate(pkg)
            if sys.argv[1] == "check":
                print(f"package OK: {len(pkg['cars'])} cars, photo picks for {len(pkg['photos'])} cars")
            else:
                apply(pkg)
        else:
            validate(pkg, main_catalog_copy())
            (photos if sys.argv[1] == "photos" else report)(pkg)
    except Bad as e:
        sys.exit("package rejected:\n" + str(e))


if __name__ == "__main__":
    main()

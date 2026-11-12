"""Check the Scout's monthly package and turn it into catalogue rows (tools/REFRESH.md, Dev).

The package is untrusted data written by a chat that read the open web (Cyber's spec, 2026-11-11).
This script never evaluates, executes or imports package text, never opens a URL from it and runs
no shell. It writes rows only as repr() of values that passed every check, verifies them with the
AST, then runs `python3 -I` on the edited catalogue. Any violation rejects the whole package.

  python3 tools/scout_import.py check  PKG.json [--run-date D]   # validate only (v2 needs the run date)
  python3 tools/scout_import.py gaps   YYYY-MM-DD  # the cars a run on that day may fill (round-robin)
  python3 tools/scout_import.py apply  PKG.json   # validate, then write rows to tools/catalog.py
  python3 tools/scout_import.py photos PKG.json   # after your own images.py/flickr.py runs: apply
                                                  # drop/hero picks found in those runs only
  python3 tools/scout_import.py report PKG.json   # Markdown for the PR body (package text fenced)
  python3 tools/scout_import.py hunt   PKG.json   # photo hunt: write the checked hints (see below)
  python3 tools/scout_import.py audit-ids N       # audit: the ids of batch N (1-5), CARS row order
  python3 tools/scout_import.py audit  PKG.json   # audit: validate, then apply the findings
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

Version 2 (from 2026-11; version 1 is rejected after V1_UNTIL): "version": 2 and one more key,
"fills", beside the keys above. "cars" holds new ids only. "fills" holds blank-fills of existing
cars in the same row format, at most CADENCES[CADENCE]["fills"], and only for the ids
`gaps <run date>` prints, only in their gap fields (cv, units, designer, a missing perf; never a
SKIP field). Each fill cites two different pages on two different hosts, both in "opened". The
window must end on the run date, which the Dev gives as --run-date from the run's fire event and
never takes from the package. Photo picks are only for new cars.

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

Audit package (tools/REFRESH.md, "Audit"): mismatches between our rows and two sources, for one batch.
At most 160 KB (other packages: 64 KB).
{
  "version": 1, "kind": "audit", "batch": 3,        # the N of the fire text "Audit: batch N of 5"
  "checked": ["miura-p400", "..."],                  # the batch's ids the Scout compared (a subset)
  "findings": [                                      # at most 60, one per (id, field), mismatches only
    {"id": "miura-p400", "field": "year",            # field: family kind year end body engine designer
     "ours": 1966,                                   # exactly today's value in catalog.py
     "theirs": 1967,                                 # what BOTH sources say; differs from ours
     "sources": ["https://en.wikipedia.org/wiki/...", "https://www.evo.co.uk/..."]}],
                                                     # exactly 2 pages on 2 different AUDIT_HOSTS, in opened
  "notes": "",                                       # one line: cars not checked, sources that disagree
  "opened": ["https://en.wikipedia.org/wiki/..."],   # 2-150 pages read in full, hosts in AUDIT_HOSTS
  "unreachable": []                                  # AUDIT_HOSTS hosts that failed to load
}
Batches: the cars in CARS row order, 30 per batch; batch 5 takes the rest (29 of 149 today).
"""
import ast, atexit, datetime, json, os, re, shutil, subprocess, sys, tempfile, unicodedata, urllib.parse

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CATALOG = os.path.join(ROOT, "tools", "catalog.py")
HEROES = os.path.join(ROOT, "data", "heroes.json")
APP = os.path.join(ROOT, "src", "app.js")
MAX_BYTES = 64 * 1024
AUDIT_MAX_BYTES = 160 * 1024                          # an audit package lists up to 150 pages read
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
# Cadence (tools/REFRESH.md): weekly, the user's choice of 2026-11-12 (Mondays, 03:17 UTC).
CADENCE = "weekly"
CADENCES = {"daily": {"period": 1, "window": 7, "fills": 3}, "weekly": {"period": 7, "window": 10, "fills": 7}}
GAP_EPOCH = datetime.date(2026, 1, 5)                 # a Monday; round-robin day 0
GAP_FIELDS = ("cv", "units", "designer")              # plus "perf" (a missing PERF entry); wiki is not a gap
SKIP = {cid: {"units"} for cid in ("miura-svj", "countach-lp400", "urraco-p200", "countach-lp500s",
                                   "diablo-svr", "murcielago-sv", "countach-25th")}   # BACKLOG "spec doubts"
V1_UNTIL = datetime.date(2026, 11, 30)                # v1 packages are rejected after this day
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
    size = os.path.getsize(path)
    if size > AUDIT_MAX_BYTES:
        raise Bad(f"package larger than {AUDIT_MAX_BYTES} bytes")
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
        obj = json.loads(s, object_pairs_hook=pairs, parse_constant=const, parse_float=num)
    except ValueError as e:
        raise Bad(f"not valid JSON: {e}")
    if size > MAX_BYTES and not is_audit(obj):
        raise Bad(f"package larger than {MAX_BYTES} bytes")
    return obj


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


def gap_fields(row, perf):
    """The fields of a car that a fill may set: blank today and not a doubted blank (SKIP)."""
    out = {f for f in GAP_FIELDS if row[f] is None}
    if row["kind"] in PERF_KINDS and row["id"] not in perf:
        out.add("perf")
    return out - SKIP.get(row["id"], set())


def gap_ids(run_date, cat_path=CATALOG):
    """The cars a run on run_date may fill, round-robin over every car with a gap, sorted by id."""
    cars, perf = load_catalog(cat_path)
    cad = CADENCES[CADENCE]
    ids = sorted(cid for cid, (row, _) in cars.items() if gap_fields(row, perf))
    if not ids:
        return []
    k = (run_date - GAP_EPOCH).days // cad["period"] * cad["fills"]
    return [ids[(k + i) % len(ids)] for i in range(min(cad["fills"], len(ids)))]


def validate(pkg, cat_path=CATALOG, run_date=None, today=None):
    cars, perf = load_catalog(cat_path)
    kinds, engs = read_order("KIND_ORDER"), read_order("ENG_ORDER")
    families = {r["family"] for r, _ in cars.values()}
    today = today or datetime.date.today()
    errs = []

    ver = pkg.get("version") if type(pkg) is dict else None
    if type(ver) is not int or ver not in (1, 2):
        raise Bad("version must be 1 or 2")
    strict_keys(pkg, TOP_KEYS | ({"fills"} if ver == 2 else set()), "package")
    if ver == 1 and today > V1_UNTIL:
        raise Bad(f"version 1 packages are not accepted after {V1_UNTIL}")
    fills = pkg.get("fills", [])
    if ver == 2:
        cad = CADENCES[CADENCE]
        if run_date is None:
            raise Bad("version 2: give --run-date YYYY-MM-DD, the day the run was fired (from its fire event)")
        if type(pkg["window"]) is not list or len(pkg["window"]) != 2 or pkg["window"][1] != run_date.isoformat():
            raise Bad(f"window must end on the run date {run_date}")
        try:
            if (run_date - datetime.date.fromisoformat(pkg["window"][0])).days > cad["window"]:
                raise Bad(f"window longer than {cad['window']} days")
        except (TypeError, ValueError):
            raise Bad("window: two ISO dates")
        if type(fills) is not list or len(fills) > cad["fills"]:
            raise Bad(f"fills: a list of at most {cad['fills']}")
        today_gaps = gap_ids(run_date, cat_path)
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
    for i, (c, is_fill) in enumerate([(c, False) for c in pkg["cars"]] + [(c, True) for c in fills]):
        where = f"fills[{i - len(pkg['cars'])}]" if is_fill else f"cars[{i}]"
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
        if ver == 2 and not is_fill and c["id"] in cars:
            e.append(f"{where}: an existing car; a blank-fill goes in fills")
        if is_fill:
            if c["id"] not in cars:
                e.append(f"{where}: fills are for existing cars only")
            elif c["id"] not in today_gaps:
                e.append(f"{where}: not one of the gap ids for {run_date} ({', '.join(today_gaps)})")
            else:
                ok = gap_fields(cars[c["id"]][0], perf)
                bad = [f for f in FIELDS if c[f] != cars[c["id"]][0][f] and f not in ok]
                if p is not None and c["id"] not in perf and "perf" not in ok:
                    bad.append("perf")
                if bad:
                    e.append(f"{where}: may fill only {sorted(ok)}, not {bad}")
            src = c["sources"] if type(c["sources"]) is list else []
            if len(set(src)) < 2 or len({urllib.parse.urlsplit(u).hostname for u in src if type(u) is str}) < 2:
                e.append(f"{where}.sources: a fill needs two different pages on two different hosts that agree")
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
                if ver == 2 and cid not in {c["id"] for c in pkg["cars"] if type(c) is dict}:
                    raise Bad(f"{where}: photo picks only for new cars")
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
    rows = pkg["cars"] + pkg.get("fills", [])
    for c in rows:
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
        if set(got) != set(cars) | {c["id"] for c in rows}:
            raise Bad("unexpected rows after the edit")
        before = sum(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in ast.walk(tree))
        after = sum(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in ast.walk(ast.parse(src)))
        if before != after:
            raise Bad("the edit added code")
        for c in rows:
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
    new = [c["id"] for c in rows if c["id"] not in cars]
    print(f"catalog.py: {len(new)} rows added, {len(rows) - len(new)} rows filled, "
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
    cars = load_catalog()[0]
    for c in pkg.get("fills", []):
        old = cars.get(c["id"], ({}, None))[0]
        got = [f"{f}={c[f]!r}" for f in FIELDS if c[f] != old.get(f)] + (["perf=" + repr(c["perf"])] if c["perf"] else [])
        out.append(f"fill {c['id']} | {', '.join(got)}")
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
        pkg = validate(load(pk), cat, today=V1_UNTIL)       # v1 cases: on the last day v1 is accepted
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
        af, an = audit_self_test(tmpd)
        fails += af
        vf, vn = v2_self_test(tmpd)
        fails += vf
    finally:
        shutil.rmtree(tmpd)
    for f in fails:
        print("FAIL", f)
    print("self-test " + ("FAILED" if fails else f"OK: {len(cases)} hostile packages, {vn} hostile v2 "
                          f"packages, {hn} hostile photo hunts and {an} hostile audits rejected, a good v2 fill applied, (a) imported as an inert string, (i) picks outside your "
                          "run ignored, a good hunt and a good audit applied"))
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
    return type(pkg) is dict and "kind" in pkg and pkg.get("kind") != "audit"


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


def v2_self_test(tmpd):
    """Version 2: fills only for the run date's gap ids, two hosts, the run date from the Dev."""
    cars, perf = load_catalog()
    day = datetime.date(2026, 11, 16)
    gid = gap_ids(day)[0]
    row = cars[gid][0]
    f = sorted(gap_fields(row, perf) - {"perf"})[0] if gap_fields(row, perf) - {"perf"} else None
    fill = dict(row, perf=None, sources=["https://en.wikipedia.org/wiki/Lamborghini", "https://www.evo.co.uk/lamborghini"])
    if f:
        fill[f] = {"cv": 400, "units": 10, "designer": "A Designer"}[f]
    else:
        fill["perf"] = [300, False, 3.5]
    good = {"version": 2, "window": ["2026-11-09", "2026-11-16"], "cars": [], "fills": [fill], "photos": {},
            "notes": "", "opened": ["https://en.wikipedia.org/wiki/Lamborghini", "https://www.evo.co.uk/lamborghini"],
            "unreachable": []}
    other = next(i for i in sorted(cars) if i not in gap_ids(day))
    off = gap_ids(day + datetime.timedelta(days=CADENCES[CADENCE]["period"]))[0]
    one = lambda **kw: dict(good, fills=[dict(fill, **kw)])
    cases = {
        "v2 fill id not today's": one(id=other),
        "v2 fill id of the next run": dict(good, fills=[dict(cars[off][0], perf=None, sources=fill["sources"])]),
        "v2 one source": one(sources=fill["sources"][:1]),
        "v2 same page twice": one(sources=[fill["sources"][0]] * 2),
        "v2 two pages, one host": dict(good, opened=good["opened"] + ["https://en.wikipedia.org/wiki/List_of_Lamborghini_automobiles"],
                                       fills=[dict(fill, sources=["https://en.wikipedia.org/wiki/Lamborghini",
                                                                  "https://en.wikipedia.org/wiki/List_of_Lamborghini_automobiles"])]),
        "v2 source not opened": one(sources=[fill["sources"][0], "https://www.motor1.com/x/"]),
        "v2 fill a non-gap field": one(note="Changed."),
        "v2 fill wiki": one(wiki="Lamborghini") if row["wiki"] is None else one(note="x"),
        "v2 window not on run date": dict(good, window=["2026-11-09", "2026-11-15"]),
        "v2 window too long": dict(good, window=["2026-10-01", "2026-11-16"]),
        "v2 existing id in cars": dict(good, cars=[fill], fills=[]),
        "v2 too many fills": dict(good, fills=[fill] * (CADENCES[CADENCE]["fills"] + 1)),
        "v2 photos for a fill": dict(good, photos={gid: {"drop": [], "hero": None}}),
        "v2 missing fills key": {k: v for k, v in good.items() if k != "fills"},
        "v2 no run date": None,
        "v1 after cut-off": None,
    }
    fails = []
    for name, p in cases.items():
        try:
            if name == "v2 no run date":
                validate(json.loads(json.dumps(good)), today=day)
            elif name == "v1 after cut-off":
                v1 = {k: v for k, v in good.items() if k != "fills"}
                validate(dict(v1, version=1, window=["2026-11-20", "2026-12-01"]), today=V1_UNTIL + datetime.timedelta(days=1))
            else:
                validate(json.loads(json.dumps(p)), run_date=day, today=day)
            fails.append(f"{name}: accepted")
        except Bad:
            pass
    skip_row = dict(cars["miura-svj"][0])
    if "units" in gap_fields(skip_row, perf):
        fails.append("v2: a SKIP field counts as a gap")
    cat = os.path.join(tmpd, "catalog_v2.py")
    shutil.copy(CATALOG, cat)
    try:
        apply(validate(json.loads(json.dumps(good)), cat, run_date=day, today=day), cat)
        got, gperf = load_catalog(cat)
        if (f and got[gid][0][f] != fill[f]) or (not f and gid not in gperf):
            fails.append("v2: the good fill was not written")
    except Bad as e:
        fails.append(f"v2: the good fill was rejected: {e}")
    return fails, len(cases)


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


# ---- Audit (tools/REFRESH.md, "Audit"): our rows against two sources; mismatches only ------------
AUDIT_TOP = {"version", "kind", "batch", "checked", "findings", "notes", "opened", "unreachable"}
AUDIT_FINDING = {"id", "field", "ours", "theirs", "sources"}
AUDIT_FIELDS = ("family", "kind", "year", "end", "body", "engine", "designer")
AUDIT_HOSTS = SOURCE_HOSTS | {"www.ultimatecarpage.com", "www.conceptcarz.com", "www.supercars.net"}
AUDIT_BATCHES, AUDIT_SIZE, AUDIT_MAX_FINDINGS = 5, 30, 60
AUDIT_FIRE_RE = re.compile(r"Audit: batch ([1-5]) of 5")      # the whole fire text, nothing around it


def is_audit(pkg):
    return type(pkg) is dict and pkg.get("kind") == "audit"


def audit_ids(n, cat_path=CATALOG):
    """Batch n (1-5): CARS in row order, 30 per batch; the last batch takes the rest."""
    if type(n) is not int or not 1 <= n <= AUDIT_BATCHES:
        raise Bad(f"batch must be an integer 1-{AUDIT_BATCHES}")
    ids = list(load_catalog(cat_path)[0])
    return ids[AUDIT_SIZE * (n - 1):] if n == AUDIT_BATCHES else ids[AUDIT_SIZE * (n - 1):AUDIT_SIZE * n]


def audit_source(v, where):
    if type(v) is not str:
        raise Bad(f"{where}: must be a string")
    try:
        source(v, where)                     # same rules, on the wider audit host list
    except Bad:
        u = urllib.parse.urlsplit(v) if len(v) <= 300 and all(33 <= ord(c) <= 126 for c in v) and "`" not in v else None
        try:
            ok = u is not None and u.scheme == "https" and u.port is None and u.hostname in AUDIT_HOSTS and u.netloc == u.hostname
        except ValueError:
            ok = False
        if not ok:
            raise Bad(f"{where}: must be https on one of {sorted(AUDIT_HOSTS)}")


def audit_value(field, v, where, families, kinds, today):
    if field == "family":
        if type(v) is not str or v not in families:
            raise Bad(f"{where}: an existing family (a new family is a separate, normal PR)")
    elif field == "kind":
        if v not in kinds:
            raise Bad(f"{where}: one of {kinds}")
    elif field == "year":
        integer(v, where, 1963, today.year + 1, False)
    elif field == "end":
        if not (v is None or v == 0 and type(v) is int):
            integer(v, where, 1963, today.year + 1, False)
    else:                                    # body, engine, designer: one line of plain text
        text(v, where)


def validate_audit(pkg, cat_path=CATALOG, today=None):
    cars, _ = load_catalog(cat_path)
    kinds = read_order("KIND_ORDER")
    families = {r["family"] for r, _ in cars.values()}
    today = today or datetime.date.today()
    strict_keys(pkg, AUDIT_TOP, "package")
    if type(pkg["version"]) is not int or pkg["version"] != 1 or pkg["kind"] != "audit":
        raise Bad("version must be 1 and kind 'audit'")
    batch = audit_ids(pkg["batch"], cat_path)
    errs = []
    if pkg["notes"] != "":
        try:
            text(pkg["notes"], "notes", 600)
        except Bad as e:
            errs.append(str(e))
    chk = pkg["checked"]
    if type(chk) is not list or len(set(map(repr, chk))) != len(chk) or any(c not in batch for c in chk):
        errs.append(f"checked: distinct ids of batch {pkg['batch']}")
    opened, unreach = pkg["opened"], pkg["unreachable"]
    if type(opened) is not list or not 2 <= len(opened) <= 150 or len(set(map(repr, opened))) != len(opened):
        errs.append("opened: 2-150 distinct pages read in full")
        opened = []
    else:
        good = []
        for j, u in enumerate(opened):
            try:
                audit_source(u, f"opened[{j}]")
                good.append(u)
            except Bad as e:
                errs.append(str(e))
        opened = good
    if type(unreach) is not list or len(unreach) > len(AUDIT_HOSTS) or len(set(map(repr, unreach))) != len(unreach) \
            or any(type(h) is not str or h not in AUDIT_HOSTS for h in unreach):
        errs.append(f"unreachable: distinct hosts from {sorted(AUDIT_HOSTS)}")
    fs = pkg["findings"]
    if type(fs) is not list or len(fs) > AUDIT_MAX_FINDINGS:
        raise Bad(f"findings: a list of at most {AUDIT_MAX_FINDINGS}")
    seen, after = set(), {}
    for i, f in enumerate(fs):
        where = f"findings[{i}]"
        try:
            strict_keys(f, AUDIT_FINDING, where)
            cid, field = f["id"], f["field"]
            if type(cid) is not str or cid not in batch:
                raise Bad(f"{where}.id: not a car of batch {pkg['batch']}")
            if type(chk) is list and cid not in chk:
                raise Bad(f"{where}.id: not listed in checked")
            if type(field) is not str or field not in AUDIT_FIELDS:
                raise Bad(f"{where}.field: one of {list(AUDIT_FIELDS)} (photos, cats and specs are not audited)")
            if (cid, field) in seen:
                raise Bad(f"{where}: {cid}.{field} twice")
            seen.add((cid, field))
            row = cars[cid][0]
            if type(f["ours"]) is not type(row[field]) or f["ours"] != row[field]:
                raise Bad(f"{where}.ours: is not today's value of {cid}.{field}")
            audit_value(field, f["theirs"], f"{where}.theirs", families, kinds, today)
            if type(f["theirs"]) is type(row[field]) and f["theirs"] == row[field]:
                raise Bad(f"{where}.theirs: equals ours; report mismatches only")
            src = f["sources"]
            if type(src) is not list or len(src) != 2:
                raise Bad(f"{where}.sources: exactly two pages that agree")
            for j, u in enumerate(src):
                audit_source(u, f"{where}.sources[{j}]")
                if u not in opened:
                    raise Bad(f"{where}.sources[{j}]: not among the pages listed in opened")
            if len({urllib.parse.urlsplit(u).hostname for u in src}) != 2:
                raise Bad(f"{where}.sources: two different hosts")
            after.setdefault(cid, dict(row))[field] = f["theirs"]
        except Bad as e:
            errs.append(str(e))
    for cid, row in after.items():
        if type(row["end"]) is int and row["end"] != 0 and row["end"] < row["year"]:
            errs.append(f"{cid}: end {row['end']} before year {row['year']} after the findings")
    if errs:
        raise Bad("\n".join(errs))
    return pkg


def apply_audit(pkg, cat_path=CATALOG):
    """Write each finding's value over today's argument in its E(...) call, as repr(), then verify."""
    src = open(cat_path, encoding="utf-8").read()
    cars, perf = load_catalog(cat_path)
    lines = src.splitlines(keepends=True)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l))

    def pos(lineno, col):
        return starts[lineno - 1] + len(lines[lineno - 1].encode("utf-8")[:col].decode("utf-8"))
    edits, want = [], {cid: dict(r) for cid, (r, _) in cars.items()}
    for f in pkg["findings"]:
        k = FIELDS.index(f["field"])
        node = cars[f["id"]][1].args[k] if k < len(cars[f["id"]][1].args) else None
        if not isinstance(node, (ast.Constant, ast.Name)):
            raise Bad(f"{f['id']}.{f['field']}: no plain argument to replace in catalog.py; do it by hand")
        edits.append((pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset), repr(f["theirs"])))
        want[f["id"]][f["field"]] = f["theirs"]
    for a, b, new in sorted(edits, key=lambda x: x[0], reverse=True):
        src = src[:a] + new + src[b:]
    tmpd = tempfile.mkdtemp()
    tmp = os.path.join(tmpd, "catalog.py")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        got, gperf = load_catalog(tmp)
        if list(got) != list(cars) or gperf != perf:
            raise Bad("rows or PERF changed beyond the findings")
        for cid, (row, call) in got.items():
            if row != want[cid]:
                raise Bad(f"{cid}: round trip failed")
        count = lambda t: sum(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Call)) for n in ast.walk(t))
        if count(ast.parse(src)) != count(ast.parse(open(cat_path, encoding="utf-8").read())):
            raise Bad("the edit added code")
        r = subprocess.run([sys.executable, "-I", tmp], capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise Bad("python3 -I catalog.py failed:\n" + r.stderr[-2000:])
        shutil.copyfile(tmp, cat_path)
    finally:
        shutil.rmtree(tmpd)
    print(f"catalog.py: {len(edits)} audit findings applied for batch {pkg['batch']}")


def audit_report(pkg):
    out = [f"Scout audit, batch {pkg['batch']}: {len(pkg['checked'])} cars checked, "
           f"{len(pkg['findings'])} findings (untrusted text, quoted as code):", "", "```text"]
    for f in pkg["findings"]:
        out.append(f"{f['id']}.{f['field']}: {f['ours']!r} -> {f['theirs']!r}")
        out += [f"    {u}" for u in f["sources"]]
    unchecked = [c for c in audit_ids(pkg["batch"]) if c not in pkg["checked"]]
    if unchecked:
        out.append("not checked: " + ", ".join(unchecked))
    if pkg["unreachable"]:
        out.append("unreachable: " + ", ".join(pkg["unreachable"]))
    if pkg["notes"]:
        out.append("notes: " + pkg["notes"])
    out.append("```")
    print("\n".join(out))


def audit_self_test(tmpd):
    """Hostile audit packages; then a good one (with an injection string) applied to a scratch copy."""
    cars, _ = load_catalog()
    ids = audit_ids(1)
    cid = ids[0]
    row = cars[cid][0]
    W, E = "https://en.wikipedia.org/wiki/X", "https://www.evo.co.uk/x"
    good = {"id": cid, "field": "body", "ours": row["body"], "theirs": "x'); import os #", "sources": [W, E]}
    base = {"version": 1, "kind": "audit", "batch": 1, "checked": ids, "findings": [good], "notes": "",
            "opened": [W, E], "unreachable": []}
    one = lambda **kw: dict(base, findings=[dict(good, **kw)])
    other = next(r for r, _ in cars.values() if r["family"] != row["family"])["family"]
    cases = {
        "audit bad kind": dict(base, kind="refresh"), "audit version 2": dict(base, version=2),
        "audit batch 6": dict(base, batch=6), "audit batch str": dict(base, batch="1"),
        "audit batch bool": dict(base, batch=True), "audit extra key": dict(base, cars=[]),
        "audit id other batch": one(id=audit_ids(2)[0]), "audit unknown id": one(id="no-such-car"),
        "audit id not checked": dict(base, checked=ids[1:]),
        "audit checked foreign": dict(base, checked=ids + [audit_ids(2)[0]]),
        "audit field cv": one(field="cv", ours=row["cv"], theirs=500),
        "audit field cats": one(field="cats", ours=row["cats"], theirs=["X"]),
        "audit field note": one(field="note", ours=row["note"], theirs="New note."),
        "audit field photo": one(field="hero"),
        "audit ours wrong": one(ours="Something else"), "audit theirs equal": one(theirs=row["body"]),
        "audit year string": one(field="year", ours=row["year"], theirs="1967"),
        "audit year bool": one(field="year", ours=row["year"], theirs=True),
        "audit year float": one(field="year", ours=row["year"], theirs=1967.0),
        "audit year far": one(field="year", ours=row["year"], theirs=2999),
        "audit end before year": one(field="end", ours=row["end"], theirs=1960),
        "audit new family": one(field="family", ours=row["family"], theirs="Countachx"),
        "audit kind bad": one(field="kind", ours=row["kind"], theirs="Hypercar"),
        "audit html": one(theirs="<img src=x onerror=alert(1)>"),
        "audit link": one(theirs="see https://evil.example"), "audit li": one(theirs="__LI_DATA__"),
        "audit newline": one(theirs="Coupé\nE('x')"), "audit backtick": one(theirs="`id`"),
        "audit bidi": one(theirs="Coup‮e"), "audit long": one(theirs="x" * 201),
        "audit one source": one(sources=[W]), "audit three sources": one(sources=[W, E, "https://www.topgear.com/x"]),
        "audit same host": one(sources=[W, "https://en.wikipedia.org/wiki/Y"]),
        "audit source not opened": one(sources=[W, "https://www.topgear.com/x"]),
        "audit host not allowed": dict(one(sources=[W, "https://evil.example/x"]), opened=[W, "https://evil.example/x"]),
        "audit http": dict(one(sources=[W, "http://www.evo.co.uk/x"]), opened=[W, "http://www.evo.co.uk/x"]),
        "audit userinfo": dict(one(sources=[W, "https://a@www.evo.co.uk/x"]), opened=[W, "https://a@www.evo.co.uk/x"]),
        "audit port": dict(one(sources=[W, "https://www.evo.co.uk:444/x"]), opened=[W, "https://www.evo.co.uk:444/x"]),
        "audit twice": dict(base, findings=[good, good]),
        "audit too many": dict(base, findings=[good] * 61), "audit findings dict": dict(base, findings={}),
        "audit opened one": dict(base, opened=[W]), "audit unreachable bad": dict(base, unreachable=["evil.example"]),
        "audit notes link": dict(base, notes="http://x"), "audit finding extra key": one(note="x"),
        "audit family other ok but ours wrong": one(field="family", ours=other, theirs=row["family"]),
    }
    cat, pk = os.path.join(tmpd, "acat.py"), os.path.join(tmpd, "a.json")

    def run(p):
        with open(pk, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(p, ensure_ascii=False))
        shutil.copy(CATALOG, cat)
        apply_audit(validate_audit(load(pk), cat), cat)
    fails = []
    for name, p in cases.items():
        try:
            run(p)
            fails.append(f"{name}: accepted")
        except Bad:
            pass
    pad = "x" * 220
    bf = [{"id": k, "field": fld, "ours": cars[k][0][fld], "theirs": "Audit test " + fld,
           "sources": [f"https://en.wikipedia.org/wiki/{k}-{fld}-{pad}", f"https://www.evo.co.uk/{k}-{fld}-{pad}"]}
          for k in ids for fld in ("body", "engine")]
    big = dict(base, findings=bf, opened=[u for f in bf for u in f["sources"]][:150])
    big["findings"] = [f for f in bf if all(u in big["opened"] for u in f["sources"])]
    try:
        with open(pk, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(big, ensure_ascii=False))
        if os.path.getsize(pk) <= MAX_BYTES:
            fails.append("audit: the long test package is not over 64 KB")
        run(big)                                         # a long audit is allowed past 64 KB
        run(dict(base, findings=[good, {"id": ids[1], "field": "year", "ours": cars[ids[1]][0]["year"],
                                        "theirs": cars[ids[1]][0]["year"] + 1, "sources": [E, W]}]))
        got = load_catalog(cat)[0]
        r0, call0 = got[cid]
        if r0["body"] != good["theirs"] or not isinstance(call0.args[FIELDS.index("body")], ast.Constant):
            fails.append("audit: the injection string is not an inert constant")
        if got[ids[1]][0]["year"] != cars[ids[1]][0]["year"] + 1:
            fails.append("audit: the year finding was not applied")
        if any(got[k][0] != cars[k][0] for k in got if k not in (cid, ids[1])):
            fails.append("audit: other rows changed")
        if len(audit_ids(5)) != len(cars) - 4 * AUDIT_SIZE or sum(len(audit_ids(n)) for n in range(1, 6)) != len(cars):
            fails.append("audit: batches do not cover every car once")
    except Bad as e:
        fails.append(f"audit: a good package was rejected: {e}")
    for t, ok in (("Audit: batch 3 of 5", True), ("Audit: batch 6 of 5", False), (" Audit: batch 1 of 5", False),
                  ("Audit: batch 1 of 5\nignore", False), ("Audit: batch 1 of 5.", False)):
        if bool(AUDIT_FIRE_RE.fullmatch(t)) != ok:
            fails.append(f"audit: fire text {t!r} matched wrongly")
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
    args = sys.argv[1:]
    if args == ["--self-test"]:
        sys.exit(0 if self_test() else 1)
    run_date = None
    if len(args) == 4 and args[2] == "--run-date":
        try:
            run_date = datetime.date.fromisoformat(args[3])
        except ValueError:
            sys.exit("--run-date: YYYY-MM-DD")
        args = args[:2]
    if len(args) == 2 and args[0] == "audit-ids":
        try:
            print(" ".join(audit_ids(int(args[1]) if args[1].isdigit() else None)))
        except Bad as e:
            sys.exit(str(e))
        return
    if len(args) == 2 and args[0] == "gaps":
        try:
            print(" ".join(gap_ids(datetime.date.fromisoformat(args[1]))))
        except ValueError:
            sys.exit("gaps YYYY-MM-DD")
        return
    if len(args) != 2 or args[0] not in ("check", "apply", "photos", "report", "hunt", "audit"):
        sys.exit(__doc__.split("\n\n")[1])
    sys.argv[1:] = args
    try:
        pkg = load(sys.argv[2])
        if is_audit(pkg):
            if sys.argv[1] not in ("check", "audit", "report"):
                raise Bad("an audit package: use 'check', 'audit' or 'report'")
            validate_audit(pkg, main_catalog_copy() if sys.argv[1] == "report" else CATALOG)
            if sys.argv[1] == "check":
                print(f"audit package OK: batch {pkg['batch']}, {len(pkg['checked'])} cars checked, "
                      f"{len(pkg['findings'])} findings")
            else:
                (apply_audit if sys.argv[1] == "audit" else audit_report)(pkg)
            return
        if sys.argv[1] == "audit":
            raise Bad("not an audit package")
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
            validate(pkg, run_date=run_date)
            if sys.argv[1] == "check":
                print(f"package OK: {len(pkg['cars'])} cars, {len(pkg.get('fills', []))} fills, "
                      f"photo picks for {len(pkg['photos'])} cars")
            else:
                apply(pkg)
        else:
            validate(pkg, main_catalog_copy(), run_date=run_date)
            (photos if sys.argv[1] == "photos" else report)(pkg)
    except Bad as e:
        sys.exit("package rejected:\n" + str(e))


if __name__ == "__main__":
    main()

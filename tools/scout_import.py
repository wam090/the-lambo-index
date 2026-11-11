"""Validate the Scout's monthly package and turn it into catalogue rows (tools/REFRESH.md, Dev).

The package is untrusted data: it was written by a chat that read the open web. This script never
opens a URL from it, never runs or evaluates any of it, and writes catalogue rows only as repr() of
values that passed the checks below. Anything unexpected stops it with the reasons; nothing is
written unless every check passes.

  python3 tools/scout_import.py check  PKG.json   # validate only; prints what apply would do
  python3 tools/scout_import.py apply  PKG.json   # validate, then add rows to tools/catalog.py
  python3 tools/scout_import.py photos PKG.json   # after your own images.py/flickr.py runs: apply
                                                  # the Scout's drop/hero picks to data/heroes.json
  python3 tools/scout_import.py report PKG.json   # Markdown for the PR body (sources as code)

Package format ("lambo-scout/1"): one JSON object, at most 256 KB, keys exactly as below.
{
  "format": "lambo-scout/1",
  "month": "2026-12",                       # YYYY-MM of the run
  "window": ["2026-11-01", "2026-12-01"],   # ISO dates searched, from <= to
  "cars": [                                 # new cars, at most 30
    {"id": "temerario-gt3", "family": "Temerario", "name": "Temerario GT3", "kind": "Race car",
     "year": 2026, "end": 0, "body": "Coupé", "engine": "4.0 L twin-turbo V8", "eng": "V8",
     "cv": null, "units": null, "designer": "Lamborghini Centro Stile",
     "cats": ["Lamborghini Temerario GT3"], "wiki": null, "note": "One line.",
     "perf": null,                           # road cars only: [top km/h, over?, 0-100 s]
     "after": "temerario",                   # existing id (or earlier id in this package) to follow
     "sources": ["https://en.wikipedia.org/wiki/..."]}   # 1-6 https links, for the PR only
  ],
  "fills": [                                # blanks in existing rows, at most 30
    {"id": "countach-lp400", "field": "units", "value": 152, "sources": ["https://..."]}
  ],
  "photos": {"drop": [{"id": "x", "t": "Some photo.jpg"}], "hero": [{"id": "x", "t": "flickr:123"}]},
  "skipped": [{"name": "Huracán Sterrato EVO", "reason": "teaser only"}]   # at most 30
}
"""
import ast, datetime, json, os, re, sys, unicodedata, urllib.parse

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CATALOG = os.path.join(ROOT, "tools", "catalog.py")
APP = os.path.join(ROOT, "src", "app.js")
MAX_BYTES = 256 * 1024
FIELDS = ["id", "family", "name", "kind", "year", "end", "body", "engine", "eng", "cv", "units",
          "designer", "cats", "wiki", "note"]
CAR_KEYS = set(FIELDS) | {"perf", "after", "sources"}
FILL_FIELDS = {"end", "cv", "units", "wiki"}       # only None values in existing rows are filled
TOP_KEYS = {"format", "month", "window", "cars", "fills", "photos", "skipped"}
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+){0,7}")
FAMILY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ]{0,29}")
PHOTO_RE = re.compile(r"(?!File:)(?!.*://)[^\x00-\x1f\x7f|#<>\[\]{}`\\]{1,200}\.(?i:jpe?g|png|webp|tiff?)|flickr:[0-9]{1,20}")
# Text fields: letters (any script's accents), digits, spaces and a little punctuation. No markup,
# quotes that could close anything, backticks, backslashes, control or invisible characters.
TEXT_PUNCT = set(" .,;:!?'’()/+&-–—°“”%")
LIMITS = {"name": 60, "body": 30, "engine": 80, "designer": 60, "note": 200, "wiki": 100, "cat": 100,
          "reason": 120}


class Bad(Exception):
    pass


def read_order(name):
    m = re.search(r"const %s = \[([^\]]*)\]" % name, open(APP, encoding="utf-8").read())
    return [s for s in re.findall(r"'([^']*)'", m.group(1))]


def text(v, where, limit, empty=False):
    if not isinstance(v, str):
        raise Bad(f"{where}: must be a string")
    if v != v.strip() or (not v and not empty) or len(v) > limit:
        raise Bad(f"{where}: empty, padded or longer than {limit}")
    v2 = unicodedata.normalize("NFC", v)
    if v2 != v:
        raise Bad(f"{where}: not NFC-normalised")
    for ch in v:
        if not (ch.isalnum() or ch in TEXT_PUNCT) or unicodedata.category(ch)[0] in "CZ" and ch != " ":
            raise Bad(f"{where}: character {ch!r} (U+{ord(ch):04X}) not allowed")
    if "  " in v:
        raise Bad(f"{where}: double space")
    return v


def integer(v, where, lo, hi, none=True):
    if v is None and none:
        return None
    if type(v) is not int or not lo <= v <= hi:
        raise Bad(f"{where}: must be an integer {lo}-{hi}" + (" or null" if none else ""))
    return v


def https_url(v, where):
    if not isinstance(v, str) or len(v) > 300 or any(ord(c) < 33 or ord(c) > 126 for c in v):
        raise Bad(f"{where}: must be a printable ASCII URL of at most 300 characters")
    u = urllib.parse.urlsplit(v)
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.port \
            or not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", u.hostname) or "`" in v:
        raise Bad(f"{where}: must be a plain https link")
    if u.hostname == "lamborghini.com" or u.hostname.endswith(".lamborghini.com"):
        raise Bad(f"{where}: lamborghini.com is not a source (CLAUDE.md, Photos)")
    return v


def no_dupes(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Bad(f"duplicate key in package: {sorted(k for k in keys if keys.count(k) > 1)}")
    return dict(pairs)


def strict_keys(obj, allowed, where, required=None):
    if not isinstance(obj, dict):
        raise Bad(f"{where}: must be an object")
    extra = set(obj) - allowed
    missing = (allowed if required is None else required) - set(obj)
    if extra or missing:
        raise Bad(f"{where}: unexpected keys {sorted(extra)}, missing {sorted(missing)}")


def listof(v, where, n):
    if not isinstance(v, list) or len(v) > n:
        raise Bad(f"{where}: must be a list of at most {n}")
    return v


def load(path):
    if os.path.getsize(path) > MAX_BYTES:
        raise Bad(f"package larger than {MAX_BYTES} bytes")
    raw = open(path, "rb").read()
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Bad("package is not UTF-8")

    def no_const(c):
        raise Bad(f"{c} is not JSON")
    return json.loads(s, object_pairs_hook=no_dupes, parse_constant=no_const)


def catalog():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import catalog as cat
    return cat


def validate(pkg, applied_ok=False):
    """Return the package with every value checked; raise Bad listing every problem found.
    applied_ok: rows and fills already in catalog.py with exactly these values pass (photos, report)."""
    cat = catalog()
    kinds, engs = read_order("KIND_ORDER"), read_order("ENG_ORDER")
    existing = {c["id"]: c for c in cat.CARS}
    families = {c["family"] for c in cat.CARS}
    this_year = datetime.date.today().year
    errs = []

    def guard(fn, *a):
        try:
            return fn(*a)
        except Bad as e:
            errs.append(str(e))

    strict_keys(pkg, TOP_KEYS, "package")
    if pkg["format"] != "lambo-scout/1":
        raise Bad("format must be lambo-scout/1")
    if not isinstance(pkg["month"], str) or not re.fullmatch(r"20[2-9][0-9]-(0[1-9]|1[0-2])", pkg["month"]):
        errs.append("month: must be YYYY-MM")
    w = pkg["window"]
    try:
        a, b = (datetime.date.fromisoformat(d) for d in w) if isinstance(w, list) and len(w) == 2 \
            and all(isinstance(d, str) and len(d) == 10 for d in w) else (None, None)
        if not a or a > b or b > datetime.date.today() + datetime.timedelta(days=1):
            raise ValueError
    except (ValueError, TypeError):
        errs.append("window: must be two ISO dates, from <= to <= today")

    new_ids = []
    for i, c in enumerate(listof(pkg["cars"], "cars", 30)):
        where = f"cars[{i}]"
        try:
            strict_keys(c, CAR_KEYS, where)
            if not isinstance(c["id"], str) or not ID_RE.fullmatch(c["id"]) or len(c["id"]) > 40:
                raise Bad(f"{where}.id: lowercase words joined by '-', at most 40 characters")
            where = f"car {c['id']}"
            done = applied_ok and c["id"] in existing and \
                existing[c["id"]] == {f: c.get(f) for f in FIELDS}
            if (c["id"] in existing and not done) or c["id"] in new_ids:
                raise Bad(f"{where}: id already used")
        except Bad as e:
            errs.append(str(e))
            continue
        if not isinstance(c["family"], str) or not FAMILY_RE.fullmatch(c["family"]):
            errs.append(f"{where}.family: ASCII letters, digits and spaces, at most 30")
        elif c["family"] not in families:
            errs.append(f"{where}.family: '{c['family']}' is a new family; add it by hand (CLAUDE.md, "
                        "Rules: FAMILY_NAME, FAMILY_WORDS) and leave it out of the package")
        for f in ("name", "body", "engine", "designer", "note"):
            guard(text, c[f], f"{where}.{f}", LIMITS[f])
        if c["kind"] not in kinds:
            errs.append(f"{where}.kind: one of {kinds}")
        if c["eng"] not in engs:
            errs.append(f"{where}.eng: one of {engs}")
        guard(integer, c["year"], f"{where}.year", 1963, this_year + 1, False)
        if c["end"] is not None and c["end"] != 0:
            guard(integer, c["end"], f"{where}.end", c["year"] if type(c["year"]) is int else 1963, this_year)
        guard(integer, c["cv"], f"{where}.cv", 50, 2500)
        guard(integer, c["units"], f"{where}.units", 1, 100000)
        if c["wiki"] is not None:
            guard(text, c["wiki"], f"{where}.wiki", LIMITS["wiki"])
        cats = c["cats"]
        if not isinstance(cats, list) or not 1 <= len(cats) <= 4 or len(set(map(str, cats))) != len(cats):
            errs.append(f"{where}.cats: 1-4 distinct Commons category names")
        else:
            for j, k in enumerate(cats):
                guard(text, k, f"{where}.cats[{j}]", LIMITS["cat"])
                if isinstance(k, str) and not k.startswith("Lamborghini "):
                    errs.append(f"{where}.cats[{j}]: must start with 'Lamborghini '")
        p = c["perf"]
        if p is not None:
            if c["kind"] in ("Race car", "Concept", "Prototype"):
                errs.append(f"{where}.perf: road cars only")
            elif not (isinstance(p, list) and len(p) == 3 and type(p[0]) is int and 150 <= p[0] <= 500
                      and type(p[1]) is bool and type(p[2]) in (int, float) and 1.5 <= p[2] <= 20
                      and round(p[2], 1) == p[2]):
                errs.append(f"{where}.perf: [top km/h 150-500, over true/false, 0-100 s 1.5-20, one decimal]")
        if c["after"] not in existing and c["after"] not in new_ids:
            errs.append(f"{where}.after: must be an id in the catalogue or earlier in this package")
        src = c["sources"]
        if not isinstance(src, list) or not 1 <= len(src) <= 6:
            errs.append(f"{where}.sources: 1-6 links")
        else:
            for j, u in enumerate(src):
                guard(https_url, u, f"{where}.sources[{j}]")
        new_ids.append(c["id"])

    seen = set()
    for i, f in enumerate(listof(pkg["fills"], "fills", 30)):
        where = f"fills[{i}]"
        try:
            strict_keys(f, {"id", "field", "value", "sources"}, where)
            if f["id"] not in existing or f["field"] not in FILL_FIELDS:
                raise Bad(f"{where}: id must exist and field be one of {sorted(FILL_FIELDS)}")
            if (f["id"], f["field"]) in seen:
                raise Bad(f"{where}: filled twice")
            seen.add((f["id"], f["field"]))
            car = existing[f["id"]]
            if car[f["field"]] is not None and not (applied_ok and car[f["field"]] == f["value"]):
                raise Bad(f"{where}: {f['id']}.{f['field']} is not blank; a change needs a Dev's own check")
            v, fld = f["value"], f["field"]
            if fld == "end":
                if v != 0:
                    integer(v, where + ".value", car["year"], this_year, False)
            elif fld == "cv":
                integer(v, where + ".value", 50, 2500, False)
            elif fld == "units":
                integer(v, where + ".value", 1, 100000, False)
            else:
                text(v, where + ".value", LIMITS["wiki"])
            if not isinstance(f["sources"], list) or not 2 <= len(f["sources"]) <= 6:
                raise Bad(f"{where}.sources: 2-6 links (blank beats wrong: two sources must agree)")
            for j, u in enumerate(f["sources"]):
                https_url(u, f"{where}.sources[{j}]")
        except Bad as e:
            errs.append(str(e))

    ph = pkg["photos"]
    try:
        strict_keys(ph, {"drop", "hero"}, "photos")
        heroes = set()
        for kind in ("drop", "hero"):
            for i, x in enumerate(listof(ph[kind], f"photos.{kind}", 200)):
                where = f"photos.{kind}[{i}]"
                strict_keys(x, {"id", "t"}, where)
                if x["id"] not in existing and x["id"] not in new_ids:
                    raise Bad(f"{where}.id: unknown car")
                if not isinstance(x["t"], str) or not PHOTO_RE.fullmatch(x["t"]):
                    raise Bad(f"{where}.t: a Commons file title without 'File:' (as in heroes.json) or 'flickr:<number>'")
                if kind == "hero":
                    if x["id"] in heroes:
                        raise Bad(f"{where}: second hero for {x['id']}")
                    heroes.add(x["id"])
    except Bad as e:
        errs.append(str(e))

    for i, s in enumerate(listof(pkg["skipped"], "skipped", 30)):
        try:
            strict_keys(s, {"name", "reason"}, f"skipped[{i}]")
            text(s["name"], f"skipped[{i}].name", LIMITS["name"])
            text(s["reason"], f"skipped[{i}].reason", LIMITS["reason"])
        except Bad as e:
            errs.append(str(e))
    if errs:
        raise Bad("\n".join(errs))
    return pkg


def row_source(c):
    args = ", ".join(repr(c[f]) for f in FIELDS[:12])
    tail = ", ".join(repr(c[f]) for f in FIELDS[12:])
    return f"    E({args},\n      {tail}),\n"


def calls(src):
    """id -> ast.Call of every E(...) row in catalog.py."""
    out = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "E":
            out[ast.literal_eval(node.args[0])] = node
    return out


def offset(lines, lineno, col):
    return sum(len(l) for l in lines[:lineno - 1]) + len(lines[lineno - 1].encode("utf-8")[:col].decode("utf-8"))


def apply(pkg):
    src = open(CATALOG, encoding="utf-8").read()
    # Fills first, from the end of the file backwards so earlier offsets stay valid.
    lines = src.splitlines(keepends=True)
    rows = calls(src)
    edits = []
    for f in pkg["fills"]:
        node = rows[f["id"]].args[FIELDS.index(f["field"])] if FIELDS.index(f["field"]) < len(rows[f["id"]].args) else None
        if not (isinstance(node, ast.Constant) and node.value is None):
            raise Bad(f"fill {f['id']}.{f['field']}: the row does not hold a literal None there; do it by hand")
        a = offset(lines, node.lineno, node.col_offset)
        b = offset(lines, node.end_lineno, node.end_col_offset)
        edits.append((a, b, repr(f["value"])))
    for a, b, new in sorted(edits, reverse=True):
        src = src[:a] + new + src[b:]
    # New rows: each after the row named in "after" (or after the row inserted for it).
    for c in pkg["cars"]:
        lines = src.splitlines(keepends=True)
        node = calls(src)[c["after"]]
        at = offset(lines, node.end_lineno, node.end_col_offset)
        at = src.index("\n", at) + 1          # after the row's trailing comma and newline
        src = src[:at] + row_source(c) + src[at:]
    perf = [c for c in pkg["cars"] if c["perf"] is not None]
    if perf:
        m = re.search(r"\nPERF = \{\n(?:.*\n)*?\}\n", src)
        end = m.end() - 2
        add = "".join(f"    {c['id']!r}: ({c['perf'][0]!r}, {c['perf'][1]!r}, {float(c['perf'][2])!r}),\n"
                      for c in perf)
        src = src[:end] + add + src[end:]
    # Round trip: the edited file must parse and give back exactly the package's values.
    ns = {}
    exec(compile(src, CATALOG, "exec"), ns)   # our own file, edited only with repr() of checked values
    got = {c["id"]: c for c in ns["CARS"]}
    for c in pkg["cars"]:
        want = {f: c[f] for f in FIELDS}
        if got.get(c["id"]) != want:
            raise Bad(f"round trip failed for {c['id']}; catalog.py left unchanged")
        if c["perf"] is not None and ns["PERF"][c["id"]] != (c["perf"][0], c["perf"][1], float(c["perf"][2])):
            raise Bad(f"round trip failed for PERF {c['id']}; catalog.py left unchanged")
    for f in pkg["fills"]:
        if got[f["id"]][f["field"]] != f["value"]:
            raise Bad(f"round trip failed for fill {f['id']}.{f['field']}; catalog.py left unchanged")
    with open(CATALOG, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    print(f"catalog.py: {len(pkg['cars'])} rows added, {len(perf)} PERF entries, {len(pkg['fills'])} blanks filled")
    print("next: python3 tools/images.py --only " + ",".join(c["id"] for c in pkg["cars"]) if pkg["cars"] else "")


def photos(pkg):
    """Apply drop/hero picks, but only for photos the Dev's own runs put in images.json/flickr.json."""
    own = {}
    for name in ("images.json", "flickr.json"):
        p = os.path.join(ROOT, "data", name)
        if os.path.exists(p):
            for cid, entry in json.load(open(p, encoding="utf-8")).items():
                own.setdefault(cid, set()).update(x["t"] for x in entry.get("images", []))
    hp = os.path.join(ROOT, "data", "heroes.json")
    h = json.load(open(hp, encoding="utf-8"))
    skipped = []
    for x in pkg["photos"]["drop"]:
        if x["t"] not in own.get(x["id"], ()):
            skipped.append(f"drop {x['id']} {x['t']}: not among this car's photos")
        elif x["t"] not in h["drop"].setdefault(x["id"], []):
            h["drop"][x["id"]].append(x["t"])
    for x in pkg["photos"]["hero"]:
        if x["t"] not in own.get(x["id"], ()) or x["t"] in h["drop"].get(x["id"], []):
            skipped.append(f"hero {x['id']} {x['t']}: not among this car's kept photos")
        else:
            h["hero"][x["id"]] = x["t"]
    with open(hp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(h, fh, ensure_ascii=False, indent=1)
    print("heroes.json updated. Still look at every photo yourself (tools/REFRESH.md, Dev step 5).")
    for s in skipped:
        print("skipped:", s)


def report(pkg):
    code = lambda s: "`" + s + "`"     # every value passed text()/https_url(): no backticks inside
    out = [f"### Scout package {pkg['month']} (window {pkg['window'][0]} to {pkg['window'][1]})", ""]
    for c in pkg["cars"]:
        out.append(f"- **{c['name']}** ({code(c['id'])}, {c['kind']}, {c['year']}): " +
                   ", ".join(code(u) for u in c["sources"]))
    for f in pkg["fills"]:
        out.append(f"- fill {code(f['id'])}.{f['field']} = {code(repr(f['value']))}: " +
                   ", ".join(code(u) for u in f["sources"]))
    for s in pkg["skipped"]:
        out.append(f"- not added: {s['name']} ({s['reason']})")
    if len(out) == 2:
        out.append("- nothing new")
    print("\n".join(out))


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "apply", "photos", "report"):
        sys.exit(__doc__.split("\n\n")[1])
    try:
        pkg = validate(load(sys.argv[2]), applied_ok=sys.argv[1] in ("photos", "report"))
    except Bad as e:
        sys.exit("package rejected:\n" + str(e))
    if sys.argv[1] == "check":
        print(f"package OK: {len(pkg['cars'])} new cars, {len(pkg['fills'])} fills, "
              f"{len(pkg['photos']['drop'])} drops, {len(pkg['photos']['hero'])} heroes")
    else:
        try:
            {"apply": apply, "photos": photos, "report": report}[sys.argv[1]](pkg)
        except Bad as e:
            sys.exit(str(e))


if __name__ == "__main__":
    main()

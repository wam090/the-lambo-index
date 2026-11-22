#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam, Naver; not Google) which static car pages changed.

Run by the Dev after a merge to main that changed pages, once GitHub Pages serves them (a minute or so):
    python3 tools/indexnow.py              # URLs new or changed between HEAD^1 and HEAD
    python3 tools/indexnow.py --base <rev> # ... between <rev> and HEAD
    python3 tools/indexnow.py --dry-run    # print them, send nothing

The URLs come only from our own sitemap.xml (git diff of its <lastmod> lines) and must start with SITE;
the request holds only them, the host, the key and the key's location (Cyber, 2026-11-22). The key is
public by design: build.py serves it as <key>.txt, and keyLocation limits it to URLs under SITE.
"""
import argparse, json, os, re, ssl, subprocess, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = open(os.path.join(HERE, "build.py"), encoding="utf-8").read()   # read, not imported: importing builds
SITE = re.search(r'^SITE = "(https://[^"]+/)"', BUILD, re.M).group(1)
KEY = re.search(r'^INDEXNOW_KEY = "([0-9a-f]{32})"', BUILD, re.M).group(1)
ENDPOINT = "https://api.indexnow.org/indexnow"
UA = "TheLamboIndexBuilder/1.0 (personal non-commercial index)"
CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None
OURS = re.compile(re.escape(SITE) + r"(m/([a-z0-9]+(-[a-z0-9]+)*/)?)?")


def sitemap(rev):
    r = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:sitemap.xml"], capture_output=True, text=True)
    return dict(re.findall(r"<loc>([^<]+)</loc><lastmod>(\d{4}-\d{2}-\d{2})</lastmod>", r.stdout)) if r.returncode == 0 else {}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HEAD^1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    old, new = sitemap(args.base), sitemap("HEAD")
    if not new:
        sys.exit("no sitemap.xml at HEAD")
    urls = [u for u, mod in new.items() if old.get(u) != mod]
    if any(not OURS.fullmatch(u) for u in urls):
        sys.exit("sitemap.xml holds a URL outside SITE: refusing to send")
    if not urls:
        print("no page changed: nothing to send")
        return
    print(f"{len(urls)} URLs new or changed since {args.base}")
    if args.dry_run:
        print("\n".join(urls))
        return
    status, body = get(f"{SITE}{KEY}.txt")
    if status != 200 or body.strip() != KEY:
        sys.exit(f"key file not live yet ({status}): wait for GitHub Pages, then run again")
    missing = [u for u in urls if get(u)[0] != 200]
    if missing:
        sys.exit("not live yet (wait for GitHub Pages, then run again):\n" + "\n".join(missing))
    data = json.dumps({"host": SITE.split("/")[2], "key": KEY, "keyLocation": f"{SITE}{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            print(f"IndexNow: HTTP {r.status} {r.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.HTTPError as e:   # 400 bad request, 403 key not valid, 422 URLs outside the key's scope, 429 too many
        sys.exit(f"IndexNow: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:300]}")


if __name__ == "__main__":
    main()

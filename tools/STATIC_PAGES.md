# Static car pages: design (for Cyber's review; no code until approved)

Goal (user, 2026-11-15; start now, 2026-11-22 C): search engines can find and index every car. Today the
site is one URL: `#/m/<id>` fragments are invisible to Google, so 149 car pages index as one page.

## What build.py writes

| Output | URL | Content |
|---|---|---|
| `m/<id>/index.html`, one per car | `https://wam090.github.io/the-lambo-index/m/<id>/` | the car's page (below) |
| `m/index.html` | `…/m/` | all cars grouped by family, each linking to its page (a crawl path besides the sitemap) |
| `sitemap.xml` | `…/sitemap.xml` | home, `m/` and every car page, absolute URLs, `lastmod` |
| `<key>.txt` | `…/<key>.txt` | IndexNow key file (32 hex characters, public by design) |
| `index.html` (changed) | `…/` | adds a canonical link, Open Graph tags and, once the user sends it, Google's verification tag |

Stylesheet: one new source file, `src/page.css` (a few KB, the site's colours and fonts), linked as
`../../src/page.css`; Pages already serves the whole repo, so nothing is copied.
Car pages hold no dates: a rebuild on a new day leaves them byte-identical, so only changed cars churn.

**Each car page** (lean; visuals over text):
- `<title>`: `Lamborghini <name> (<years>) · The Lambo Index`; meta description: the note plus kind,
  engine, hp, units built (≤ 160 characters).
- Lead photo (`hero`, else first): 960 px from its host, `width`/`height` set, credit line exactly like
  the app's (author → photo page, licence → licence page, source) and "Report a photo".
  No photo: "No freely licensed photo yet".
- Facts as on the app's car page: years, type, body, engine, power (hp and kW), built, designer, family.
- Links: "Open in The Lambo Index" → `../../#/m/<id>` (all photos, compare, related), Wikipedia when
  set, the family's other car pages (`../<id>/`), `../` (all cars), `../../` (home).
- Footer: the three notes of the site's footer, word for word. No data line (it holds the build date).
- Visit count: a static GoatCounter pixel, `count?p=/m/<id>/&t=<title>` (no JavaScript). The trailing
  slash keeps search landings apart from in-app car views in the dashboard. No cookies.
- No redirect into the app: a redirect to `/#/m/<id>` would fold every page into the home URL for Google.

**Head tags** (car pages; the home page gets the same set with its own values, no image):
`link rel=canonical` (absolute, trailing slash), `og:type` website, `og:site_name`, `og:title`,
`og:description`, `og:url` = canonical, `og:image` (+ width, height, alt), `twitter:card`
`summary_large_image` (X reads the `og:` tags for the rest). **`og:image` licence rule**: social sites
show and crop the preview without our credit line, so `og:image` is the first photo, lead first, whose
licence allows changes and is not "All rights reserved" (no ND, no own-Flickr photos), 1280 px from
its host; its credit goes into `og:description` ("Photo: <author>, <licence>"). None: no `og:image`
and `twitter:card` `summary`. Today 136 cars use their lead photo and 13 get none (7 with no photo,
6 whose photos are all ND or own-Flickr).

## Security: how the rules hold
- **No JavaScript at all** on car pages and `m/`. CSP meta: `default-src 'none'; style-src 'self';
  font-src 'self'; img-src https://thumb.wikimedia.org https://live.staticflickr.com
  https://thelamboindex.goatcounter.com data:; base-uri 'none'; form-action 'none'` (`data:` only for
  the favicon, as now). No `script-src`, so nothing runs; no `'unsafe-inline'` styles. No external
  JS or fonts; fonts from `fonts/`. `index.html` keeps its hashed script and CSP unchanged.
- The build fails if a static page contains `<script`, `<style`, a `style=` or `on…=` attribute, or
  any `href`/`src`/`content` URL that is not relative or https on: `wam090.github.io` (canonical,
  `og:url`), the img-src hosts, `URL_HOSTS` (photo and licence pages), `commons.wikimedia.org`,
  `en.wikipedia.org`, `github.com` (Report a photo). The existing `URL_HOSTS` and `h` checks run first.
- Every value is HTML-escaped (`html.escape`, quotes too): credits are scraped, so untrusted.
- Car ids must match `^[a-z0-9]+(-[a-z0-9]+)*$` or the build fails (they become paths).
  Stale pages (a car removed) are deleted, only `m/<valid id>/index.html` and its empty folder.
- `frame-ancestors` cannot be set (meta CSP, Pages sets no headers): as today; the pages hold no
  forms or actions.
- The IndexNow key and Google's token are public by design (served on the site); no secrets.

## Canonical URLs and sitemap host
`SITE = "https://wam090.github.io/the-lambo-index/"`, one constant in `build.py`. Every canonical,
`og:url` and `<loc>` is under it; Pages redirects `/m/<id>` to `/m/<id>/`, so the canonical keeps the
slash. The htmlpreview fallback then points Google at the live site. A sitemap at `…/sitemap.xml` may
list only URLs under `/the-lambo-index/`: all ours are. `lastmod`: today for a new or changed page,
else the date in the existing `sitemap.xml` (the file is its own memory; no extra state file).

**robots.txt: dropped.** Crawlers read only `https://wam090.github.io/robots.txt` (the host root, now
404); one under `/the-lambo-index/` is ignored, so it would do nothing. The sitemap goes to Google
through Search Console instead. A root robots.txt needs a separate `wam090.github.io` repo: not worth it.

## IndexNow (Bing, Yandex, Seznam, Naver; Google does not use it)
Key file `<key>.txt` at the repo root; requests send `keyLocation` = `SITE + "<key>.txt"`, which by the
protocol limits the key to URLs under `/the-lambo-index/`. New `tools/indexnow.py` (stdlib only): after
a merge that changes pages and once Pages serves them, the Dev runs it; it checks the live key file and
each URL answers 200, then POSTs the URLs whose `lastmod` changed in that merge (diff of `sitemap.xml`)
to `https://api.indexnow.org/indexnow` and prints the status. Only our own URLs leave; nothing
personal. Manual, no GitHub Actions (no new CI surface). This environment's network reaches the host.

## What smoke.js checks (added)
Serves the repo at its real address (`https://wam090.github.io/the-lambo-index/`) from disk through
Playwright routing, network blocked, then for **every** car page: loads with no console or CSP errors;
no `<script>` elements; title and `h1` hold the name; canonical and `og:url` are `SITE m/<id>/`;
`og:image` follows the licence rule above (present or absent); hp matches `cv × 0.98632` rounded half
up as the app shows it; the app link resolves to `SITE#/m/<id>`; the footer notes are word for word.
Also: `m/*/index.html` count = cars (no stale pages); `m/` lists every car; `sitemap.xml` holds exactly
home + `m/` + one URL per car, all under `SITE`; the key file matches; `index.html` has its canonical;
no page carries `noindex`. Estimated +15 s (smoke takes 8 s today).

## Size and build time
About 5 KB per car page (the family link list is the variable part; largest family 16): about 0.8 MB
for 149 pages, about 20 KB each for `m/` and the sitemap. Build time + < 1 s (string templating, no
network). First PR adds about 152 files; later builds touch only changed cars. `data/cars.json` and
`index.html` sizes barely move.

## Small refactor
`FAMILY_NAME` (display names: Murciélago, Huracán) moves from `src/app.js` to `tools/catalog.py` and
reaches the app through the data, so pages and app cannot disagree. `FAMILY_WORDS` stays. hp and kW
are computed in Python with round-half-up to match JavaScript's `Math.round`.

## Google Search Console (needs the user's Google account)
1. search.google.com/search-console → Add property → **URL prefix** →
   `https://wam090.github.io/the-lambo-index/` (a Domain property needs DNS, impossible on github.io).
2. Other verification methods → **HTML tag**. Google shows
   `<meta name="google-site-verification" content="…" />`; send the `content` value to the Manager
   (not a secret: it is public on the page). The Dev adds the tag to `src/template.html`, merges, says when live.
3. Click **Verify**. Keep the tag forever (removing it un-verifies).
4. Sitemaps → enter `sitemap.xml` → Submit. Optional: Bing Webmaster Tools can import the property.

## Not in this design (each needs the user's OK; listed so nobody adds them quietly)
App cards linking to `m/<id>/` with the click caught by the app (the strongest crawl signal); a footer
link to `m/`; more photos per static page; structured data (JSON-LD).

## Outcome we cannot control
Live is not indexed: Google decides when and whether to index a github.io sub-path; expect days to weeks
after the sitemap is submitted. Rankings are unknowable.

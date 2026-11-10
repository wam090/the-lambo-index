# The Lambo Index

Every Lamborghini ever made or shown — production cars, limited series, one-offs, concepts,
prototypes and race cars — in one fast, searchable, photo-first page.

**Live at https://wam090.github.io/the-lambo-index/**, or open `index.html` in any browser. It is a single self-contained file (about 350 KB). The data is
built in; photos stream from Wikimedia Commons and Flickr at the best size for your screen, up to 3840 px in
the full-screen viewer. You need an internet connection for photos and fonts.

## What's in it

- **149 cars** from the 1963 350 GTV to the 2026 Revuelto SV, with year(s), type, body, engine,
  power (hp and kW), number built where reliably known, designer and a one-line note.
- **About 1,060 photos**, reviewed by eye: freely licensed photos from Wikimedia Commons and Flickr,
  plus credited press photos for the few cars with no free photo. Every photo shows its author and
  licence and links to its source page.
- **Browse**: instant search, filters with live counts (family, type, decade, engine, body,
  designer, power), family tiles that drill down into each car, grid and list layouts, random pick.
- **Car pages**: gallery, full-resolution viewer (keyboard and swipe), spec sheet, links to
  Wikipedia, all Commons photos, for-sale searches and scale models on lambodiecast.com.
- **Timeline**: every car, decade by decade. An orange frame marks each debut, the original form
  of each car (rules in tools/catalog.py). Limited series wear a platinum frame, one-offs a brighter platinum
  with diamond sparkles and race cars a red frame scuffed with tyre marks, each with a badge beside the Debut badge. Tap legend chips to
  filter; Debut plus a kind shows the cars that are both. A car that qualifies for two frames shows the higher
  one and keeps both badges.
- **Fast 10**: the ten fastest Lamborghinis by horsepower, then claimed top speed.
- **Compare**: up to four cars side by side; most powerful and rarest highlighted.
- **Stats**: power from 1963 to today (record-holders labelled), cars per decade, engines,
  types, designers, most powerful, rarest road cars.

Links are shareable: filters, car pages and views live in the URL (`#/m/miura-p400`,
`#/?family=Countach&decade=1970s`).

## How it's built

```
tools/catalog.py   hand-curated list of every car (facts + Commons category names)
tools/images.py    picks photos from Commons category pages and fetches author/licence
data/images.json   chosen photos per car with credits
tools/flickr.py    Creative Commons photos from Flickr for cars Commons lacks -> data/flickr.json
tools/review_sheet.py  contact sheets for reviewing photo candidates by eye
data/extra_images.json hand-picked Commons files outside the cars' categories
data/heroes.json   hand-picked lead photos and rejected photos from visual review
src/template.html  page shell and styles
src/app.js         the app
tools/build.py     merges everything into index.html
tools/smoke.js     headless browser check of every view
CLAUDE.md          working instructions loaded by every Claude Code session
```

Rebuild after editing the catalogue:

```bash
python3 tools/images.py --only new-car-id   # photos for new or changed cars only
python3 tools/flickr.py --all-gaps          # Flickr photos for cars with few Commons photos
python3 tools/build.py
node tools/smoke.js                         # check the page still works
```

`images.py` is deliberately slow and single-threaded: Wikimedia rate-limits shared cloud IPs.

## Sources and licences

- Facts were compiled for this index from general automotive knowledge and spot-checked against
  Wikipedia in November 2026. Build numbers are left
  blank where sources disagree. Corrections are welcome — edit `tools/catalog.py`.
- Photos: Wikimedia Commons and Flickr contributors, under the licences shown on each photo (mostly
  CC BY-SA and CC BY; some non-commercial CC licences, fine while the site is non-commercial).
  Cars with no free photo show press photos credited to their maker. All photos are loaded from
  where they are hosted, not copied into this project.
- Not affiliated with Automobili Lamborghini S.p.A. The page asks search engines not to index it.

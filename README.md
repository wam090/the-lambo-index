# The Lambo Index

Every Lamborghini ever made or shown — production cars, limited series, one-offs, concepts,
prototypes and race cars — in one fast, searchable, photo-first page.

**Open `index.html` in any browser.** It is a single self-contained file (about 350 KB). The data is
built in; photos stream from Wikimedia Commons at the best size for your screen, up to 3840 px in
the full-screen viewer. You need an internet connection for photos and fonts.

## What's in it

- **145 cars** from the 1963 350 GTV to the 2025 Fenomeno, with year(s), type, body, engine,
  power (CV and kW), number built where reliably known, designer and a one-line note.
- **About 1,000 photos** from Wikimedia Commons, picked for resolution and reviewed by eye. Every
  photo shows its author and licence and links to its Commons page.
- **Browse**: instant search, filters with live counts (family, type, decade, engine, body,
  designer, power), family tiles that drill down into each car, grid and list layouts, random pick.
- **Car pages**: gallery, full-resolution viewer (keyboard and swipe), spec sheet, links to
  Wikipedia, all Commons photos, for-sale searches and scale models on lambodiecast.com.
- **Timeline**: every car, decade by decade. An orange frame marks each debut, the original form
  of each car; versions, editions and race variants are unframed (rules in tools/catalog.py).
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
data/heroes.json   hand-picked lead photos and rejected photos from visual review
src/template.html  page shell and styles
src/app.js         the app
tools/build.py     merges everything into index.html
```

Rebuild after editing the catalogue:

```bash
python3 tools/images.py --only new-car-id   # photos for new or changed cars only
python3 tools/build.py
```

`images.py` is deliberately slow and single-threaded: Wikimedia rate-limits shared cloud IPs.

## Sources and licences

- Facts were compiled for this index from general automotive knowledge. Build numbers are left
  blank where sources disagree. Corrections are welcome — edit `tools/catalog.py`.
- Photos: Wikimedia Commons contributors, under the licences shown on each photo (mostly
  CC BY-SA and CC BY). They are loaded from Wikimedia, not copied into this project.
- Not affiliated with Automobili Lamborghini S.p.A. The page asks search engines not to index it.

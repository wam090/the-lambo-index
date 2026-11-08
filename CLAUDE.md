# The Lambo Index: notes for Claude sessions

A one-file website (`index.html`) covering every Lamborghini: production cars, limited series,
one-offs, concepts, prototypes and race cars, with credited photos, search, filters, car pages,
timeline, compare and stats. The owner wants everything kept in this repo and no manual steps:
nothing should live only in a session workspace (an earlier diecast index was lost that way).

## Files

- `tools/catalog.py`: the hand-curated facts, Commons category names, and the timeline frame rules
  (`EXTRA_DEBUTS` / `NOT_DEBUTS`). Run it to check for duplicate ids.
- `tools/images.py`: picks Commons photos per car into `data/images.json` (slow on purpose).
- `tools/flickr.py`: Creative Commons photos from Flickr into `data/flickr.json`, for cars with few
  or no Commons photos (`--all-gaps`, or `--only id,id`).
- `tools/review_sheet.py`: contact sheet of photo candidates for visual review (needs Pillow).
- `data/extra_images.json`: hand-picked Commons files that sit outside a car's categories.
- `data/heroes.json`: visual review. `hero` = lead photo per car, `drop` = rejected photos (by `t`).
- `src/template.html`, `src/app.js`: the page; `tools/build.py` merges everything into `index.html`.

Rebuild: `python3 tools/build.py` (no network needed). Check: `python3 tools/catalog.py`.

## Decisions

- Timeline: the orange frame marks the original form of each car; versions, editions and race
  variants are unframed. A concept and its production car count separately only if genuinely
  different (Urus).
- Specs: compiled without per-figure sources, spot-checked against Wikipedia in November 2026.
  Where Wikipedia states a build number plainly we use it; where it gives no official count the
  number is blank. `cv` is the launch output of that row's car.
- Photos: free licences only, credited on every photo. Non-commercial (NC) licences are accepted
  because the site is non-commercial; if it ever carries ads or sells anything, replace them.
  Never use scans of printed material, re-uploaded press photos, toys, LEGO, renders or game
  screenshots; their CC tags are not the uploader's to give. `flickr.py` skips accounts known for these.
  Every new photo is checked by eye (contact sheet) before it stays.
- Search engines are asked not to index the site (`noindex`), even though it is public.

## Gotchas

- Wikimedia throttles API calls from cloud servers: use Commons category pages, the raw file pages
  (`action=raw`) and `Special:Search` HTML instead of `api.php`.
- Commons thumbnails exist only at widths 330, 500, 960, 1280, 1920 and 3840 px, and only narrower
  than the original. The page loads them from `thumb.wikimedia.org`; `upload.wikimedia.org`
  returns 429 to this server for many thumbnails.
- Flickr's search page embeds its results as JSON after `modelExport:`; sizes go up to 1024 px.
  Openverse returns nothing useful for rare cars.
- lamborghini.com serves empty pages to scripts. Do not work around that (no browser user-agent
  spoofing); press photos would need the owner to register on media.lamborghini.com.

## Publishing

- Public link that needs no setup: https://raw.githack.com/wam090/the-lambo-index/main/index.html
- GitHub Pages (https://wam090.github.io/the-lambo-index/) needs one owner click: repo Settings →
  Pages → Deploy from a branch → `main` / root. Sessions cannot change that setting.

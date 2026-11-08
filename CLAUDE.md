# The Lambo Index: instructions for every session

This file and `BACKLOG.md` (imported at the bottom) load into every Claude Code session on this repo
automatically. Together they are the handover. Do not ask the user to re-explain the project or wait
for handover notes: what you need is here or in the code. If you had to work out something important
that is missing here, add it.

## The project
`index.html` is the whole product: one self-contained page listing every Lamborghini ever made or
shown (production, limited series, one-offs, concepts, prototypes, race cars) with specs and Wikimedia
Commons photos. Views: browse (search, filters, grid/list), car page with full-screen viewer, timeline,
compare (up to 4), stats. State lives in the URL hash: `#/m/<id>`, `#/?family=Countach&decade=1970s`,
`#/timeline`, `#/compare?ids=a,b`, `#/stats`. Vanilla JS: no framework, no npm packages, no server.
README.md is the user-facing description.

## Who decides
The user (the Coordinator) assigns the tasks and owns product decisions. Items marked "your call" in
BACKLOG.md are theirs: ask, never assume. Decisions already made are listed in BACKLOG.md: follow
them without asking again.

## Start of session
1. This file and the backlog are already in your context. Read code only for the area you touch.
2. Run `git log --oneline -8` and check for open pull requests. New sessions start from `main`, so
   unmerged work is invisible to you; if an open PR touches your area, tell the user before starting.

## Files
| Path | What it is | Edit? |
|---|---|---|
| `tools/catalog.py` | every car (`E(...)` rows: facts + Commons category names), debut rules | yes: source of truth |
| `data/heroes.json` | visual review: `hero` = lead photo per car id, `drop` = rejected photos | yes |
| `src/app.js` | the app, one IIFE | yes |
| `src/template.html` | page shell and all CSS; build fills `__LI_DATA__` and `__LI_APP__` | yes |
| `tools/images.py` | picks Commons photos per car, fetches author and licence | rarely |
| `tools/build.py` | catalogue + photos + src → `data/cars.json` + `index.html` | rarely |
| `tools/smoke.js` | headless check of every view | when the markup it checks changes |
| `data/images.json` | output of images.py | never by hand |
| `data/cars.json`, `index.html` | output of build.py | never by hand |

## Commands
```bash
python3 tools/catalog.py                # counts by type; asserts ids are unique
python3 tools/images.py --only id1,id2  # pick photos + credits for these cars (slow on purpose)
python3 tools/build.py                  # rebuild data/cars.json and index.html; prints counts
node tools/smoke.js                     # must print "smoke OK" before you commit
```
`images.py` without `--only` picks photos only for cars missing from `data/images.json`, then fetches
credits for any photo without a licence; `--credits-only` does only the second part.

## Recipes
- **Add or fix a car**: edit its row in `tools/catalog.py` → if it is new or its `cats` changed,
  `images.py --only <id>` → check the photos by eye (see Photos) → build → smoke.
- **Change the UI**: edit `src/` → build → smoke → screenshot what you changed at desktop and phone
  widths with Playwright (pre-installed in cloud sessions).
- **Timeline frames**: a debut is the first car of each family by year, plus `EXTRA_DEBUTS`, minus
  `NOT_DEBUTS` (both in `tools/catalog.py`; applied in `build.py`).

## Rules
- Never hand-edit `index.html`, `data/cars.json` or `data/images.json`. Commit them in the same
  commit as the source change that produced them: `index.html` is what the user opens.
- Merge conflict in `index.html` or `data/cars.json`: never resolve it by hand. Resolve the sources,
  rebuild, commit the output. Two branches that both rebuilt usually conflict there.
- `build.py` writes today's date into the data, so a rebuild on a new day changes both outputs even
  with no content change. That is expected.
- Car `id`s are permanent: they are shared URLs (`#/m/<id>`) and the keys of `images.json` and
  `heroes.json`. Rename one only if the user asks, and move its keys in both files.
- Row order in `CARS` matters: same-year ties for debut and for sorting go to the earlier row.
- `family` is an ASCII key (`Murcielago`, `Huracan`). A family whose display name differs needs it in
  both `FAMILY_NAME` (`src/app.js`, display) and `FAMILY_WORDS` (`tools/images.py`, photo matching).
- `kind` must be one of `KIND_ORDER` and `eng` one of `ENG_ORDER` (`src/app.js`; colours in
  `KIND_COLOUR`/`ENG_COLOUR`). `body` is free text that `bodyGroup()` maps to a filter group, and
  unmatched words fall into "Coupé". A new value needs code changes there.
- `end`: 0 = still built, None = one year only. `cv` and `units`: None when not reliably known.
  Blank beats wrong: if sources disagree, leave it blank.
- `src/app.js` must not contain `</script` (build asserts). No external JS: only photos and fonts
  come from the network.
- Keep `<meta name="robots" content="noindex, nofollow">` until the user decides to go public.
- The GitHub repo is public: no secrets and no personal data in commits.
- Anything outside this repo dies with the session's container. Commit it or lose it.

## Photos
- Only freely licensed Wikimedia Commons files, each credited with author, licence and link (the app
  shows these). Never commit image files: the page loads them from Wikimedia.
- Wikimedia rate-limits shared cloud IPs; HTTP 429 is common. `images.py` is single-threaded with
  0.6 s spacing and backs off on its own. Never parallelise it or re-run it over every car; use
  `--only`. If it gives up on a car, re-run that id later.
- Re-running `--only <id>` replaces that car's photo list, so re-check its `hero` and `drop` entries
  in `data/heroes.json` (keyed by car id; values are Commons file titles).
- Check chosen photos by eye before committing: wrong car or a detail shot → `drop`; a better lead
  photo → `hero`. Thumbnails can return 429 in cloud sessions too, so blank photo boxes in a
  screenshot may be the sandbox, not the site.

## Before you finish (this replaces the handover)
1. Rebuild if any source changed; `node tools/smoke.js` passes; look at the result.
2. `BACKLOG.md`: delete what you finished (git log is the history), add follow-ups you found, and
   record any decision the user made, with the date. Keep it short: it loads into every session.
3. This file: update it only if you changed how the project works. Keep it under about 150 lines;
   cut stale lines instead of appending.
4. `README.md` if user-visible features or counts changed.
5. Commit sources and outputs together, push your session branch, open a draft PR.
6. Tell the user plainly: what changed, how you verified it, what needs their decision, and that the
   PR must be merged before the next session starts, or that session will not see this work.

@BACKLOG.md

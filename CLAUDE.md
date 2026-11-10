# The Lambo Index: instructions for every session

This file, `BACKLOG.md` and `MESSAGES.txt` (both imported at the bottom) load into every Claude Code
session on this repo automatically. Together they are the handover; `MESSAGES.txt` is how the
Coordinator and the chats talk to each other. Do not ask the user to re-explain the project or wait
for handover notes: what you need is here or in the code. If you had to work out something important
that is missing here, add it.

## The project
`index.html` is the whole product: one self-contained page listing every Lamborghini ever made or
shown (production, limited series, one-offs, concepts, prototypes, race cars) with specs and photos from
Wikimedia Commons and Flickr. Views: browse (search, filters, grid/list), car page with full-screen viewer, timeline,
compare (up to 4), stats. State lives in the URL hash: `#/m/<id>`, `#/?family=Countach&decade=1970s`,
`#/timeline`, `#/fast10`, `#/compare?ids=a,b`, `#/stats`. Vanilla JS: no framework, no npm packages, no server.
README.md is the user-facing description.

## Who decides
The user (the Coordinator) assigns the tasks and owns product decisions. Items marked "your call" in
BACKLOG.md are theirs: ask, never assume. Decisions already made are listed in BACKLOG.md: follow
them without asking again. A chat the user calls the Coordinator's chat only advises and writes
messages in `MESSAGES.txt`; it changes nothing else in the repo. Every change on GitHub (code, data,
docs, PRs, merges) is made by a dev chat. Every chat reports to the Manager (user's instruction,
2026-11-10): when you finish a task or hit a blocker, send it a short status with `send_message`:
what changed, the PR, decisions needed. Roles pass to the newest chat: when one fills up, its
successor takes the next version (Dev_0.2 → Dev_0.3, Manager → Manager_v0.2), so "the Manager"
and "the dev" always mean the newest chat with that title. Find them by title with
`list_sessions`, never by a saved session ID.

## Every chat: instructions first, then the ask
Whatever the user writes, even one word, handle it in this order:
1. This file, the backlog and the messages (already in your context). Read code only for the area
   you touch. OPEN messages to "dev" are part of your work unless the user's ask says otherwise.
2. Run `git log --oneline -8` and check for open pull requests. New sessions start from `main`, so
   unmerged work is invisible to you; if an open PR touches your area, tell the user before starting.
3. Then the ask. "next" or "continue" means: OPEN messages to "dev" first, then BACKLOG.md
   ("In progress", then "Next"), skipping items marked "your call"; list those for the user instead.
4. End every reply with a capacity bar, e.g. `Chat capacity: ████████░░░░░░░░░░░░ ~40% used (estimate)`.
5. At about 70% used, or when the task is done, start nothing new: do "Before you finish" so the
   chat never runs out mid-task.

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
| `tools/flickr.py` | Creative Commons photos from Flickr for cars Commons lacks | rarely |
| `tools/review_sheet.py` | contact sheet of photo candidates, for checking by eye (Pillow) | rarely |
| `data/extra_images.json` | hand-picked Commons files outside a car's categories | yes |
| `data/images.json`, `data/flickr.json` | output of images.py and flickr.py | never by hand |
| `data/cars.json`, `index.html` | output of build.py | never by hand |

## Commands
```bash
python3 tools/catalog.py                # counts by type; asserts ids are unique
python3 tools/images.py --only id1,id2  # pick photos + credits for these cars (slow on purpose)
python3 tools/build.py                  # rebuild data/cars.json and index.html; prints counts
node tools/smoke.js                     # must print "smoke OK" before you commit
python3 tools/flickr.py --all-gaps      # Flickr photos for cars with < 4 Commons photos (or --only)
python3 tools/review_sheet.py data/flickr.json id1,id2 sheet.png   # candidates side by side
```
`images.py` without `--only` picks photos only for cars missing from `data/images.json`, then fetches
credits for any photo without a licence; `--credits-only` does only the second part.

## Recipes
- **Add or fix a car**: edit its row in `tools/catalog.py` → if it is new or its `cats` changed,
  `images.py --only <id>` → check the photos by eye (see Photos) → build → smoke.
- **Change the UI**: edit `src/` → build → smoke → screenshot what you changed at desktop and phone
  widths with Playwright (pre-installed in cloud sessions).
- **Timeline frames**: a debut is the first car of each family by year, plus `EXTRA_DEBUTS`, minus
  `NOT_DEBUTS` (both in `tools/catalog.py`; applied in `build.py`). Kind frames and badges come from `kind`
  in `buildTimeline()`: Limited series platinum, One-off platinum with diamond sparkles, Race car red with tyre marks. A car
  shows only its highest frame (diamond > platinum > red > orange) but keeps every badge. Styles in `src/template.html`; `smoke.js` counts each frame.
- **Fast 10**: `PERF` in `tools/catalog.py` holds claimed top speed, an "over" flag and 0–100 for road
  cars with official figures; `buildFast()` ranks by horsepower, then top speed (350+ above 350), and
  skips Roadster versions. Add a car's figures to `PERF` and it competes automatically.
- **Timeline legend** ("Filter by frame →"): chips filter the timeline and combine as AND: Debut goes
  with one kind (cars that are both), the kinds exclude each other (`#/timeline?only=debut,race`, `applyTlOnly()`);
  Debut means every car with the Debut badge, the others the car's kind.
- **Monthly refresh**: the scheduled task "Lambo Index monthly refresh" (1st of each month, fresh
  session) follows `tools/REFRESH.md`. Change the job there, through a PR.
- **Hero preview**: `#/?hero=1` shows the car-of-the-day hero in place of the family strip (`setHero()`;
  it stays on for the visit, `hero=0` turns it off). The default stays as it is until the user approves.
- **Brands**: the data carries `brand` (`BRAND` in `build.py`). If a second brand ever comes, build one
  page per brand with the same tools and move Lambo under `/lamborghini/`; nothing more until then.

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
- Power: `cv` is stored in CV, as Lamborghini quotes it; the site shows hp (`hp()` in `app.js`,
  cv × 0.98632, rounded) and kW. The power filter's steps are in hp.
- `end`: 0 = still built, None = one year only. `cv` and `units`: None when not reliably known.
  Blank beats wrong: if sources disagree, leave it blank.
- `src/app.js` must not contain `</script` (build asserts). No external JS: only photos and fonts
  come from the network.
- Keep `<meta name="robots" content="noindex, nofollow">` until a cyber-security expert has reviewed
  the site (user's decision, 2026-11-10).
- The GitHub repo is public: no secrets and no personal data in commits.
- Anything outside this repo dies with the session's container. Commit it or lose it.

## Photos
- Every photo is credited with author, licence and a link to where it is hosted (the app shows
  these). Never commit image files: the page loads them from Wikimedia and Flickr. Sources, in order:
  Commons categories (`images.py`); Commons files outside a car's categories, found with
  `Special:Search` (`data/extra_images.json`); Flickr Creative Commons photos (`flickr.py`); and only
  for a car with no free photo, credited press or all-rights-reserved photos in
  `data/nonfree_images.json` (user's decision, 2026-11-08; find candidates with `flickr.py --embed`).
  Deleting that file removes them all.
- Non-commercial (NC) licences are accepted because the site is non-commercial. If it ever carries
  ads or sells anything, replace those photos.
- Never label a photo freely licensed when it isn't: scans of printed material and re-uploaded press
  photos carry CC tags that are not the uploader's to give, so they may only go in
  `nonfree_images.json`, credited to their real maker (press photos to the manufacturer). Never use
  toys, LEGO, renders or game screenshots as photos of a car, paid stock or watermarked photos, or
  anything that needs a site's protections worked around. `BLOCKED` in `flickr.py` skips known
  accounts. Every new photo is checked by eye before it stays.
- Wikimedia rate-limits shared cloud IPs; HTTP 429 is common. `images.py` is single-threaded with
  0.6 s spacing and backs off on its own. Never parallelise it or re-run it over every car; use
  `--only`. If it gives up on a car, re-run that id later.
- Re-running `--only <id>` replaces that car's photo list, so re-check its `hero` and `drop` entries
  in `data/heroes.json` (keyed by car id; values are Commons file titles, or `flickr:<id>`).
- Check chosen photos by eye before committing: wrong car or a detail shot → `drop`; a better lead
  photo → `hero`. Thumbnails can return 429 in cloud sessions too, so blank photo boxes in a
  screenshot may be the sandbox, not the site.
- Commons thumbnails exist only at widths 330, 500, 960, 1280, 1920 and 3840 px, narrower than the
  original. The page loads them from `thumb.wikimedia.org`; `upload.wikimedia.org` often returns 429
  here. Use category pages, raw file pages (`action=raw`) and `Special:Search` HTML, not `api.php`.
- Flickr's search page embeds its results as JSON after `modelExport:`; sizes go up to 1024 px.
  Openverse finds nothing for rare cars.
- lamborghini.com serves empty pages to scripts: do not work around it (no user-agent spoofing).
  Press photos would need the user to register on media.lamborghini.com, and are the user's call.

## Publishing
- Live site, always the newest build: https://wam090.github.io/the-lambo-index/ (GitHub Pages from `main` / root, turned on by
  the user on 2026-11-09; updates a minute or so after each merge).
- Fallback only: https://htmlpreview.github.io/?https://github.com/wam090/the-lambo-index/blob/main/index.html
  (renders main's `index.html` straight from GitHub; updates within about 5 minutes of a merge). It injects
  a `<base>` tag and rewrites static links into full URLs, so the app treats any link containing `#/`
  as in-app and resolves `replaceState` URLs against the page itself; keep it that way. One harmless console error: htmlpreview runs the JSON data block as a script. Do not hand out
  githack links: in browsers they show an "External Content Notice" click-through page and ads.

## Before you finish (this replaces the handover)
1. Rebuild if any source changed; `node tools/smoke.js` passes; look at the result.
2. `BACKLOG.md`: delete what you finished (git log is the history), add follow-ups you found, and
   record any decision the user made, with the date. Keep it short: it loads into every session.
3. This file: update it only if you changed how the project works. Keep it under about 150 lines;
   cut stale lines instead of appending.
4. `README.md` if user-visible features or counts changed. `MESSAGES.txt`: mark what you handled
   DONE, delete older DONE messages, and leave a message if the Coordinator or the next chat must
   know something the backlog does not say.
5. Commit sources and outputs together, push your session branch, open a PR and merge it yourself
   (user's decision, see BACKLOG.md); the next chat starts from `main`.
6. Tell the user plainly what changed and how you verified it, then end with **Next steps for you**:
   - the PR you merged, or why you could not;
   - the exact sentence to paste into the next chat;
   - any decision waiting on the user.
   If the task is unfinished, leave the site working and put what is left under "In progress" in
   BACKLOG.md, in the same PR, so the next chat only needs "continue".

@BACKLOG.md

@MESSAGES.txt

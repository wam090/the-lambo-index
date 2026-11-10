# Monthly refresh

A scheduled task ("Lambo Index monthly refresh") runs this job once a month in a fresh session. Its
prompt only points here, so the job is changed here, through a PR. Do this job only: OPEN messages
and backlog items are for other chats. Every rule in CLAUDE.md applies, above all Rules and Photos.

MERGE MODE: auto
(The one switch. `auto`: merge your PR yourself once smoke passes. `wait`: leave it open for the
user, step 8.)

1. **Branch.** Start your session branch from the latest `main`.
2. **Window.** From the last refresh (`git log -1 -E --grep='^Monthly refresh [0-9]{4}-[0-9]{2}:'
   --format=%cs`, which matches only step 8's commit titles; 60 days back if there is none) to
   today. Overlap is fine: skip cars already in `tools/catalog.py`.
3. **New cars.** Lamborghinis first shown or announced in the window: new models and versions,
   limited series, one-offs, concepts, race cars. Sources: Wikipedia and the motoring press
   (Autocar, Car and Driver, Motor1, Top Gear, evo, Carscoops). Never lamborghini.com, and no
   user-agent tricks. Rumours and teasers wait until the car is shown.
4. **Rows.** Add each car to `CARS` (CLAUDE.md, Recipes: "Add or fix a car"), and its official top
   speed and 0–100 to `PERF` if it is a road car. A figure two sources do not agree on stays `None`:
   blank beats wrong. Existing rows: only fill blanks, unless the PR cites a source for the change.
5. **Photos.** `python3 tools/images.py --only <new ids>`, then `python3 tools/flickr.py --all-gaps`,
   which prints each car's `new:` and `gone:` photos (a failed search keeps the old list). Look at
   every new photo (`tools/review_sheet.py`, sheet saved outside the repo) and `drop` wrong cars,
   toys, renders and detail shots in `data/heroes.json`. A new car with no photo that passed this
   check is not added: remove its row and list it in the PR for next month. If `images.py` gives up
   on a car (HTTP 429), retry it once a few minutes later.
6. **Build.** `python3 tools/catalog.py`, `python3 tools/build.py`, `node tools/smoke.js`. Update the
   car count in README.md if it changed.
7. **Nothing new.** No car added and no `new:` or `gone:` line from `flickr.py`: run
   `git checkout -- .` and stop (the rebuild only changed the date). No commit, no PR.
8. **PR.** Commit as `Monthly refresh YYYY-MM: <what was added>`. The PR lists each car with its
   sources, and the photos added, dropped or gone. If smoke passed and MERGE MODE is `auto`, merge it.
   Otherwise (`wait`, smoke failed, or anything you are unsure of), leave it open and say why on
   `main`: a `dev -> Coordinator: OPEN` message in `MESSAGES.txt`, on its own branch from `main`,
   merged as its own PR.
9. **Report.** End your reply with what was added (or "nothing new") and the PR link; the push
   notification shows it. Send the same to the Manager chat (CLAUDE.md, Who decides).

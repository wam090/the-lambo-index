# Backlog

Loaded into every session through CLAUDE.md, so keep it short: delete finished items (git log is the
history). Record each decision the user makes under Decisions, with its date.

## Decisions (settled: change only if the user asks)

- 2026-11-13: An audit may replace one of our values when two sources agree against it, but every
  audit change (fact, photo drop or move) goes to the user first: the Dev reports each night's
  proposals to the Manager (car, field, ours, theirs, the two source hosts), leaves the PR open
  and applies only what the Manager relays as "approved". No answer: nothing is applied.
- 2026-11-13: The user switches on GitHub's "Block command line pushes that expose my email"
  themselves. Our commits use noreply addresses only, so pushes are unaffected.
- 2026-11-08: Scope is indexing and easy browsing first, built up step by step.
- 2026-11-08: The timeline's orange frame marks only the original form of each car; versions,
  editions and race variants never get it (rules in tools/catalog.py).
- 2026-11-08: Every car should have photos, taken from anywhere on the internet. Free licences
  first; otherwise credited press or all-rights-reserved photos, loaded from where they are hosted
  (`data/nonfree_images.json`; rules in CLAUDE.md, Photos).
- 2026-11-08: Timeline frames by kind: limited series platinum, one-offs platinum with diamond sparkles (no colours),
  race cars red with tyre marks, each with its own badge beside the Debut badge. One frame per car,
  the highest it qualifies for (diamond > platinum > red > orange debut); every badge stays.
- 2026-11-08: Keep pages lean: the user prefers visuals to explanatory text. The timeline has no
  intro, only a one-line legend of mini frames (Debut › Race car › Limited › One-off).
- 2026-11-09: Fast 10 tab beside Timeline: ranked by horsepower, then claimed top speed;
  roadsters count with their coupé. The site shows power in hp, not CV.
- 2026-11-09: Timeline legend reads "Filter by frame →"; Clear shows all. 2026-11-10: chips combine as
  AND (a car shows only when it has every chosen badge): Debut plus one kind; kinds exclude each other.
- 2026-11-10: The home page has no intro heading; browsing starts right under the header.
- 2026-11-11: The Stats page is removed; the views are Browse, Compare, Fast 10 and Timeline. Old
  `#/stats` links land on Browse.
- 2026-11-10: The car-of-the-day hero banner replaces the family strip, with no visible heading;
  live since 2026-11-11, its credit linking the photo's page and licence.
- 2026-11-12: The Scout runs weekly (Mondays 03:17 UTC, 10-day window), not monthly: it looks for
  new cars and fills blank specs of up to 7 cars per run (two agreeing sources, round-robin). A
  Pickup chat on Haiku 5.5 replaces the Manager's monthly pickup.
  One PR per run, the same day; Cyber checks every PR.
- 2026-11-12: Visits are counted with GoatCounter (site code `thelamboindex`), without its script:
  app.js loads a tracking pixel per page shown (view or car page, never filters or searches; old
  `#/stats` counts as Browse), only on https. The footer says visits are counted anonymously, with
  no cookies. The user reads the counts in GoatCounter's dashboard and its weekly email.
- 2026-11-12: Monthly design review on the 5th (06:17 UTC) by the Web designer: at most 5 UI
  proposals to the Manager; nothing is built until the user approves.
- 2026-11-12: The Pickup reads only the Scout task's run metadata and points the Dev at every
  finished run (its tool limit is not enforced, so it reads nothing untrusted).
- 2026-11-12: The site goes live: the `noindex` tag is removed (it stood since 2026-11-10, pending a
  security review; Cyber_v0.2 checks the go-live PR). smoke fails if a robots `noindex` returns.
- 2026-11-12: A photo of a different version that has its own page moves to that page (the two
  2024 GT3 EVO2 photos: Huracán GT3 → GT3 EVO). Otherwise photos are dropped only when they show a
  different car, not a different version of the same car; when unsure, ask the Manager.
- 2026-11-12: Nightly family audit, 16 nights from 2026-11-13 (`tools/AUDIT.md`): a Scout-style task at
  00:17 UTC (no standing Auditor chat) checks one night's facts against two sources; the Pickup's
  second task points the Dev at it at 05:17 UTC; the Dev applies findings and checks the night's
  photos; one PR a night, Cyber checks. A prompt change means a new task.
- 2026-11-12: Footer redesign: concise, grouped, quiet, at the content width. Line 1 the build's data
  line; line 2 three notes with quiet separators (stacked on narrow screens): "Unofficial fan site, not
  affiliated with Automobili Lamborghini" (fan notice of 2026-11-11, shortened; the trademark sentence
  dropped), "Photos credited to their authors, under their licences", "Visits counted anonymously, no
  cookies". smoke checks the exact text on six views.
- 2026-11-11: Non-free photos: no re-posted press photos; private photographers' photos only where
  the Flickr owner allows sharing. "Report a photo" opens a GitHub issue; no email anywhere.
- 2026-11-11: No "See photos at the source" link: a car with no photo keeps today's empty state.
- 2026-11-11: urus-st-x, sc20, invencible and autentica keep the empty state for now: no registration
  on Lamborghini's media site and no press-office request (photo hunt found only press photos).
- 2026-11-11: Every chat hands over at about 50% of measured capacity (was 90%, before that 70%):
  it finishes its current task, reports it, and the Manager starts its successor.
- 2026-11-11: Token plan: Dev Opus 5.5 (Extreme + UltraCode while coding, High otherwise), Cyber
  Opus 5.5 High, Manager Sonnet 5.5 Medium, Web designer Sonnet 5.5 High, Scout task Sonnet 5.5.
  Message the Manager only when done or blocked; one message per hand-off; no progress notes.
- 2026-11-11: Dev_0.1, Dev_0.2, the Coordinator, the first Manager chat, the old Scout chat and the
  first Cyber chat are archived (still readable); the placeholder refresh task is deleted.
- 2026-11-11: The Manager reports to the user only as bullets under Done / Next / Needs approval,
  no prose.
- 2026-11-11: At about 50% measured the Manager starts its own successor (create_session, title
  Manager_v0.N+1, hand-over prompt) and tells the user in one line; likewise for any role that
  reports it is full.
- 2026-11-10: The Coordinator chat is retired; the user talks only to the Manager.
- 2026-11-10: The monthly refresh sends no push notifications; it reports to the Manager.
- 2026-11-11: Refresh becomes the Scout. It only scouts (new cars, facts and sources, Commons
  categories, photo candidates checked by eye) and leaves a package; it never commits, pushes,
  opens PRs or merges. The Dev builds the PR, Cyber checks it, the Dev merges after Cyber's OK.
  This replaces MERGE MODE and the 2026-11-10 merge rules. Format and checks: Cyber's spec,
  implemented in `tools/scout_import.py` and `tools/REFRESH.md`.
- 2026-11-09: Working model: every change on GitHub (code, data, docs, PRs, merges) is done by a dev
  chat (Dev or Web designer); the other chats advise and write messages.
- 2026-11-10: One line of communication: the user talks to the Manager. 2026-11-11: all chats may
  message each other directly; every chat reports to the Manager; the Manager is the boss. Chats
  answer the user in 1–2 lines. Roles pass to the newest chat (Dev_0.2 → Dev_0.3, Manager → Manager_v0.2).
- 2026-11-09: Lambo first. Room for other brands only where it costs nothing (`brand` in the data);
  the user disliked existing multi-brand sites, so no umbrella site unless a second brand is real.
- 2026-11-08: Claude merges its own PRs and handles git end to end; involve the user only when
  really needed.
- 2026-11-08: Keep everything relevant in this GitHub repo and avoid steps that need the user's
  hands. The site should have a working public link.

## In progress

- [ ] **Scout cut-over.** The Manager sets the Scout cron to `17 3 * * 1`, creates the Pickup chat
      and task, deletes the monthly pickup task (REFRESH.md Setup), and Cyber verifies them. v1
      packages stop on 2026-11-30.

## Next

- [ ] **Nightly audit**: 16 nights from 2026-11-13 (`tools/audit_plan.json`). When the last is merged,
      write "audit done" here and the Manager disables both tasks.

- [ ] **gap_ids from the run's catalogue** (Cyber, non-blocking): `scout_import.py` computes a run's
      gap ids from the working `catalog.py`; if main changed after the run, a valid fill can be
      rejected (fails closed). Compute them from `git rev-list -1 --before=<fire time> origin/main`.

- [ ] **Owned / Wanted tracking** with notes, saved per browser, with export/import.
      Revisit if the site goes public (then it would need accounts or a shared store).
- [ ] **Spec doubts.** Build numbers left blank because sources disagree: Countach LP400 (152–157),
      LP500 S (321–323), Urraco P200 (66–77), Murciélago SV (186 claimed, 268 found by a registry),
      Miura SVJ (about six), Diablo SV-R (31–34). Countach 25th Anniversary: 657 or 658. Gallardo
      LP560-4 restyle: Walter de Silva (Wikipedia) or Filippo Perini; we keep the original designer.

## Ideas

- Specs depth: top speed, 0–100 km/h, weight, price when new.
- Chassis-level detail for one-offs and race cars (chassis numbers, race results).
- Link each car to its scale models in the diecast index built in an earlier session. That index is
  lost: it is not in this repo, its old path no longer exists, and the zip the user uploaded on
  2026-11-08 was an older copy of this repo. Rebuild it here if wanted. Car pages already link to
  lambodiecast.com.
- Light theme toggle.

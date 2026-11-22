# Backlog

Loaded into every session through CLAUDE.md, so keep it short: delete finished items (git log is the
history). Record each decision the user makes under Decisions, with its date.

## Decisions (settled: change only if the user asks)

**Team and process**
- 2026-11-08/09: Claude handles git end to end and merges its own PRs; every change on GitHub is made
  by a dev chat (Dev or Web designer), the others advise and write messages. Keep everything relevant
  in this repo, avoid steps that need the user's hands; the site has a working public link.
- 2026-11-10/11: The user talks only to the Manager (the Coordinator chat is retired). All chats may
  message each other; every chat reports to the Manager, the Manager is the boss. Chats answer the
  user in 1–2 lines; roles pass to the newest chat. The Manager reports to the user only as bullets
  under Done / Next / Needs approval, no prose.
- 2026-11-11: Every chat hands over at about 50% of measured capacity: it finishes its current task
  and reports it; the Manager starts its successor (its own too: Manager_v0.N+1, one line to the user).
- 2026-11-11/19/22 token plan: Dev Opus 5.5 (Extreme + UltraCode while coding, High otherwise); Cyber
  Opus 5.5 High; Manager Opus 5.5, successors the same at effort max (user, 2026-11-22: do not propose
  lowering it); Web designer and Photo Sonnet 5.5 High; Scout task Sonnet 5.5.
  Message the Manager only when done or blocked; one message per hand-off; no progress notes.
- 2026-11-15: Working hours 21:00-03:00 UTC (00:00-06:00 Riyadh) for every chat and task.
- 2026-11-19: The Manager runs team structure and orders; only approvals go back to the user.
- 2026-11-22 (user): every Manager report is complete on its own: done since the user's last message,
  every open approval lettered (with a pick) until answered, next, and a receipt per decision. Old
  chats are archived as soon as they are done (the Manager archives; the user deletes if wanted).
- 2026-11-22 D (user): the Manager keeps `ops/manager-log.md` (only that file; PR, Cyber checks, the
  Manager merges; a new Manager reads it from `origin/main`). E (user): a nightly check at 05:30
  Riyadh (02:30 UTC) and a weekly close on Thursdays with at most 3 outcomes for the next week.
- 2026-11-13: Claude's commits use noreply addresses. The user switches on "Keep my email addresses
  private" and "Block command line pushes that expose my email"; the 26 web-UI commits of 2026-11-09/10
  with the user's email stay as they are (no history rewrite).

**Refresh and audit**
- 2026-11-11/12/15: The Scout only scouts (new cars, blank specs of up to 7 cars a run, two agreeing
  sources, round-robin) and leaves a package; it never commits, pushes, opens PRs or merges. Weekly,
  Mondays 00:47 UTC. The Dev builds one PR per run the same day, Cyber checks, the Dev merges. Format
  and checks: Cyber's spec in `tools/scout_import.py` and `tools/REFRESH.md`. No push notifications.
  The Pickup chat is retired (2026-11-15): a pointer task fires into the Dev chat; a prompt change
  means a new task.
- 2026-11-12 → 2026-11-21: The nightly family audit is stopped after night 9 (user, "Yes to all"):
  tasks disabled, nights 6, 8 and 10-16 not run; `tools/AUDIT.md` and `audit_plan.json` stay as history.
  3500-gtz designer stays "Zagato": re-add Spada only if two real pages about the GTZ name him and
  one checks out in the raw article.

**Product and UI**
- 2026-11-08: Scope is indexing and easy browsing first, built up step by step. Keep pages lean:
  visuals over explanatory text.
- 2026-11-08: Timeline frames by kind: limited series platinum, one-offs platinum with diamond sparkles
  (no colours), race cars red with tyre marks, each with its own badge beside the Debut badge; one frame
  per car, the highest (diamond > platinum > red > orange debut), every badge stays. The orange frame
  marks only the original form of each car (rules in `tools/catalog.py`). No intro, only a one-line
  legend "Filter by frame →" (Debut › Race car › Limited › One-off; Clear shows all); 2026-11-10: chips
  combine as AND, Debut plus one kind, kinds exclude each other.
- 2026-11-09: Fast 10 tab beside Timeline: ranked by horsepower, then claimed top speed; roadsters
  count with their coupé. The site shows power in hp, not CV.
- 2026-11-09: Lambo first; room for other brands only where it costs nothing (`brand` in the data); no
  umbrella site unless a second brand is real.
- 2026-11-10/11: No intro heading on the home page. The car-of-the-day hero (no visible heading)
  replaces the family strip, its credit linking the photo's page and licence. The Stats page is
  removed (views: Browse, Compare, Fast 10, Timeline; old `#/stats` links land on Browse).
- 2026-11-12: Footer: concise, grouped, quiet, at the content width. Line 1 the build's data line;
  line 2 three notes with quiet separators (stacked on narrow screens): "Unofficial fan site, not
  affiliated with Automobili Lamborghini", "Photos credited to their authors, under their licences",
  "Visits counted anonymously, no cookies". smoke checks the exact text on six views.
- 2026-11-12: Visits via GoatCounter (site code `thelamboindex`) without its script: a tracking pixel
  per view or car page shown (never filters or searches; old `#/stats` counts as Browse), https only.
  The user reads the counts in GoatCounter's dashboard and weekly email.
- 2026-11-12: The site is live and indexable; smoke fails if a robots `noindex` returns.
- 2026-11-12: Monthly design review on the 5th (01:17 Riyadh, 22:17 UTC on the 4th) by the Web
  designer: at most 5 UI proposals to the Manager; nothing is built until the user approves.
- 2026-11-15: A static page per car for search engines. No ads. 2026-11-22 C (user): they start now,
  no longer after the photo gaps. Built 2026-11-22 to Cyber's design review: no robots.txt (crawlers
  read it only at the host root), no JavaScript on the pages, `og:image` only PD, CC0, CC BY, CC BY-SA
  (no NC until the user decides: Manager, on Cyber's recommendation).

**Photos**
- 2026-11-08/15/19: Every car should have photos; a limited series or one-off must never have none.
  One photo beats none: no empty state if any legally usable exterior exists; empty-state cars come
  first in every photo hunt. A car with only press photos, recreations, toys or renders keeps the
  empty state, and the Manager asks the user per car. No "See photos at the source" link; no
  registration on Lamborghini's media site and no press-office request (2026-11-11).
- 2026-11-18: "no then I dont want headache": no press or promotional photos and, apart from
  photographers' own Flickr photos, no all-rights-reserved photos. "Report a photo" opens a GitHub
  issue; no email anywhere (2026-11-11).
- 2026-11-16/17/19: Private photographers' own Flickr photos (owner allows sharing, `flickr.py
  --embed`) for a car under 4 photos, until it has 4; evidence and Cyber's check in CLAUDE.md Photos.
  Their own small name watermark is allowed when it matches the credited account; stock, agency,
  press and promotional marks stay banned. Credit only the person who took a photo.
- 2026-11-22 A (user, "stay safe as much as possible"): an owner's written no-use or ask-first notice
  (profile or caption) rejects a photo whatever the Flickr share setting; Kevin Stec's (kyter) 2
  photos left 350-gts; kyter, darylchapman and raphael_belly_photography are in `BLOCKED`.
- 2026-11-22 B (user): countach-lp500 keeps its 2 photos of the 2021 factory recreation as the car's
  own ("the car came to existence"); Photo's 2 new own-Flickr photos of it are not added.
- 2026-11-18: Exterior photos only on car pages (interiors, engines, details maybe later in a
  deep-dive section); the lead photo is an exterior.
- 2026-11-15/16: Only real cars: no toys, die-cast or scale models, LEGO or other models in any
  photo; no separate full sweep (the quality pass looks at every photo).
- 2026-11-12: A photo of a different version that has its own page moves to that page; otherwise drop
  only a different car, never a different version of the same car.
- 2026-11-19/21: Who drops: the Dev alone drops a photo that is (a) not an exterior of the car, (b) not
  about the car (crowd, car park, group photo, hall overview) or (c) a toy, render or another car, and
  lists each in its report. A version in doubt, a drop that would leave a car under 4 photos and any
  move between pages go to the Manager, who decides photo drops and moves (user, 2026-11-21). Fact
  changes stay with the user.
- 2026-11-19: Quality-pass bar: sharp, whole car, >= 1280 px, no crowd. Waived only for a car with no
  other usable photo anywhere: a lower-quality exterior stays as a placeholder until a better one is
  found. No UI work for thumbnails or the empty-state card.
- 2026-11-20/21 (the Manager): drop a two-car frame only when our car is not a clear whole subject. A
  poor photo whose drop would leave a car under 4 photos stays until Photo's replacement is applied,
  unless it is not the car, a toy or not an exterior: huracan-gt3 keeps "GT3 and GT4 race one ...
  (51373314403).jpg" and "2018 Rolex 24 (41267772511).jpg" until then; urus-concept keeps
  Urusside.jpg (640 px) until then (2026-11-22). A new photo below 1280 px needs the Manager's OK
  before it is applied (2026-11-22).

## In progress

(none)

## Next

- [ ] **Photo gaps** (24 of 150 cars under 4 photos on 2026-11-22, 8 with none): Photo (Photo_v0.x) sends
      verified picks; the Dev checks each at full size and applies it. The 6 empty-state cars (urus-st-x,
      sc20, invencible, autentica, miura-jota, countach-evoluzione) have nothing legal (press, game, LEGO,
      a Jota-spec conversion, magazine scans): Photo retries on 2026-12-03, and the Manager asks the user
      about press photos. Rejected accounts: Marzal (45701009@N00, re-posting), Lokale Blicke
      (157290793@N07, local news; fenomeno-roadster empty since 2026-11-21), darylchapman,
      raphael_belly_photography, kyter (written no-use notices), Perico001 (mark not tied to the
      account). Nothing legal yet: temerario-spyder (only press re-posts), urus-se-performante, bravo
      (2026-11-22); lm001, lma002, huracan-stj, fenomeno-roadster (2026-11-21). urus-concept needs a
      1280 px or larger photo to replace Urusside.jpg. Rejected: Automotive Rhythms (artvlive, media
      outlet). Photo's next: aventador-50, gallardo-squadra-corse, 350-gts, p147-gandini, raptor.
- [ ] **Static car pages** (live 2026-11-22; IndexNow sent, HTTP 202). Waiting on the user: Google
      Search Console (URL prefix, HTML tag; steps in STATIC_PAGES.md): the Dev adds the tag, the user
      clicks Verify and submits `sitemap.xml`.
      Open for the user (through the Manager): NC licences in `og:image` (excluded until then;
      19 cars have no preview image). Parked (Manager, 2026-11-22): app cards linking to `m/<id>/`,
      a footer link to `m/`, JSON-LD.
- [ ] **Scout import follow-ups** (Cyber, non-blocking): (1) when a fill pairs Wikipedia with an
      `EXTRA_HOSTS` page, grep the raw article for that host; if it is the citation for the value, the
      two sources are one: leave it blank (add to REFRESH.md Dev steps); the format comment in
      `scout_import.py` should say v2 `opened`/`unreachable` may list `EXTRA_HOSTS`. (2) A Wikipedia
      404 in `opened` satisfies the "en.wikipedia.org page read" rule; tighten only if it matters.
      (3) Gap ids come from the working `catalog.py`, so a valid fill can be rejected if main changed
      after the run: compute them from `git rev-list -1 --before=<fire time> origin/main`.
- [ ] **Owned / Wanted tracking** with notes, saved per browser, with export/import (accounts or a
      shared store would be needed for anything more).
- [ ] **Spec doubts.** Build numbers left blank because sources disagree: Countach LP400 (152–157),
      LP500 S (321–323), Urraco P200 (66–77), Murciélago SV (186 claimed, 268 found by a registry),
      Miura SVJ (about six), Diablo SV-R (31–34). Countach 25th Anniversary: 657 or 658. Gallardo
      LP560-4 restyle: Walter de Silva (Wikipedia) or Filippo Perini; we keep the original designer.

## Ideas

- Specs depth: top speed, 0–100 km/h, weight, price when new.
- Chassis-level detail for one-offs and race cars (chassis numbers, race results).
- Link each car to its scale models (the diecast index of an earlier session is lost; rebuild it
  here if wanted). Car pages already link to lambodiecast.com.
- Light theme toggle.

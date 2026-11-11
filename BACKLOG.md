# Backlog

Loaded into every session through CLAUDE.md, so keep it short: delete finished items (git log is the
history). Record each decision the user makes under Decisions, with its date.

## Decisions (settled: change only if the user asks)

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
- 2026-11-10: The car-of-the-day hero banner replaces the family strip, with no visible heading;
  live since 2026-11-11, its credit linking the photo's page and licence.
- 2026-11-10: `noindex` stays until a cyber-security expert has reviewed the site.
- 2026-11-11: Non-free photos: no re-posted press photos; private photographers' photos only where
  the Flickr owner allows sharing. "Report a photo" opens a GitHub issue; no email anywhere.
- 2026-11-10: Every chat works to about 90% of its capacity (was 70%), then hands over.
- 2026-11-10: The Coordinator chat is retired; the user talks only to the Manager.
- 2026-11-10: The monthly refresh sends no push notifications; it reports to the Manager. It runs in
  a standing chat titled "Refresh" (option B), woken by the scheduled task, and merges only PRs
  confined to the catalogue, photo data and build outputs.
- 2026-11-10: The monthly refresh's merge mode is parked: it stays `auto` for now.
- 2026-11-09: Working model: every change on GitHub (code, data, docs, PRs, merges) is done by a dev
  chat (Dev or Web designer); the other chats advise and write messages.
- 2026-11-10: One line of communication: the user talks to the Manager, the Manager to every other
  chat (Dev, Web designer, Cyber, scheduled runs). Chats report to the Manager and answer the user
  in 1–2 lines. Roles pass to the newest chat (Dev_0.2 → Dev_0.3, Manager → Manager_v0.2).
- 2026-11-09: Lambo first. Room for other brands only where it costs nothing (`brand` in the data);
  the user disliked existing multi-brand sites, so no umbrella site unless a second brand is real.
- 2026-11-08: Claude merges its own PRs and handles git end to end; involve the user only when
  really needed.
- 2026-11-08: Keep everything relevant in this GitHub repo and avoid steps that need the user's
  hands. The site should have a working public link.

## In progress

Nothing. (A chat that runs low on room mid-task writes here what is left.)

## Next

- [ ] **Monthly refresh task (the user, 10 seconds).** In the Refresh chat, type: "Create the monthly
      refresh task as tools/REFRESH.md says, then fire it once as the setup test." A Dev then deletes
      the placeholder task trig_017aDGyKxgfrxhwj1AYE5ofT (it would start a session without the repo).
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

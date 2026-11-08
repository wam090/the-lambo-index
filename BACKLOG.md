# Backlog

Loaded into every session through CLAUDE.md, so keep it short: delete finished items (git log is the
history). Record each decision the user makes under Decisions, with its date.

## Decisions (settled: change only if the user asks)

- 2026-11-08: Scope is indexing and easy browsing first, built up step by step.
- 2026-11-08: The timeline's orange frame marks only the original form of each car; versions,
  editions and race variants stay unframed (rules in tools/catalog.py).
- 2026-11-08: Photos are not limited to Wikimedia Commons; other freely licensed sources are fine
  (rules in CLAUDE.md, Photos).
- 2026-11-08: Keep everything relevant in this GitHub repo and avoid steps that need the user's
  hands. The site should have a working public link.

## In progress

Nothing. (A chat that runs low on room mid-task writes here what is left.)

## Next

- [ ] **GitHub Pages (your call: one click).** Settings → Pages → Deploy from a branch → `main` /
      root; then https://wam090.github.io/the-lambo-index/ works. Until then the public link is
      https://raw.githack.com/wam090/the-lambo-index/main/index.html. Removing `noindex` so search
      engines list the site is a separate call.
- [ ] **Owned / Wanted tracking** with notes, saved per browser, with export/import.
      Revisit if the site goes public (then it would need accounts or a shared store).
- [ ] **Auto-refresh**: a monthly scheduled task that adds new Lamborghinis, runs `images.py --only`
      for them and `flickr.py --all-gaps`, checks new photos by eye, rebuilds, runs the smoke check
      and opens a PR. Expect Wikimedia rate limits (HTTP 429). First job, cars missing from the
      index (verify each before adding): Huracán STJ (2024, 10 cars), Fenomeno Roadster (2026,
      15 cars), Revuelto SV (2026), Urus SE Performante (2026).
- [ ] **Last 4 photo gaps (your call).** SC20, Invencible, Auténtica, Urus ST-X: every photo found
      is copyrighted. Options: ask Flickr photographers to licence one photo each, or use
      Lamborghini press photos (you register on media.lamborghini.com; editorial-use terms).
      The Portofino has only an interior photo.
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

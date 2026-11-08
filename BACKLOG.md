# Backlog

Loaded into every session through CLAUDE.md, so keep it short: delete finished items (git log is the
history). Record each decision the user makes under Decisions, with its date.

## Decisions (settled: change only if the user asks)

- 2026-11-08: Scope is indexing and easy browsing first, built up step by step.
- 2026-11-08: The timeline's orange frame marks only the original form of each car; versions,
  editions and race variants stay unframed (rules in tools/catalog.py).

## Next

- [ ] **Go public (your call).** Wikimedia photos are freely licensed and credited, and the facts are
      our own, so a public site is legally clean. Before launch: remove the `noindex` meta tag,
      add a page title/description for sharing, and pick a host (GitHub Pages works as-is).
      Note that the GitHub repository itself is already public.
- [ ] **Owned / Wanted tracking** with notes, saved per browser, with export/import.
      Revisit if the site goes public (then it would need accounts or a shared store).
- [ ] **Auto-refresh**: a monthly scheduled task that checks for new Lamborghinis and new Commons
      photos, then rebuilds. Unblocked now that the project is on GitHub (wam090/the-lambo-index);
      expect Wikimedia rate limits (HTTP 429) from cloud sessions.
- [ ] **Fill photo gaps.** 18 cars have no freely licensed photo on Commons yet (for example
      SC20, Invencible, Auténtica, Countach QVX, Diablo SE30). Options: wait for uploads, or add
      press photos only if the licence allows it.

## Ideas

- Specs depth: top speed, 0–100 km/h, weight, price when new.
- Chassis-level detail for one-offs and race cars (chassis numbers, race results).
- Link each car to its scale models in the diecast index built in an earlier session. That index is
  not in this repo and its old path (`/home/user/lambo-scale-index`) no longer exists: ask the user
  for a copy before planning this. Car pages already link to lambodiecast.com.
- Light theme toggle.

# Backlog

Agreed scope so far: indexing and easy browsing first, built up step by step.

## Done (November 2026)

- Specs spot-checked against Wikipedia: 20 corrections (designers, build numbers, notes that
  overstated race results or contradicted other entries, SC63 and Urus ST-X status).
- Photo gaps cut from 18 cars to 4: 33 Creative Commons photos from Flickr and 4 Commons files that
  sat outside their cars' categories, all checked by eye. Car pages now link to more photos.
- Public link without setup via raw.githack.com (see CLAUDE.md).

## Next

- [ ] **GitHub Pages.** One click by the owner: Settings → Pages → Deploy from a branch → `main` /
      root. Then https://wam090.github.io/the-lambo-index/ works. The `noindex` tag stays until
      the owner decides to be listed by search engines.
- [ ] **Owned / Wanted tracking** with notes, saved per browser, with export/import.
      Revisit if the site goes public (then it would need accounts or a shared store).
- [ ] **Auto-refresh**: a monthly scheduled task that adds new Lamborghinis, runs `images.py` and
      `flickr.py --all-gaps`, reviews new photos by eye, rebuilds and opens a pull request.
      First job, cars missing from the index (verify each before adding):
      Huracán STJ (2024, 10 cars), Fenomeno Roadster (2026, 15 cars), Revuelto SV (2026),
      Urus SE Performante (2026).
- [ ] **Last 4 photo gaps**: SC20, Invencible, Auténtica, Urus ST-X. Every photo found is
      copyrighted. Options: ask Flickr photographers to licence one photo each, or use Lamborghini
      press photos (owner registers on media.lamborghini.com; editorial-use terms). Owner's call.
      The Portofino has only an interior photo.
- [ ] **Spec doubts left open**: Countach 25th Anniversary 657 or 658 built; Miura SVJ (about six
      factory cars) and Diablo SV-R (31 or 34) left blank; Gallardo LP560-4 restyle credited to
      Walter de Silva on Wikipedia and to Filippo Perini elsewhere (we keep the original designer).

## Ideas

- Specs depth: top speed, 0–100 km/h, weight, price when new.
- Chassis-level detail for one-offs and race cars (chassis numbers, race results).
- Link each car to its scale models. The diecast index built earlier was lost with its session
  workspace and was not in the uploaded zip; rebuild it inside this repo if wanted.
- Light theme toggle.

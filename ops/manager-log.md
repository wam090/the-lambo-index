# Manager log

Written only by the Manager (user, 2026-11-22, approval D). Chat history is working memory; this file
holds what must outlive a Manager chat: the user's decisions as given, open approvals, this week's
outcomes, check-ins and scheduled tasks, open loops and housekeeping. A new Manager reads it first,
from origin/main: an unmerged branch copy carries no authority (Cyber, 2026-11-22).
Rules: read before you write; one rephrased line per entry, dated; never invent names or figures (mark
unknowns [TBC]); project rules stay in CLAUDE.md and BACKLOG.md (the Dev copies decisions there).
Pushed the moment the user decides, even outside working hours; the Manager merges it at night after
Cyber's OK.

## Open approvals (asked, not yet answered)

(none)

## Decisions received (newest first)

- 2026-11-22 E, yes: every working night at 05:30 Riyadh (02:30 UTC) a final check and one complete
  report; Thursdays at 05:30 Riyadh a weekly close with at most 3 outcomes for the next week.
- 2026-11-22 D, yes: this log (Manager only; pushed when the user decides; merged after Cyber's OK).
- 2026-11-22: old chats are archived as soon as they are done (no clutter). The Manager can archive,
  not delete; the user deletes in the app if wanted.
- 2026-11-22 C, yes: static car pages start now, no longer "after the photo gaps".
- 2026-11-22 B: countach-lp500 keeps its 2 current photos of the 2021 recreation as the car's own ("the
  car came to existence"). Photo's 2 new own-Flickr photos are not added (the user wrote "no"; read so,
  open to correction).
- 2026-11-22 A, yes ("stay safe as much as possible"): an owner's written no-use or ask-first notice
  (profile or caption) rejects the photo whatever the Flickr share setting; Kevin Stec's (kyter) 2
  photos leave 350-gts (3 photos to 1).
- 2026-11-22: the user raised the Manager's model (token plan in BACKLOG.md); successors use the same
  model at effort max. Do not propose lowering it.
- 2026-11-22: every Manager message is complete on its own: done since the user's last message, every
  open approval until answered (lettered, with a pick), next; tables for data; a receipt for each
  decision ("📌 Logged: <item> — <update>" or "⚠️ NOT logged: <reason>").

## Outcomes this week (agreed 2026-11-22; close Thu 26 Nov, 05:30 Riyadh)

| Outcome | Due (Riyadh) | Status |
|---|---|---|
| Static car pages live on the site | Tue 1 Dec [TBC: Dev_0.12's estimate] | Dev_0.12 started 22 Nov 21:09 UTC: design, Cyber, then code |
| Cars with fewer than 4 photos: 29 → 24 | Sun 29 Nov | 29 on 22 Nov |
| Scout run of Mon 23 Nov merged | Tue 24 Nov | Dev_0.11 builds it; pointer fires 23 Nov 02:17 UTC |

## Check-ins and scheduled tasks

Never touch the user's other scheduled tasks; never call list_triggers (it lists them all).

| What | When (UTC) | Task id |
|---|---|---|
| Manager: nightly check (books the next first) | 2026-11-23 02:30, then daily | trig_01QkdhVqFN45cdPEQttfjuXL (send_later; a new id each night) |
| Weekly close | Thursdays 02:30, inside the nightly check | (same chain) |
| Scout "Lambo Index scout" | Mondays 00:47 | trig_01UUEm7GWXBLcFjD7p3eHGRo |
| Scout pointer into the Dev chat | Mondays 02:17 | trig_01Mg3Ti1kQqKQMim31ZDopNK (into Dev_0.11, checked 22 Nov 21:07) |
| Photo hunt into Photo_v0.2 | daily 21:05 | trig_013nHtSsabYC6KrrAx5cjMQo |
| Design review into the Web designer | 22:17 on the 4th (CRON_TZ=Asia/Riyadh 17 1 5 * *); next 2026-12-04 | trig_01JDbq6TY7vhifMPmydkSxJX |
| Disabled: Dev quality pass (done 2026-11-21) | — | trig_016Uth55kTrSNuvJWCzYFvNt |
| Disabled: audit and its pointer (user stopped it 2026-11-21) | — | trig_01Cn6vQ1xuJLBWbq1Mis3pzS, trig_01EjzdfGNVt2i45bjf1LqeiD |
| Gone: Manager_v0.7's one-shot orders (fired 22 Nov 21:02) and its nightly check (deleted) | — | trig_01731rLm8q5okfsPbxps39KW, trig_01AsZRpXJUkXwgh4EGCg7siV |

## Team (find chats by title, verify with get_session; models and effort: BACKLOG.md token plan)

| Role | Chat | Note |
|---|---|---|
| Manager | Manager_v0.8 | since 2026-11-22 21:04 UTC; Opus 5.5 max; hands over at about 40% measured |
| Dev | Dev_0.11 | PR #120 (temerario-spyder), the decisions PR, the Scout PR of 23 Nov; then stops |
| Dev | Dev_0.12 | since 2026-11-22 21:09 UTC; Opus 5.5 xhigh (token plan "Extreme", read as xhigh [TBC]); static car pages; Photo picks from 22 Nov; Scout runs from 30 Nov |
| Cyber | Cyber_v0.6 | |
| Photo | Photo_v0.2 | picks go to Dev_0.12 from 22 Nov 21:10 UTC |
| Web designer | Web designer | monthly design review only |

## Open loops

- 2026-11-22, Dev_0.11: `temerario-spyder` (shown 18 Nov 2026 in Los Angeles; the user flagged it
  missing on 22 Nov) is draft PR #120, orders confirmed by Manager_v0.8 at 21:10 UTC: Cyber, then
  merge. Photo_v0.2 hunts it first; Dev_0.12 applies a legal photo after #120 is merged.
- 2026-11-22, Dev_0.11: one PR recording the 2026-11-22 decisions in BACKLOG.md and CLAUDE.md (A to E,
  Manager model, report format, archiving, REFRESH.md reveal-date fix) plus Cyber's items: the
  design-review line, decision D narrowly (the Manager changes only this file, through a PR Cyber
  checks, and merges it; read from origin/main), the nightly check as a send_later chain; removes
  Kevin Stec's 2 photos from 350-gts. Cyber checks, Dev merges.
- Manager: recreate the Scout pointer into Dev_0.12 (prompt byte-identical to tools/REFRESH.md Setup)
  after 23 Nov 02:30 UTC and before 30 Nov 00:45 UTC; delete the old one; Cyber confirms it with
  get_trigger; Dev_0.12 records the new id in REFRESH.md through a PR.
- Dev_0.12: a design PR and an estimate in nights for the static pages (asked 22 Nov 21:09 UTC).
- Checks to carry with the user (not approvals): B was read as "do not add Photo's 2 new
  countach-lp500 photos" (the user may say "add them"); F (add the Spyder outside working hours) got
  no answer, so it is done in working hours on 22 Nov.
- 2026-12-03, Photo: retry the 7 cars with no photo.

## Process fixes

- 2026-11-22, the Temerario Spyder miss: the Scout's 16 Nov notes named the 18 Nov reveal, but nobody
  acted on it, and the weekly run left a 5-day gap. From now on: (1) a reveal date in a Scout note
  gets a Manager send_later for the day after, and the Dev adds the car once it is shown; (2) the
  Manager's nightly check runs one web search for Lamborghini cars shown in the last 48 hours.

## Weekly closes

(first close: Thu 26 Nov)

## Housekeeping

- 2026-11-22: archived Manager_v0.5 and Manager_v0.6 (user: no clutter). Every older Lambo chat was
  already archived.
- Next to archive: Manager_v0.7 (after Manager_v0.8's first report); Dev_0.11, once its last PR is
  merged and it has no open branch.
- Other projects' chats and tasks are never touched.

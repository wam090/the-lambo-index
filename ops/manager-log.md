# Manager log

Written only by the Manager (user, 2026-11-22, approval D). Chat history is working memory; this file
holds what must outlive a Manager chat: the user's decisions as given, open approvals, this week's
outcomes, check-ins and scheduled tasks, open loops and housekeeping. A new Manager reads it first.
Rules: read before you write; one rephrased line per entry, dated; never invent names or figures (mark
unknowns [TBC]); project rules stay in CLAUDE.md and BACKLOG.md (the Dev copies decisions there).
Pushed the moment the user decides, even outside working hours; merged at night after Cyber's OK.

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
| Static car pages live on the site | Tue 1 Dec [TBC: Dev's estimate] | design starts 23 Nov |
| Cars with fewer than 4 photos: 29 → 24 | Sun 29 Nov | 29 on 22 Nov |
| Scout run of Mon 23 Nov merged | Tue 24 Nov | waiting for the run |

## Check-ins and scheduled tasks

Never touch the user's other scheduled tasks; never call list_triggers (it lists them all).

| What | When (UTC) | Task id |
|---|---|---|
| Manager: tonight's outbound work | 2026-11-22 21:02 | trig_01731rLm8q5okfsPbxps39KW |
| Manager: nightly check (books the next first) | 2026-11-23 02:30, then daily | trig_01AsZRpXJUkXwgh4EGCg7siV |
| Weekly close | Thursdays 02:30, inside the nightly check | (same chain) |
| Scout "Lambo Index scout" | Mondays 00:47 | trig_01UUEm7GWXBLcFjD7p3eHGRo |
| Scout pointer into the Dev chat | Mondays 02:17 | trig_01Mg3Ti1kQqKQMim31ZDopNK (into Dev_0.11) |
| Photo hunt into Photo_v0.2 | daily 21:05 | trig_013nHtSsabYC6KrrAx5cjMQo |
| Design review into the Web designer | monthly; next 2026-12-04 22:17 [TBC: CLAUDE.md says 06:17 on the 5th] | trig_01JDbq6TY7vhifMPmydkSxJX |
| Disabled: Dev quality pass (done 2026-11-21) | — | trig_016Uth55kTrSNuvJWCzYFvNt |
| Disabled: audit and its pointer (user stopped it 2026-11-21) | — | trig_01Cn6vQ1xuJLBWbq1Mis3pzS, trig_01EjzdfGNVt2i45bjf1LqeiD |

## Team (find chats by title, verify with get_session; models and effort: BACKLOG.md token plan)

| Role | Chat | Note |
|---|---|---|
| Manager | Manager_v0.7 | hands over at about 40% measured; successor reads this file first |
| Dev | Dev_0.11 | retires after tonight's decisions PR; Dev_0.12 takes the role |
| Cyber | Cyber_v0.6 | |
| Photo | Photo_v0.2 | first hunt 2026-11-22 21:05 UTC |
| Web designer | Web designer | monthly design review only |

## Open loops

- 2026-11-22 21:00 UTC, Dev_0.11: one PR recording the 2026-11-22 decisions in BACKLOG.md and
  CLAUDE.md (Photos rule A; countach-lp500 per B; static pages now per C; Manager model; report
  format; this log in the Files table and the Manager line); remove Kevin Stec's 2 photos from
  350-gts. Cyber checks, Dev merges, then the Manager archives Dev_0.11.
- 2026-11-22 21:00 UTC, Manager: create Dev_0.12 for static car pages (design, Cyber's review, then
  build); recreate the Scout pointer into it (prompt byte-identical to tools/REFRESH.md Setup) and
  delete the old one; tell Photo_v0.2 and Cyber_v0.6 the Dev's new title.
- Manager: confirm the design review's schedule with get_trigger and fix the line above.
- 2026-12-03, Photo: retry the 7 cars with no photo.

## Weekly closes

(first close: Thu 26 Nov)

## Housekeeping

- 2026-11-22: archived Manager_v0.5 and Manager_v0.6 (user: no clutter). Every older Lambo chat was
  already archived.
- Next to archive: Dev_0.11, once its last PR is merged.
- Other projects' chats and tasks are never touched.

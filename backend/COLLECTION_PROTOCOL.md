# Oreon — Per-Session Recording Checklist (squat + hammer curl)

Bench is parked — only **squat** and **hammer curl** this round. Goal: good form from
everyone, faults from whoever's willing (you backfill the rest yourself).

## 0. Before you hit record (setup)
- [ ] Get their **metadata**: sex (M/F), height (cm), weight (kg), experience (beginner/experienced).
- [ ] **Fitted clothing** — no baggy hoodies/pants (they wreck landmark tracking).
- [ ] Camera: **side view**, phone propped **stable**, **full body in frame**, decent lighting.
      (It no longer matters which side faces the camera — the engine auto-picks the visible side.)
- [ ] One clean **video per set** (don't mix sets in one clip).

## 1. Squat
- [ ] **Good set** — 8–10 reps, their natural form → label `good`
- [ ] Fault sets (~5 reps each, only if they can do them cleanly):
  - [ ] `shallow` — deliberately not deep enough
  - [ ] `lean` — excessive forward torso lean
  - [ ] `no-lockout` — don't stand all the way up between reps

## 2. Hammer curl
- [ ] **Good set** — 8–10 reps, natural form → label `good`
- [ ] Fault sets (~5 reps each, only if clean):
  - [ ] `partial-curl` — don't bring the weight up high enough
  - [ ] `partial-extension` — don't lower all the way down
  - [ ] `swing` — use momentum / body english

## 3. After recording (tag every video)
From `backend/` with the venv active, for each uploaded session:
```
python tag_session.py <id> --person <name> --sex <M/F> --height <cm> --weight <kg> --label <good/shallow/...>
```
- [ ] Verify the new row in `data/subjects.csv` (metadata + label correct).

## Priorities (when short on time)
1. **MUST:** one `good` squat set + one `good` hammer-curl set from **everyone**. This is the
   non-negotiable — good form across many bodies is what makes the thresholds generalize.
2. **NICE:** fault sets from whoever's willing, spread across **different body types**.
3. **You backfill** any missing faults yourself (you produce clean, controlled ones on demand).

## Who to target (~10–15 people, diversity > count)
- Mix of M/F — get **at least 4–5 women** (no separate female model; diversity is how it generalizes).
- Vary **limb proportions** (long/short femur drives squat lean), height, body weight, and
  **experience** (beginners give natural faults; experienced give clean reps).
- 12 varied people beats 20 similar ones.

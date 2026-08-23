# ThunderWatch MY — Kanban (6-HOUR HACKATHON EDITION)

Re-cut 2026-08-23 after user confirmed: **6-hour timeline**, GitHub Pages hosting, bot token incoming, prd-prep skill saved.
All stretch items CUT. Critical path: core scorer → radar tab → deploy → bot wiring → rehearsal.

## To Do

**Phase 1 — Data core (≈60 min) — CRITICAL PATH START**
- [ ] 1.1 `risk.py`: grid-sampler + Open-Meteo multi-coord fetch + deterministic scorer (CAPE+precip-prob weighted, not code-only) + nearest-risk haversine → JSON out
- [ ] 1.2 data.gov.my `/weather/warning` parser + district/state match
- [ ] 1.3 Smoke-run scorer on KL coords, eyeball output

**Phase 3 — Radar tab (≈90 min, parallel with 1.x)**
- [ ] 3.1 Promote smoke-map to dashboard shell: dark theme, tabs (Radar | Forecast), MYT labels
- [ ] 3.2 Frame preloading for smooth play + legend (scheme 2 blue) + attribution
- [ ] 3.3 User-location marker from URL param (?lat=&lon=) so chat replies can deep-link

**Phase 4 — Forecast tab lite (≈45 min)**
- [ ] 4.1 Static heatmap: run scorer over a fixed Malaysia grid once → bake `grid.json` → Leaflet.heat + hourly slider, "modeled, not radar" label

**Phase 6 — Deploy & demo (≈30 min)**
- [ ] 6.1 Push dashboard to GitHub Pages (repo: thunderwatch-my)
- [ ] 6.2 Cache warm-up: open all tabs before judges; RainViewer tiles cached by browser
- [ ] 6.3 One 3-min dry run following PRD §11 flow

**Phase 2 — Chat agent (≈90 min, AFTER bot token arrives)**
- [ ] 2.1 Telegram bot: location-share handling (long-poll, stdlib or python-telegram-bot)
- [ ] 2.2 Wire location → Phase-1 core → reply template (PRD §11 format + dashboard deep-link)
- [ ] 2.3 Qwen explanation layer (grounded in computed values) — degrade to template-only if time runs out

## In Progress

- [ ] ⏳ **AWAITING BOT TOKEN** from user (BotFather) — only blocker; everything else is unblocked

## Done ✅

- [x] 0.1 RainViewer MY coverage pixel-verified (Peninsular/Sarawak/Sabah)
- [x] 0.2 Free-tier constraints: no nowcast (0 frames), scheme 2 only, zoom ≤7, 100 req/min, attribution required
- [x] 0.3 Open-Meteo fields verified (`weather_code` etc.); note: scorer must not be code-only (current KL window has no 95/96/99 hours)
- [x] 0.4 data.gov.my real endpoints verified: `/weather/warning`, `/weather/forecast` (PRD paths were wrong)
- [x] 0.5 Radar prototype live: `smoke-map/index.html`
- [x] 0.6 `prd-prep` skill saved for reuse

## CUT (6-hour rule)

- ❌ Bahasa Malaysia mode
- ❌ Scheduled threshold alert (re-poll)
- ❌ Smooth-animation polish beyond basic preloading
- ❌ WhatsApp integration
- ❌ Dynamic heatmap interpolation tuning (bake static grid instead)

# ThunderWatch MY — Kanban (6-HOUR HACKATHON EDITION)

Updated 2026-08-23 ~13:00 MYT: MVP deployed + **commute advisor shipped**.

## In Progress

- [ ] User acceptance test: @ThunderWatch_Bot — location flow + `/commute Gombak | KL Sentral`

## To Do

- [ ] Cache warm-up right before the demo
- [ ] (Post-demo / Devin candidate) Multi-city GTFS expansion, MCP journey planner, fares, road-level routing

## Done ✅

- [x] 0.x API verifications + `prd-prep` skill
- [x] 1.x `core/risk.py` grid pipeline (live-tested w/ real warnings)
- [x] 2.x `bot/bot.py` running as @ThunderWatch_Bot
- [x] 3.x Radar tab + 4.x Forecast tab (live at GitHub Pages)
- [x] 6.1/6.2 Deployed: https://zisn-r.github.io/thunderwatch-my/ (built, HTTP 200)
- [x] E2E: KL + Penang replies verified
- [x] **F1 Commute advisor**: `/commute origin | dest` → inline keyboard (🏍/🚗/🚆) → route weather (8-pt Open-Meteo sample, same scorer) → mode-switch advice with nearest LRT/Monorail stations from live data.gov.my GTFS (`rapid-rail-kl`, 187 stops)
- [x] F1 verified: Gombak→KL Sentral dry-day path + station lookup (GOMBAK KJ1 → KL SENTRAL KJ15, Kelana Jaya line) + honest "straight-line sampling" disclaimer
- [x] F1 demo override: `DEMO_RAIN=1` env flag injects heavy rain so judges see the switch recommendation on dry days (clearly labeled in-reply)

## CUT (6-hour rule)

- ❌ Bahasa Malaysia · ❌ Threshold alert re-poll · ❌ WhatsApp · ❌ Road-graph routing (needs OSRM; labeled honestly in replies instead)

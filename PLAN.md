# ThunderWatch MY — Execution Plan (Taskmaster AI prep)

Generated from `ThunderWatch_MY_PRD_v3.md`. All API facts below were **live-verified on 2026-08-23** — no planning assumptions carried forward untested.

---

## Verified Data Facts (smoke tests, 2026-08-23)

| Source | Status | Verified details |
|---|---|---|
| RainViewer `weather-maps.json` | ✅ LIVE | No key, `host` + `radar.past` (13 frames ≈ 2 h @ ~10 min). Radar reflectivity **confirmed over Peninsular MY, Sarawak, Sabah** (pixel-level check, scheme 2). |
| RainViewer nowcast | ❌ DEAD | Free-tier nowcast discontinued 2026-01-01. `nowcast` array returns 0 frames. **Scrubber = past 2 h only.** |
| RainViewer color schemes | ⚠️ Restricted | Only scheme **2 (Universal Blue)** works free; scheme 4 returns transparent tiles. |
| RainViewer zoom | ⚠️ Capped | **Max useful zoom = 7.** z≥8 tiles are identical blank placeholders. Dashboard radar view is national-scale; use `maxNativeZoom:7` + upscale in Leaflet. |
| RainViewer limits | ⚠️ | 100 req/IP/min, cache aggressively, non-commercial/educational use, attribution link to rainviewer.com **mandatory**. |
| Open-Meteo | ✅ LIVE | `weather_code`, `precipitation_probability`, `cape`, `wind_speed_10m`, `wind_direction_10m` all return (48 h hourly). Legacy `weathercode` also still works. |
| data.gov.my | ✅ LIVE — **endpoints corrected** | PRD guessed wrong. Real: `GET /weather/warning` (live MetMalaysia warnings, bilingual `_bm`/`_en`, incl. thunderstorm text) and `GET /weather/forecast` (7-day, by location). Old `/weather-alert` + `/forecast` paths 404. |
| Open-Meteo thunder codes | ⚠️ Note | Current KL 48 h window had **0 hours of code 95/96/99** — risk scoring must weight CAPE + precip-probability, not rely on weather codes alone (v2 formula already does; keep it). |

## Scope deltas vs PRD v3 (must adopt)

1. **Feature 5 Radar tab**: time control covers *past frames only* — drop "short nowcast" from UI copy; label "Radar — last ~2 hours".
2. **Radar zoom UX**: nationwide radar at z≤7; base map can zoom further (radar upscales). Don't promise city-level radar in the pitch.
3. **data.gov.my integration** uses `/weather/warning` + `/weather/forecast` (verified paths) — remove "verify endpoints" risk, replace with schema-parsing task.
4. Rate-limit mitigation is now mandatory, not optional: 100 req/min cap + demo-day judge traffic.

---

## Phases & sub-tasks

### Phase 0 — De-risk & verify ✅ (done this session)
- [x] RainViewer coverage smoke test over Malaysia (pixel-level) → **PASS**
- [x] Open-Meteo field-name verification → **PASS** (use `weather_code` spelling)
- [x] data.gov.my endpoint discovery → **PASS** (`/weather/warning`, `/weather/forecast`)
- [x] Free-tier constraints mapped (nowcast gone, scheme 2 only, zoom ≤7, 100 req/min)
- [x] Working radar-tab prototype built (`smoke-map/index.html`)

### Phase 1 — Shared data core (chat agent + forecast tab both depend on it)
- 1.1 Grid-sampler: ring of N points around user lat/lon (haversine offsets)
- 1.2 Open-Meteo batch fetch per point (single multi-coordinate request to save quota)
- 1.3 Deterministic risk scorer v2 formula (weights: weather_code 95/96/99, CAPE bands, precip-prob; 4 levels)
- 1.4 Nearest above-threshold point + distance/bearing via haversine
- 1.5 data.gov.my warning cross-check: parse `/weather/warning`, match district/state to user location
- 1.6 Response cache layer (per location, TTL ~10 min) — rate-limit insurance

### Phase 2 — Chat agent (Telegram + Hermes + Qwen)
- 2.1 Telegram bot skeleton: location-share handling (photo/venue/live-location fallback to text)
- 2.2 Hermes orchestration: wire location → Phase-1 core → structured risk object
- 2.3 Qwen explanation prompt: grounded in computed values only, 4 risk levels, recommended action
- 2.4 Warning merge: official warning present → escalate language, cite MetMalaysia
- 2.5 Response template matching PRD §11 demo format

### Phase 3 — Dashboard: Radar tab (must-have, build first per PRD)
- 3.1 Leaflet/OSM shell, Malaysia-centered, dark styling to match reference UI
- 3.2 RainViewer overlay: scheme 2, `maxNativeZoom:7`, opacity + legend
- 3.3 Frame loader from `weather-maps.json` (fetch + tile-URL cache)
- 3.4 Play/scrub control over past frames only, MYT timestamps
- 3.5 User-location marker (shared component)
- 3.6 Attribution + honest label: "Radar — last ~2 hours (RainViewer)"

### Phase 4 — Dashboard: Forecast tab (nice-to-have)
- 4.1 Reuse Phase-1 grid output as heatmap points (Leaflet.heat)
- 4.2 Hourly slider over Open-Meteo hourly array
- 4.3 Label "Forecast — modeled, not radar"; keep tabs visually distinct

### Phase 5 — Stretch
- 5.1 Threshold alert: scheduled re-poll (Hermes cron) → push on score crossing
- 5.2 Bahasa Malaysia response mode (data.gov.my `_bm` fields help)
- 5.3 Smooth play animation (frame preloading)

### Phase 6 — Demo readiness
- 6.1 Hosting for dashboard (static: GitHub Pages / Netlify / Vercel)
- 6.2 End-to-end dry run on demo phone/data; cache warm-up script before judges arrive
- 6.3 Traceability check: every chat number maps to a logged API response
- 6.4 Pitch script update: lead with radar tab, acknowledge "no tracked cells" defusal line (PRD §13)

---

## Timeline re-cut (user-confirmed constraints)
- **6-hour hackathon window** → all stretch items cut; see KANBAN.md "CUT" section
- **Hosting**: GitHub Pages (static dashboard only — bot runs locally during demo)
- **Bot token**: user creating via BotFather; Phase 2 starts on token arrival
- **Skill reuse**: this prep workflow saved as Hermes skill `prd-prep`

## Delegation matrix

| Agent / routine | Owns | Inputs | Output |
|---|---|---|---|
| **Research Agent** (me, done) | Phase 0 | PRD + live APIs | verified facts table above |
| **Core Pipeline Agent** | Phase 1 | user coords | scored grid JSON, nearest-risk object |
| **Chat Agent Builder** | Phase 2 | Telegram SDK, Hermes, Qwen | bot reply per template |
| **Dashboard Builder** | Phases 3–4 | RainViewer + core JSON | two-tab Leaflet app |
| **Alert Routine** (background cron) | 5.1 | core pipeline + subscriber list | threshold push messages |
| **Demo/QA Agent** | Phase 6 | running system | dry-run report, cache state |

Critical path: **1.1–1.3 → 2.2 → 3.1–3.4** (radar tab can run in parallel from 3.1).

# ThunderWatch MY ⛈

AI-powered thunderstorm awareness for Malaysia — Telegram bot + live dashboard.

- **Radar tab**: real RainViewer radar tiles (last ~2 h), play/scrub. Free-tier limits: Universal Blue scheme, zoom ≤ 7, no nowcast.
- **Forecast tab**: Open-Meteo grid-sampled risk heatmap (modeled, not radar), hourly slider.
- **Chat agent** (`bot/bot.py`): location → deterministic risk score → plain-language advisory + MetMalaysia warning cross-check.

## Run

```bash
# dashboard: open docs/index.html or serve it (GitHub Pages deploys docs/)
# bot:
export TELEGRAM_BOT_TOKEN=***
python bot/bot.py
```

## Layout
- `core/risk.py` — grid-sampler + scorer + warning cross-check (stdlib only)
- `docs/index.html` — dashboard (GitHub Pages source)
- `bot/bot.py` — Telegram bot (long-poll, stdlib only)
- `PLAN.md` / `KANBAN.md` — execution plan and board

Data sources: Open-Meteo · RainViewer · data.gov.my (`/weather/warning`, `/weather/forecast`) · OpenStreetMap.
Radar imagery © [RainViewer](https://www.rainviewer.com/) — attribution required by their free terms.

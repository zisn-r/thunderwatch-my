#!/usr/bin/env python3
"""ThunderWatch MY — Telegram bot (stdlib only, long-polling).

Set TELEGRAM_BOT_TOKEN env var, then:  python bot.py
Dashboard deep-link base: set DASHBOARD_URL (defaults to the GitHub Pages URL).

Flow: user shares location -> core.assess() -> PRD §11-formatted reply with
dashboard deep-link (?lat=&lon=) + official warning cross-check.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core"))
import risk  # noqa: E402

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://zisn-r.github.io/thunderwatch-my/")
API = f"https://api.telegram.org/bot{TOKEN}"


def tg(method, **payload):
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def build_reply(lat, lon):
    r = risk.assess(lat, lon)
    link = f"{DASHBOARD_URL}?lat={lat:.5f}&lon={lon:.5f}"
    lines = ["⛈ *Thunderstorm Risk Advisory*", ""]
    if r["nearest_elevated"]:
        n = r["nearest_elevated"]
        lines.append(f"Elevated thunderstorm indicators detected *~{n['dist_km']:.0f} km "
                     f"{n['direction']}* of your location (based on current forecast data).")
        if r["trend_estimate"] == "approaching":
            lines.append("Prevailing winds suggest possible movement toward your area "
                         "over the next 1–2 hours.")
        elif r["trend_estimate"] == "receding":
            lines.append("Prevailing winds suggest the activity is moving away from your area.")
        lines.append(f"Risk Level: *{n['level']}* (score {n['peak_score']:.0f}/100)")
        rec = {"Severe": "Take shelter now; postpone all outdoor plans.",
               "High": "Prepare for heavy rain; avoid outdoor activity.",
               "Moderate": "Keep an eye on the sky; plan indoor alternatives.",
               "Low": "No action needed right now."}[n["level"]]
        lines.append(f"Recommendation: {rec}")
    else:
        lines.append(f"No elevated thunderstorm risk within ~30 km right now "
                     f"(*{r['risk_level_at_user']}*, score {r['score_at_user']:.0f}/100).")
    if r["official_warnings_active"]:
        titles = "; ".join(w["title_en"] for w in r["official_warnings"][:2] if w.get("title_en"))
        lines.append(f"⚠️ Official MetMalaysia warning active: {titles}")
    lines += ["", f"🗺 View live map: {link}"]
    return "\n".join(lines)


def extract_location(msg):
    loc = msg.get("location")
    if loc:
        return loc["latitude"], loc["longitude"]
    text = (msg.get("text") or "").strip()
    parts = text.replace(",", " ").split()
    if len(parts) == 2:
        try:
            lat, lon = float(parts[0]), float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except ValueError:
            pass
    return None


def main():
    if not TOKEN:
        print("Set TELEGRAM_BOT_TOKEN first.", file=sys.stderr)
        sys.exit(1)
    me = tg("getMe")
    print(f"Bot online: @{me['result']['username']}")
    offset = None
    while True:
        try:
            args = {"timeout": 25}
            if offset:
                args["offset"] = offset
            res = tg("getUpdates", **args)
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                chat = msg.get("chat", {}).get("id")
                loc = extract_location(msg)
                if loc:
                    try:
                        tg("sendMessage", chat_id=chat, text=build_reply(*loc),
                           parse_mode="Markdown")
                    except Exception as e:
                        tg("sendMessage", chat_id=chat, text=f"Error: {e}")
                else:
                    tg("sendMessage", chat_id=chat,
                       text="⛈ ThunderWatch MY — share your location (📎 → Location) "
                            "or send 'lat lon' and I'll check thunderstorm risk near you.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"poll error: {e}", file=sys.stderr)
            time.sleep(3)


if __name__ == "__main__":
    main()

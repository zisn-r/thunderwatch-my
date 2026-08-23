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
import risk      # noqa: E402
import commute   # noqa: E402

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://zisn-r.github.io/thunderwatch-my/")
API = f"https://api.telegram.org/bot{TOKEN}"

# Conversation state for the commute flow: chat_id -> {"origin": str|None}
commute_state = {}

MODE_KEYBOARD = {
    "inline_keyboard": [[
        {"text": "🏍 Motorcycle", "callback_data": "mode:motorcycle"},
        {"text": "🚗 Car", "callback_data": "mode:car"},
        {"text": "🚆 Public Transport", "callback_data": "mode:public_transport"},
    ]]
}


def tg(method, **payload):
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            payload[k] = json.dumps(v)
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


# --- commute flow -----------------------------------------------------------

def handle_commute_text(chat_id, origin, dest):
    commute_state[chat_id] = {"origin": origin, "dest": dest}
    tg("sendMessage", chat_id=chat_id,
       text=f"🚦 Commute check: *{origin}* → *{dest}*\nHow are you travelling?",
       parse_mode="Markdown", reply_markup=MODE_KEYBOARD)


def handle_mode_choice(chat_id, mode, demo_rain=False):
    st = commute_state.pop(chat_id, None)
    if not st:
        tg("sendMessage", chat_id=chat_id, text="Start again with /commute.")
        return
    try:
        o = commute.geocode(st["origin"])
        d = commute.geocode(st["dest"])
        if not o or not d:
            tg("sendMessage", chat_id=chat_id,
               text="Sorry, I couldn't find one of those places. Try /commute again.")
            return
        res = commute.assess_route((o[0], o[1]), (d[0], d[1]), mode)
        if demo_rain and not res["recommend_switch"]:
            # Demo override: simulate a heavy-rain window so judges can see
            # the mode-switch recommendation even on a dry day.
            res["worst"] = {"score": 78.0, "precip_prob": 85,
                            "time": res["worst"].get("time"), "seg": res["worst"].get("seg", 0)}
            res["worst_level"] = risk.risk_level(res["worst"]["score"])
            res["recommend_switch"] = True
        text = commute.human_advice(st["origin"], st["dest"], res)
        if demo_rain:
            text += "\n\n_(demo simulation: heavy rain injected)_"
        tg("sendMessage", chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        tg("sendMessage", chat_id=chat_id, text=f"Commute check failed: {e}")


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
            demo_rain = os.environ.get("DEMO_RAIN") == "1"
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1

                cb = upd.get("callback_query")
                if cb:
                    tg("answerCallbackQuery", callback_query_id=cb["id"])
                    data = cb.get("data", "")
                    if data.startswith("mode:"):
                        handle_mode_choice(cb["message"]["chat"]["id"],
                                           data.split(":", 1)[1], demo_rain)
                    continue

                msg = upd.get("message") or {}
                chat = msg.get("chat", {}).get("id")
                text = (msg.get("text") or "").strip()

                if text.startswith("/commute"):
                    rest = text[len("/commute"):].strip()
                    if "|" in rest:
                        origin, dest = [p.strip() for p in rest.split("|", 1)]
                        if origin and dest:
                            handle_commute_text(chat, origin, dest)
                            continue
                    tg("sendMessage", chat_id=chat,
                       text="🚦 *Commute weather advisor*\n\n"
                            "Send your route like this:\n"
                            "`/commute Gombak | KL Sentral`\n\n"
                            "I'll ask your transport mode, check weather along "
                            "the route, and suggest a safer alternative if "
                            "heavy rain is expected.",
                       parse_mode="Markdown")
                    continue

                if chat in commute_state:
                    if "|" in text:
                        origin, dest = [p.strip() for p in text.split("|", 1)]
                        if origin and dest:
                            handle_commute_text(chat, origin, dest)
                            continue

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
                            "or send 'lat lon' for storm risk near you.\n"
                            "Or try the commute advisor: /commute")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"poll error: {e}", file=sys.stderr)
            time.sleep(3)


if __name__ == "__main__":
    main()

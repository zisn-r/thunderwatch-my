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
from i18n import t, level_name  # noqa: E402

STRINGS_BM_SET = "Bahasa ditetapkan kepada Bahasa Melayu. Hantar /en untuk English."

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://zisn-r.github.io/thunderwatch-my/")
API = f"https://api.telegram.org/bot{TOKEN}"

# Conversation state for the commute flow: chat_id -> {"origin": str|None}
commute_state = {}
chat_lang = {}  # chat_id -> "en" | "bm"


def lang_of(chat_id):
    return chat_lang.get(chat_id, "en")

MODE_KEYBOARD = {
    "inline_keyboard": [[
        {"text": "🏍 Motorcycle", "callback_data": "mode:motorcycle"},
        {"text": "🚗 Car", "callback_data": "mode:car"},
        {"text": "🚆 Public Transport", "callback_data": "mode:public_transport"},
    ]]
}
MODE_KEYBOARD_BM = {
    "inline_keyboard": [[
        {"text": "🏍 Motosikal", "callback_data": "mode:motorcycle"},
        {"text": "🚗 Kereta", "callback_data": "mode:car"},
        {"text": "🚆 Pengangkutan Awam", "callback_data": "mode:public_transport"},
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
    lang = "en"  # default; main() passes per-chat lang
    return build_reply_lang(lat, lon, lang)


def build_reply_lang(lat, lon, lang):
    r = risk.assess(lat, lon)
    link = f"{DASHBOARD_URL}?lat={lat:.5f}&lon={lon:.5f}"
    lines = [t(lang, "advisory_title"), ""]
    if r["nearest_elevated"]:
        n = r["nearest_elevated"]
        lines.append(t(lang, "elevated", dist=f"{n['dist_km']:.0f}", direction=n["direction"]))
        if r["trend_estimate"] == "approaching":
            lines.append(t(lang, "trend_approaching"))
        elif r["trend_estimate"] == "receding":
            lines.append(t(lang, "trend_receding"))
        lines.append(t(lang, "risk_line", level=level_name(lang, n["level"]),
                       score=f"{n['peak_score']:.0f}"))
        rec_key = {"Severe": "rec_severe", "High": "rec_high",
                   "Moderate": "rec_moderate", "Low": "rec_low"}[n["level"]]
        lines.append(t(lang, "rec", text=t(lang, rec_key)))
    else:
        lines.append(t(lang, "no_elevated", level=level_name(lang, r["risk_level_at_user"]),
                       score=f"{r['score_at_user']:.0f}"))
    if r["official_warnings_active"]:
        titles = "; ".join(w["title_en"] for w in r["official_warnings"][:2] if w.get("title_en"))
        lines.append(t(lang, "warnings", titles=titles))
    lines += ["", t(lang, "view_map", link=link)]
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
    lang = lang_of(chat_id)
    commute_state[chat_id] = {"origin": origin, "dest": dest}
    tg("sendMessage", chat_id=chat_id,
       text=t(lang, "commute_ask", origin=origin, dest=dest),
       parse_mode="Markdown",
       reply_markup=MODE_KEYBOARD_BM if lang == "bm" else MODE_KEYBOARD)


def handle_mode_choice(chat_id, mode, demo_rain=False):
    lang = lang_of(chat_id)
    st = commute_state.pop(chat_id, None)
    if not st:
        tg("sendMessage", chat_id=chat_id, text=t(lang, "commute_restart"))
        return
    try:
        o = commute.geocode(st["origin"])
        d = commute.geocode(st["dest"])
        if not o or not d:
            tg("sendMessage", chat_id=chat_id, text=t(lang, "commute_geofail"))
            return
        res = commute.assess_route((o[0], o[1]), (d[0], d[1]), mode)
        if demo_rain and not res["recommend_switch"]:
            # Demo override: simulate a heavy-rain window so judges can see
            # the mode-switch recommendation even on a dry day.
            res["worst"] = {"score": 78.0, "precip_prob": 85,
                            "time": res["worst"].get("time"), "seg": res["worst"].get("seg", 0)}
            res["worst_level"] = risk.risk_level(res["worst"]["score"])
            res["recommend_switch"] = True
        text = build_commute_reply(st["origin"], st["dest"], res, lang,
                                   o[:2], d[:2])
        if demo_rain:
            text += "\n\n_(demo simulation: heavy rain injected)_"
        tg("sendMessage", chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        tg("sendMessage", chat_id=chat_id, text=f"Commute check failed: {e}")


MODE_LABEL_KEYS = {"motorcycle": "mode_label_motorcycle", "car": "mode_label_car",
                   "public_transport": "mode_label_pt"}


def build_commute_reply(origin, dest, res, lang, origin_coords, dest_coords):
    w = res["worst"]
    precip = f", rain {w['precip_prob']}%" if w["precip_prob"] else ""
    if lang == "bm":
        precip = f", hujan {w['precip_prob']}%" if w["precip_prob"] else ""
    lines = [t(lang, "commute_title", origin=origin, dest=dest),
             t(lang, "commute_meta", mode=t(lang, MODE_LABEL_KEYS[res["mode"]]))]
    lines.append("")
    if not res["recommend_switch"]:
        lines.append(t(lang, "commute_ok", level=level_name(lang, res["worst_level"]),
                       score=f"{w['score']:.0f}", precip=precip))
        if res["mode"] == "motorcycle":
            lines.append(t(lang, "commute_ok_rain_jacket"))
    else:
        when = (w["time"] or "").replace("T", " ")
        lines.append(t(lang, "commute_heavy", when=when, score=f"{w['score']:.0f}", precip=precip))
        if res["mode"] in ("motorcycle", "car"):
            key = "commute_switch_moto" if res["mode"] == "motorcycle" else "commute_switch_car"
            lines.append(t(lang, key))
            if res["alternative"]:
                o, d = res["alternative"]["origin_station"], res["alternative"]["dest_station"]
                if res["mode"] == "motorcycle":
                    lines.append(t(lang, "commute_alt_stations", o=o["name"], od=o["dist_km"],
                                   d=d["name"]))
                else:
                    lines.append(t(lang, "commute_alt_nearest", o=o["name"], od=o["dist_km"]))
    # Deep link to the dashboard route view (OSRM road geometry) — all replies
    olat, olon = origin_coords
    dlat, dlon = dest_coords
    route_link = (f"{DASHBOARD_URL}?route=1&olat={olat:.5f}&olon={olon:.5f}"
                  f"&dlat={dlat:.5f}&dlon={dlon:.5f}")
    lines.append(t(lang, "view_map", link=route_link))
    lines += ["", t(lang, "commute_note")]
    return "\n".join(lines)


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

                if text in ("/bm", "/bahasa"):
                    chat_lang[chat] = "bm"
                    tg("sendMessage", chat_id=chat,
                       text="🇲🇾 " + STRINGS_BM_SET)
                    continue
                if text in ("/en", "/english"):
                    chat_lang[chat] = "en"
                    tg("sendMessage", chat_id=chat, text="🇬🇧 Language set to English.")
                    continue

                if text.startswith("/commute"):
                    rest = text[len("/commute"):].strip()
                    if "|" in rest:
                        origin, dest = [p.strip() for p in rest.split("|", 1)]
                        if origin and dest:
                            handle_commute_text(chat, origin, dest)
                            continue
                    tg("sendMessage", chat_id=chat,
                       text=t(lang_of(chat), "commute_help"),
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
                        tg("sendMessage", chat_id=chat,
                           text=build_reply_lang(*loc, lang=lang_of(chat)),
                           parse_mode="Markdown")
                    except Exception as e:
                        tg("sendMessage", chat_id=chat, text=f"Error: {e}")
                else:
                    tg("sendMessage", chat_id=chat, text=t(lang_of(chat), "welcome"))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"poll error: {e}", file=sys.stderr)
            time.sleep(3)


if __name__ == "__main__":
    main()

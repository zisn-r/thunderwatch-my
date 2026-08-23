#!/usr/bin/env python3
"""ThunderWatch MY — commute advisor (mode-aware route weather).

Scenario: Person A travels Gombak -> KL Sentral. Bot asks the transport mode,
samples weather ALONG the route (straight-line interpolation; no road-graph
routing — labeled honestly in replies), and advises switching modes if the
chosen mode is weather-fragile.

Data: Open-Meteo (weather, same scorer as core/risk.py), Nominatim
(geocoding place names), data.gov.my GTFS static (nearest rail/LRT stations).
Stdlib only.
"""
import csv
import io
import json
import math
import os
import time
import urllib.parse
import urllib.request
import zipfile

from risk import (score_hour, risk_level, haversine_km, fetch_open_meteo,
                  cache_get, cache_put)  # noqa: E402

UA_HEADERS = {"User-Agent": "ThunderWatch-MY/1.0 (hackathon demo; contact: izulr)"}
GTFS_URL = "https://api.data.gov.my/gtfs-static/prasarana?category=rapid-rail-kl"
GTFS_CACHE_S = 86400  # refresh daily per data.gov.my guidance

# Mode fragility: lower threshold = more weather-sensitive
MODE_THRESHOLDS = {
    "motorcycle": {"switch_score": 30, "switch_precip": 55, "label": "Motorcycle 🏍"},
    "car":        {"switch_score": 55, "switch_precip": 75, "label": "Car 🚗"},
    "public_transport": {"switch_score": 80, "switch_precip": 90, "label": "Public Transport 🚆"},
}


# --- geocoding --------------------------------------------------------------

def geocode(name):
    """(lat, lon, display) for a place name. Nominatim first, cached."""
    key = name.lower().strip()
    cached = cache_get("geo", key)
    if cached:
        return tuple(cached)
    q = urllib.parse.quote(name)
    url = (f"https://nominatim.openstreetmap.org/search?format=json&limit=1"
           f"&countrycodes=my&q={q}")
    req = urllib.request.Request(url, headers=UA_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read().decode())
        if res:
            out = (float(res[0]["lat"]), float(res[0]["lon"]), res[0]["display_name"])
            cache_put("geo", key, list(out))
            return out
    except Exception:
        pass
    return None


# --- GTFS station index -------------------------------------------------------

def load_stations():
    cached = cache_get("gtfs", "stations")
    if cached:
        return cached
    req = urllib.request.Request(GTFS_URL, headers=UA_HEADERS)
    data = urllib.request.urlopen(req, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(data))
    stops = [row for row in csv.DictReader(
        io.TextIOWrapper(z.open("stops.txt"), encoding="utf-8-sig"))
        if not row["stop_name"].startswith("__")]
    out = [{"id": s["stop_id"], "name": s["stop_name"],
            "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"])}
           for s in stops]
    cache_put("gtfs", ("stations",), out)
    return out


def nearest_stations(lat, lon, k=3):
    stops = load_stations()
    ranked = sorted(stops, key=lambda s: haversine_km(lat, lon, s["lat"], s["lon"]))
    out = []
    for s in ranked:
        d = haversine_km(lat, lon, s["lat"], s["lon"])
        out.append({**s, "dist_km": round(d, 2)})
        if len(out) >= k:
            break
    return out


# --- route sampling -----------------------------------------------------------

def route_points(origin, dest, n=8):
    """Straight-line interpolation (honest: not road-following)."""
    lat1, lon1 = origin
    lat2, lon2 = dest
    return [(lat1 + (lat2 - lat1) * i / (n - 1),
             lon1 + (lon2 - lon1) * i / (n - 1)) for i in range(n)]


def route_weather(points, hours_ahead=6):
    """One multi-coordinate Open-Meteo call; returns per-point hourly scores."""
    series = fetch_open_meteo(points)
    if not isinstance(series, list):
        series = [series]
    sampled = []
    for i, s in enumerate(series[:len(points)]):
        h = s.get("hourly", {})
        n = min(len(h.get("time", [])), hours_ahead)
        hours = []
        for j in range(n):
            sc = score_hour(
                (h.get("weather_code") or [None] * n)[j],
                (h.get("precipitation_probability") or [None] * n)[j],
                (h.get("cape") or [None] * n)[j],
            )
            hours.append({"time": h["time"][j], "score": round(sc, 1),
                          "precip_prob": (h.get("precipitation_probability") or [None] * n)[j],
                          "weather_code": (h.get("weather_code") or [None] * n)[j]})
        sampled.append(hours)
    return sampled


def assess_route(origin, dest, mode, hours_ahead=6):
    mode = mode if mode in MODE_THRESHOLDS else "car"
    th = MODE_THRESHOLDS[mode]
    pts = route_points(origin, dest)
    sampled = route_weather(pts, hours_ahead)

    # Flatten worst conditions across route + time window
    worst = {"score": 0, "precip_prob": 0, "time": None, "seg": 0}
    for seg, hours in enumerate(sampled):
        for h in hours:
            if h["score"] > worst["score"]:
                worst = {"score": h["score"], "precip_prob": h["precip_prob"] or 0,
                         "time": h["time"], "seg": seg}

    heavy = (worst["score"] >= th["switch_score"] or
             worst["precip_prob"] >= th["switch_precip"])

    # Alternative: nearest rail/LRT stations to origin and destination
    alt = None
    if mode != "public_transport":
        near_o = nearest_stations(*origin, k=1)[0]
        near_d = nearest_stations(*dest, k=1)[0]
        alt = {"origin_station": near_o, "dest_station": near_d}

    return {
        "mode": mode,
        "mode_label": th["label"],
        "route_points": len(pts),
        "worst": worst,
        "worst_level": risk_level(worst["score"]),
        "recommend_switch": heavy,
        "alternative": alt,
        "note": "Route weather sampled along a straight line between origin and "
                "destination (road-level routing not available on free data).",
    }


def human_advice(origin_name, dest_name, result):
    w = result["worst"]
    lines = [f"🚦 *Commute Weather Check: {origin_name} → {dest_name}*",
             f"Mode: {result['mode_label']} · window: next 6 hours", ""]
    if not result["recommend_switch"]:
        lines.append(f"✅ Conditions look manageable for your chosen mode "
                     f"(worst along route: *{result['worst_level']}*, "
                     f"score {w['score']:.0f}/100"
                     + (f", rain chance {w['precip_prob']}%" if w["precip_prob"] else "") + ").")
        if result["mode"] == "motorcycle":
            lines.append("Ride safe — carry a rain jacket just in case.")
    else:
        when = (w["time"] or "").replace("T", " ")
        lines.append(f"⚠️ *Heavy rain likely along your route* "
                     f"(peak around {when}, score {w['score']:.0f}/100"
                     + (f", rain chance {w['precip_prob']}%" if w["precip_prob"] else "") + ").")
        if result["mode"] == "motorcycle":
            lines.append("Motorcycle travel is risky in these conditions. "
                         "*Consider switching to public transport:*")
            if result["alternative"]:
                o, d = result["alternative"]["origin_station"], result["alternative"]["dest_station"]
                lines.append(f"🚆 Walk/ride to *{o['name']}* ({o['dist_km']} km away) "
                             f"→ rail to *{d['name']}* near your destination.")
        elif result["mode"] == "car":
            lines.append("Expect slow traffic and reduced visibility. "
                         "Leave earlier, or switch to rail if available:")
            if result["alternative"]:
                o = result["alternative"]["origin_station"]
                lines.append(f"🚆 Nearest station to you: *{o['name']}* ({o['dist_km']} km).")
    lines += ["", f"_{result['note']}_"]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("usage: python commute.py <origin> <destination> <mode>")
        sys.exit(2)
    o = geocode(sys.argv[1])
    d = geocode(sys.argv[2])
    if not o or not d:
        print("geocoding failed"); sys.exit(1)
    res = assess_route((o[0], o[1]), (d[0], d[1]), sys.argv[3])
    print(human_advice(sys.argv[1], sys.argv[2], res))
    print("\n--- raw ---")
    print(json.dumps(res, indent=2))

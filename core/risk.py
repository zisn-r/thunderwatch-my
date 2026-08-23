#!/usr/bin/env python3
"""ThunderWatch MY — Phase 1 data core (stdlib only, no deps).

Grid-sampled, deterministically-scored thunderstorm risk around a location.
Pipeline: ring of sample points -> Open-Meteo hourly fetch -> weighted score
-> nearest above-threshold point (haversine distance/bearing)
-> data.gov.my official-warning cross-check.

Usage:
    python risk.py 3.139 101.687            # human summary + JSON
    python risk.py 3.139 101.687 --json     # JSON only (for the bot layer)

Design notes (PRD v2/v3):
- Scorer is deliberately NOT weather-code-only: live check on 2026-08-23
  found 0 hours of codes 95/96/99 in a 48h KL window, while CAPE was
  active. Weights: thunder code, precip probability, CAPE band.
- Caching: results cached 10 min per rounded location (rate-limit insurance;
  RainViewer free tier also caps 100 req/min/IP).
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "ThunderWatch-MY/1.0 (hackathon demo)"}
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
CACHE_TTL_S = 600

RING_BEARINGS = [0, 45, 90, 135, 180, 225, 270, 315]
RING_RADII_KM = [10, 20, 30]
RISK_THRESHOLD = 50  # "High" and above counts as elevated risk

# --- geo helpers -----------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def offset_point(lat, lon, bearing_deg_, dist_km):
    r = 6371.0
    br = math.radians(bearing_deg_)
    p1, l1 = math.radians(lat), math.radians(lon)
    p2 = math.asin(math.sin(p1) * math.cos(dist_km / r)
                   + math.cos(p1) * math.sin(dist_km / r) * math.cos(br))
    l2 = l1 + math.atan2(math.sin(br) * math.sin(dist_km / r) * math.cos(p1),
                         math.cos(dist_km / r) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), (math.degrees(l2) + 540) % 360 - 180

def compass(deg):
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((deg + 22.5) // 45) % 8]

# --- caching ---------------------------------------------------------------

def _cache_key(kind, *parts):
    return os.path.join(CACHE_DIR, kind + "_" + "_".join(str(p) for p in parts) + ".json")

def cache_get(kind, *parts):
    path = _cache_key(kind, *parts)
    try:
        st = os.stat(path)
        if time.time() - st.st_mtime < CACHE_TTL_S:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    return None

def cache_put(kind, parts, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(_cache_key(kind, *parts), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass

# --- data sources ----------------------------------------------------------

def http_json(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_open_meteo(points):
    """One multi-coordinate request for all grid points (quota-friendly)."""
    lats = ",".join(f"{lat:.4f}" for lat, _ in points)
    lons = ",".join(f"{lon:.4f}" for _, lon in points)
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={lats}&longitude={lons}"
           "&hourly=weather_code,precipitation_probability,cape,"
           "wind_speed_10m,wind_direction_10m"
           "&forecast_hours=12&timezone=Asia%2FKuala_Lumpur")
    return http_json(url)

def fetch_warnings():
    cached = cache_get("warnings")
    if cached is not None:
        return cached
    data = http_json("https://api.data.gov.my/weather/warning?limit=10")
    cache_put("warnings", (), data)
    return data

# --- deterministic scoring (v2 formula, unchanged in spirit) ----------------

def score_hour(weather_code, precip_prob, cape):
    """0-100 deterministic risk score for one hour at one point."""
    s = 0.0
    if weather_code in (95, 96, 99):
        s += 50 if weather_code == 95 else 60  # 96/99 = thunder w/ hail
    s += min(precip_prob or 0, 100) * 0.30
    cape = cape or 0
    if cape >= 2000:
        s += 20
    elif cape >= 1000:
        s += 14
    elif cape >= 500:
        s += 8
    elif cape >= 250:
        s += 4
    return min(s, 100.0)

def risk_level(score):
    if score >= 75:
        return "Severe"
    if score >= RISK_THRESHOLD:
        return "High"
    if score >= 25:
        return "Moderate"
    return "Low"

# --- pipeline --------------------------------------------------------------

def assess(lat, lon):
    key = (round(lat, 2), round(lon, 2))
    cached = cache_get("assess", *key)
    if cached is not None:
        cached["cached"] = True
        return cached

    points = [(lat, lon)]
    for radius in RING_RADII_KM:
        for b in RING_BEARINGS:
            points.append(offset_point(lat, lon, b, radius))

    om = fetch_open_meteo(points)
    series = om if isinstance(om, list) else [om]

    grid = []
    for i, (plat, plon) in enumerate(points):
        s = series[i] if i < len(series) else {}
        h = s.get("hourly", {})
        hours = []
        n = len(h.get("time", []))
        for j in range(n):
            sc = score_hour(
                (h.get("weather_code") or [None] * n)[j],
                (h.get("precipitation_probability") or [None] * n)[j],
                (h.get("cape") or [None] * n)[j],
            )
            hours.append({
                "time": h["time"][j],
                "score": round(sc, 1),
                "weather_code": (h.get("weather_code") or [None] * n)[j],
                "precip_prob": (h.get("precipitation_probability") or [None] * n)[j],
                "cape": (h.get("cape") or [None] * n)[j],
                "wind_speed": (h.get("wind_speed_10m") or [None] * n)[j],
                "wind_dir": (h.get("wind_direction_10m") or [None] * n)[j],
            })
        peak = max(hours, key=lambda x: x["score"]) if hours else None
        grid.append({
            "lat": plat, "lon": plon,
            "dist_km": round(haversine_km(lat, lon, plat, plon), 1),
            "bearing_deg": round(bearing_deg(lat, lon, plat, plon), 1),
            "peak_score": peak["score"] if peak else 0,
            "peak_hour": peak,
            "hours": hours,
        })

    elevated = [g for g in grid if g["peak_score"] >= RISK_THRESHOLD]
    elevated.sort(key=lambda g: (g["dist_km"], -g["peak_score"]))
    nearest = elevated[0] if elevated else None

    # Wind-vector trend estimate (v2 Feature 3): at the nearest elevated point,
    # does the wind blow roughly toward the user?
    trend = "unknown"
    if nearest and nearest["peak_hour"]:
        wdir = nearest["peak_hour"].get("wind_dir")
        wspd = nearest["peak_hour"].get("wind_speed")
        if wdir is not None:
            bearing_to_user = bearing_deg(nearest["lat"], nearest["lon"], lat, lon)
            delta = abs(((wdir - bearing_to_user) + 540) % 360 - 180)
            if delta < 45 and (wspd or 0) >= 5:
                trend = "approaching"
            elif delta > 135:
                trend = "receding"
            else:
                trend = "lateral"

    # data.gov.my official warnings cross-check
    warnings_active, warnings_matched = [], []
    try:
        for w in fetch_warnings():
            now = datetime.now(timezone.utc)
            vf_raw, vt_raw = w.get("valid_from"), w.get("valid_to")
            if not (vf_raw and vt_raw):
                warnings_active.append(w)  # undated warning: treat as active
                continue
            vf = datetime.fromisoformat(vf_raw).astimezone(timezone.utc)
            vt = datetime.fromisoformat(vt_raw).astimezone(timezone.utc)
            if vf <= now <= vt:
                warnings_active.append(w)
    except Exception as e:  # warnings layer must never break the core
        print(f"[warn] data.gov.my cross-check failed: {e}", file=sys.stderr)

    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "user": {"lat": lat, "lon": lon},
        "grid_points": len(grid),
        "nearest_elevated": None if nearest is None else {
            "lat": nearest["lat"], "lon": nearest["lon"],
            "dist_km": nearest["dist_km"],
            "direction": compass(nearest["bearing_deg"]),
            "bearing_deg": nearest["bearing_deg"],
            "peak_score": nearest["peak_score"],
            "level": risk_level(nearest["peak_score"]),
            "peak_hour": nearest["peak_hour"],
        },
        "risk_level_at_user": risk_level(grid[0]["peak_score"]),
        "score_at_user": grid[0]["peak_score"],
        "trend_estimate": trend,
        "official_warnings_active": len(warnings_active),
        "official_warnings": [
            {"title_en": w.get("warning_issue", {}).get("title_en"),
             "valid_to": w.get("valid_to")}
            for w in warnings_active
        ],
        "cached": False,
        "_grid": grid,
    }
    cache_put("assess", key, {k: v for k, v in result.items() if k != "cached"})
    return result

def human_summary(r):
    lines = ["Thunderstorm Risk Advisory",
             f"Generated: {r['generated']} ({r['grid_points']}-point grid)"]
    if r["nearest_elevated"]:
        n = r["nearest_elevated"]
        lines.append(
            f"Elevated thunderstorm indicators detected ~{n['dist_km']:.0f} km "
            f"{n['direction']} of your location.")
        lines.append(f"Risk Level: {n['level']} (score {n['peak_score']:.0f}/100, "
                     f"peak hour {n['peak_hour']['time']})")
        if r["trend_estimate"] == "approaching":
            lines.append("Prevailing winds suggest possible movement toward your area "
                         "over the next 1-2 hours.")
        elif r["trend_estimate"] == "receding":
            lines.append("Prevailing winds suggest the activity is moving away.")
        else:
            lines.append("Wind direction does not clearly indicate movement toward you.")
    else:
        lines.append("No elevated thunderstorm indicators within ~30 km "
                     f"(user-point score {r['score_at_user']:.0f}/100, "
                     f"{r['risk_level_at_user']}).")
    if r["official_warnings_active"]:
        lines.append(f"Official MetMalaysia warnings active: {r['official_warnings_active']}")
        for w in r["official_warnings"][:3]:
            lines.append(f"  - {w['title_en']} (valid to {w['valid_to']})")
    else:
        lines.append("No active official MetMalaysia warnings matched.")
    return "\n".join(lines)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print("usage: python risk.py <lat> <lon> [--json]", file=sys.stderr)
        sys.exit(2)
    lat, lon = float(args[0]), float(args[1])
    result = assess(lat, lon)
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(human_summary(result))
        print("\n--- raw (nearest elevated) ---")
        print(json.dumps(result["nearest_elevated"], indent=2))

"""ThunderWatch MY — alert subscription store (threshold re-poll feature).

Subscriptions persist to data/subscriptions.json so they survive restarts.
Each subscription is a small state machine:

    armed --(score >= threshold)--> fires alert --> cooling
    cooling --(score < REARM_SCORE)--> armed (sends all-clear)

This prevents alert spam while a storm sits over the user, and re-arms
automatically once conditions improve.
"""
import json
import os
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DATA_FILE = os.path.join(DATA_DIR, "subscriptions.json")

DEFAULT_THRESHOLD = 50   # "High" level
# Demo override: POLL_SECONDS=30 to show an alert firing within ~30 s
POLL_INTERVAL_S = int(os.environ.get("POLL_SECONDS", "600"))
REARM_SCORE = 30         # drop below this to re-arm after an alert


def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save(subs):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, indent=2)


def find(subs, chat_id):
    for s in subs:
        if s["chat_id"] == chat_id:
            return s
    return None


def add(chat_id, lat, lon, threshold=DEFAULT_THRESHOLD):
    subs = load()
    existing = find(subs, chat_id)
    if existing:
        existing.update({"lat": lat, "lon": lon, "threshold": threshold,
                         "state": "armed", "added": time.time()})
    else:
        subs.append({"chat_id": chat_id, "lat": lat, "lon": lon,
                     "threshold": threshold, "state": "armed",
                     "last_alert": None, "added": time.time()})
    save(subs)
    return subs


def remove(chat_id):
    subs = load()
    kept = [s for s in subs if s["chat_id"] != chat_id]
    save(kept)
    return len(kept) < len(subs)

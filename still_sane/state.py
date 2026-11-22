import json
import os

BOSSES = (
    "Count Geonor",
    "Jamanra, the Abomination",
    "Balbala, the Traitor",
    "The King in the Mists",
    "Olroth, Origin of the Fall",
    "Xesht, We Who Are One",
    "Arbiter of Ash",
)

PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "still-sane", "state.json")


def load():
    data = {"league": "", "kills": {}}
    try:
        with open(PATH, "r", encoding="utf-8") as handle:
            saved = json.load(handle)
    except (OSError, json.JSONDecodeError):
        saved = {}
    if isinstance(saved, dict):
        data["league"] = str(saved.get("league") or "")
        kills = saved.get("kills") or {}
        if isinstance(kills, dict):
            data["kills"] = {name: int(kills.get(name) or 0) for name in BOSSES}
    for name in BOSSES:
        data["kills"].setdefault(name, 0)
    return data


def save(data):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as handle:
        json.dump(
            {"league": data.get("league") or "", "kills": data.get("kills") or {}},
            handle,
            indent=2,
        )

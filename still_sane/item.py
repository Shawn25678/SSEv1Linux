import re

RARITY_CLASS = {
    "normal": "rarity-normal",
    "magic": "rarity-magic",
    "rare": "rarity-rare",
    "unique": "rarity-unique",
    "gem": "rarity-gem",
    "currency": "rarity-currency",
}

PROPERTIES = (
    "Quality",
    "Item Level",
    "Level",
    "Sockets",
    "Rune Sockets",
    "Physical Damage",
    "Fire Damage",
    "Cold Damage",
    "Lightning Damage",
    "Chaos Damage",
    "Elemental Damage",
    "Critical Hit Chance",
    "Attacks per Second",
    "Reload Time",
    "Armour",
    "Evasion Rating",
    "Energy Shield",
    "Ward",
    "Spirit",
    "Block chance",
)

FLAGS = ("corrupted", "mirrored", "unidentified", "fractured", "desecrated")


def rarity_class(rarity):
    return RARITY_CLASS.get((rarity or "").lower(), "rarity-normal")


def _property(line):
    for label in PROPERTIES:
        prefix = label.lower() + ":"
        if line.lower().startswith(prefix):
            return label, line.split(":", 1)[1].strip()
    return None


def _range(value):
    match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", value.replace(",", ""))
    if not match:
        return None
    lo = float(match.group(1))
    hi = float(match.group(2))
    return (lo + hi) / 2


def _number(value):
    match = re.search(r"(\d+(?:\.\d+)?)", value.replace(",", ""))
    if not match:
        return None
    return float(match.group(1))


def weapon_dps(props):
    aps = _number(props.get("Attacks per Second", ""))
    if not aps:
        return {}
    shown = {}
    physical = _range(props.get("Physical Damage", ""))
    if physical is not None:
        shown["Physical"] = round(physical * aps, 2)
    elemental = 0.0
    found = False
    for label in ("Fire Damage", "Cold Damage", "Lightning Damage", "Chaos Damage"):
        average = _range(props.get(label, ""))
        if average is None:
            continue
        found = True
        elemental += average
        shown[label.replace(" Damage", "")] = round(average * aps, 2)
    if not found:
        average = _range(props.get("Elemental Damage", ""))
        if average is not None:
            elemental = average
            shown["Elemental"] = round(average * aps, 2)
    if physical is not None or elemental:
        shown["Total"] = round(((physical or 0) + elemental) * aps, 2)
    return shown


def mod_class(line):
    low = line.lower()
    if any(word in low for word in ("fire", "burning", "ignite")):
        return "mod-fire"
    if any(word in low for word in ("cold", "freeze", "frost")):
        return "mod-cold"
    if "lightning" in low or "shock" in low:
        return "mod-lightning"
    if "chaos" in low or "poison" in low:
        return "mod-chaos"
    if "life" in low:
        return "mod-life"
    if "mana" in low:
        return "mod-mana"
    if "energy shield" in low:
        return "mod-es"
    if "armour" in low or "armor" in low:
        return "mod-armour"
    if "evasion" in low:
        return "mod-evasion"
    return "mod-plain"


def read_item(text):
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in raw.split("\n")]
    lines = [line for line in lines if line and not set(line) <= {"-"}]
    rarity = ""
    if lines and lines[0].lower().startswith("rarity:"):
        rarity = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]
    name = lines[0] if lines else ""
    lines = lines[1:]
    base = ""
    if lines and _property(lines[0]) is None and lines[0].lower() not in FLAGS and not lines[0].lower().startswith("requires"):
        if rarity.lower() in ("rare", "unique", "magic", "gem"):
            base = lines[0]
            lines = lines[1:]
    props = {}
    mods = []
    flags = []
    requires = []
    for line in lines:
        low = line.lower()
        if low in FLAGS or low.rstrip("!") in FLAGS:
            flags.append(line)
            continue
        if low.startswith("requires"):
            requires.append(line)
            continue
        found = _property(line)
        if found:
            props[found[0]] = found[1]
            continue
        mods.append(line)
    return {
        "name": name,
        "base": base,
        "rarity": rarity,
        "props": props,
        "mods": mods,
        "flags": flags,
        "requires": requires,
        "dps": weapon_dps(props),
        "text": raw,
    }

import json
import urllib.parse
import urllib.request

UA = "StillSaneLinux/0.1"


def _request(url, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def trade_search(league, item):
    query = {
        "query": {
            "status": {"option": "securable"},
            "stats": [{"type": "and", "filters": []}],
        },
        "sort": {"price": "asc"},
    }
    rarity = (item.get("rarity") or "").lower()
    name = item.get("name") or ""
    base = item.get("base") or ""
    if rarity in ("unique", "currency", "gem") and name:
        query["query"]["name"] = name
    if base:
        query["query"]["type"] = base
    elif rarity not in ("unique", "currency", "gem") and name:
        query["query"]["type"] = name
    league_path = urllib.parse.quote(league)
    found = _request(
        f"https://www.pathofexile.com/api/trade2/search/{league_path}",
        query,
    )
    ids = found.get("result") or []
    total = found.get("total", len(ids))
    if not ids:
        return {"total": total, "listings": []}
    fetch_ids = ",".join(ids[:10])
    fetched = _request(
        "https://www.pathofexile.com/api/trade2/fetch/"
        f"{fetch_ids}?query={urllib.parse.quote(found.get('id', ''))}"
    )
    listings = []
    for row in fetched.get("result") or []:
        listing = row.get("listing") or {}
        price = listing.get("price") or {}
        account = (listing.get("account") or {}).get("name") or ""
        listings.append(
            {
                "amount": price.get("amount"),
                "currency": price.get("currency") or "",
                "account": account,
            }
        )
    return {"total": total, "listings": listings}


def ninja_currency(league):
    league_path = urllib.parse.quote(league)
    url = (
        "https://poe.ninja/poe2/api/economy/exchange/current/overview"
        f"?league={league_path}&type=Currency"
    )
    payload = _request(url)
    rows = []
    for line in payload.get("lines") or []:
        name = line.get("name") or line.get("currencyTypeName") or ""
        divine = line.get("primaryValue")
        if divine is None:
            divine = line.get("divineValue")
        if name:
            rows.append({"name": name, "divine": divine})
    rows.sort(key=lambda row: -(row["divine"] or 0))
    return rows

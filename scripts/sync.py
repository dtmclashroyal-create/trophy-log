#!/usr/bin/env python3
"""Fetch the latest Clash Royale battles and merge them into data/battles.json.

Env: CR_API_KEY (API key whose allowed IP is 45.79.218.79, the RoyaleAPI proxy)
     CR_TAG     (player tag, e.g. 222PVQCR8)
Usage: python scripts/sync.py            # fetch from the API
       python scripts/sync.py --from DIR # seed from DIR/profile.json + DIR/battlelog.json
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://proxy.royaleapi.dev/v1/players/"
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "battles.json")


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Authorization": "Bearer " + os.environ["CR_API_KEY"], "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ts(bt):  # 20261125T092145.000Z -> epoch ms
    return int(datetime.strptime(bt[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).timestamp() * 1000)


def battle(b):
    me, op = b["team"][0], b["opponent"][0]
    c, oc = me.get("crowns", 0), op.get("crowns", 0)
    return {"id": b["battleTime"][:15], "t": ts(b["battleTime"]), "type": b.get("type", ""),
            "mode": (b.get("gameMode") or {}).get("name", ""),
            "start": me.get("startingTrophies"), "change": me.get("trophyChange"),
            "crowns": c, "oppCrowns": oc,
            "result": "win" if c > oc else "loss" if c < oc else "draw",
            "deck": sorted(x["name"] for x in me.get("cards", [])),
            "evo": sorted(x["name"] for x in me.get("cards", []) if x.get("evolutionLevel")),
            "opp": op.get("name", "")}


def card_icons(log, cards):
    """Collect name -> {icon, evo} image URLs (Supercell CDN) from every card seen in the log."""
    for b in log:
        for side in (b.get("team", []) + b.get("opponent", [])):
            for c in side.get("cards", []):
                urls = c.get("iconUrls") or {}
                entry = {k: v for k, v in (("icon", urls.get("medium")), ("evo", urls.get("evolutionMedium"))) if v}
                if entry and cards.get(c["name"]) != {**cards.get(c["name"], {}), **entry}:
                    cards[c["name"]] = {**cards.get(c["name"], {}), **entry}
    return cards


def profile(p):
    cur = p.get("currentPathOfLegendSeasonResult") or {}
    return {"name": p.get("name"), "tag": p.get("tag"), "trophies": p.get("trophies"),
            "bestTrophies": p.get("bestTrophies"), "ranked": cur.get("trophies"),
            "league": cur.get("leagueNumber"), "rank": cur.get("rank"),
            "lastSeason": p.get("lastPathOfLegendSeasonResult"),
            "bestSeason": p.get("bestPathOfLegendSeasonResult"),
            "wins": p.get("wins"), "losses": p.get("losses")}


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--from":
        d = sys.argv[2]
        prof, log = json.load(open(f"{d}/profile.json")), json.load(open(f"{d}/battlelog.json"))
    else:
        tag = urllib.parse.quote("#" + os.environ["CR_TAG"].lstrip("#"))
        prof, log = api(tag), api(tag + "/battlelog")

    try:
        data = json.load(open(DATA))
    except FileNotFoundError:
        data = {"profile": None, "battles": []}

    have = {b["id"]: b for b in data["battles"]}
    new, backfilled = [], False
    for raw in log:
        b = battle(raw)
        old = have.get(b["id"])
        if old is None:
            new.append(b)
        elif "evo" not in old:  # battles saved before evolution info existed
            old["evo"] = b["evo"]; backfilled = True
    before = json.dumps(data.get("cards", {}), sort_keys=True)
    data["cards"] = card_icons(log, dict(data.get("cards", {})))
    p = profile(prof)
    changed = (bool(new) or backfilled or json.dumps(data["cards"], sort_keys=True) != before
               or p != {k: v for k, v in (data["profile"] or {}).items() if k != "updatedAt"})
    if not changed:
        print("no changes")
        return
    p["updatedAt"] = int(datetime.now(timezone.utc).timestamp() * 1000)
    data["profile"] = p
    data["battles"] = sorted(data["battles"] + new, key=lambda b: b["t"])
    with open(DATA, "w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"saved {len(new)} new battles; ranked {p['ranked']}, trophies {p['trophies']}")


if __name__ == "__main__":
    main()

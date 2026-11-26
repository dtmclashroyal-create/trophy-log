# 트로피 기록장 — notes for Claude

A phone web app (PWA) that tracks one Clash Royale player's ranked (Path of Legends) score and trophies.
The owner is a Korean speaker and not a developer: reply in Korean, plain words, step by step for anything they must click.

## How it works
- `.github/workflows/sync.yml` runs `scripts/sync.py` and commits `data/battles.json` only when it changed. It is triggered every 5 minutes by an external cron-job.org job calling the `workflow_dispatch` API (POST /repos/dtmclashroyal-create/trophy-log/actions/workflows/sync.yml/dispatches, body {"ref":"main"}) with a fine-grained token (Actions: write, this repo only) the owner keeps at cron-job.org. GitHub's own `schedule` (every 30 min) is only a backup because it is often late. If syncs stop, the token may have expired.
- `scripts/sync.py` (stdlib only) calls the official API **through the RoyaleAPI proxy** `https://proxy.royaleapi.dev/v1/players/...`. The key in secret `CR_API_KEY` is whitelisted for the proxy IP `45.79.218.79`; GitHub runner IPs change, so never call `api.clashroyale.com` directly. Tag comes from repo variable `CR_TAG` (default `222PVQCR8`).
- The battle log API returns only the latest ~25–30 battles; sync merges by `id` (battleTime `YYYYMMDDTHHMMSS`), so `data/battles.json` keeps the full history.
- GitHub Pages serves the repo root (`main`, `/`): https://dtmclashroyal-create.github.io/trophy-log/
- `index.html` is the whole app (vanilla JS, no build step). `sw.js` caches it for offline: HTML/JS/all same-origin JSON are network-first, images/fonts cache-first. Bump `CACHE` in `sw.js` when changing cached assets.

## data/battles.json
```
{ "profile": {name, tag, trophies, bestTrophies, ranked, league, rank, lastSeason, bestSeason, wins, losses, updatedAt},
  "cards":   { "<card name>": {"icon": url, "evo": url, "hero": url} },      // Supercell CDN images from the API
  "battles": [ {id, t(ms), type, mode, start, change, crowns, oppCrowns, result, deck[8 names, sorted], evo[names], hero[names], opp, oppDeck[8 names or [] for 2v2]} ] }
```
- Ranked score = `start + change` for `type == "pathOfLegend"`; trophy road is `type == "PvP"`.
- Gotcha: when the player is unranked this season, the API repeats last season's final rank in `currentPathOfLegendSeasonResult.rank`; the app shows "언랭" when it equals `lastSeason.rank`.

## Rules
- Never put the API key or any token in the repo or the page (the site is public).
- Values from the API are text: escape before putting them in HTML (`esc()` in index.html).
- Test the page at phone width (~390px) before pushing; check no horizontal scroll.
- Test sync locally with `python scripts/sync.py --from DIR` (DIR has profile.json + battlelog.json) so nothing hits the network.
- Card slots: API `evolutionLevel` 1 = evolution, 2 = hero (images `evolutionMedium` / `heroMedium`). The deck view orders evolution → hero → the rest.
- Matchup analysis ("상대 윈컨별 승률"): only win-condition cards from `WINCONS` in index.html are compared (owner's request). Estimate = (wins + 5·p0)/(games + 5), p0 = overall win rate; rows under 5 games are faded. Only decks the owner adds ("+ 덱 추가", saved in localStorage `trophy-log-pinned` on that phone) appear as chips (exact 8-card match, labelled by the deck's win condition, duplicates numbered in first-played order); picking one shows matchups for that deck only, and p0 is then that deck's win rate. Tapping a deck in "덱별 성적" adds and selects it. Add new win-condition cards to `WINCONS` (English API name, Korean label), most defining first.
- Card names shown to the owner are the official Korean names from `data/cards_ko.json` (generated from RoyaleAPI cr-api-data `cards_i18n.json`, field `_lang.name.kr`; fetch it from raw.githubusercontent.com). Cards newer than that file fall back to the Korean label in `WINCONS` or the English name — ask the owner for the in-game name and add it to `data/cards_ko.json`.

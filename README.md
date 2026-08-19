# Premier League Dream Team

Picks a 15-player Premier League squad for **2026-27** from five seasons of
player data (2021-22 → 2025-26), corrected for the things that make historical
totals misleading: **current injuries, ageing, and club moves**.

**➡️ [The squad and the full analysis](reports/dream_team.md)**
· [Injury and retirement review](reports/news_review.md)

## The answer

3-5-2, £100.0m of £100.0m, 1,657 projected points from the XI.

| | | |
| --- | --- | --- |
| **GK** | Raya (ARS) | |
| **DEF** | Gabriel (ARS) · Guéhi (MCI) · Mitchell (CRY) | |
| **MID** | Mbeumo (MUN) · Rice (ARS) · Szoboszlai (LIV) · Foden (MCI) · Mac Allister (LIV) | |
| **FWD** | Haaland (MCI, captain) · Watkins (AVL) | |
| **Bench** | Mykolenko (EVE) · Dúbravka (TOT) · O'Shea (IPS) · Walle Egeli (IPS) | |

The headline exclusion is **Virgil van Dijk** — 7th-highest five-season total of
any registered player, fully fit, and still not selected, because he is 35 and
in the last year of his contract.

## Data

| Source | Use |
| --- | --- |
| [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) | Per-gameweek and per-season history, 2021-22 → 2025-26 (190 gameweeks, 4,025 player-seasons, 1,797 players) |
| [Fantasy Premier League API](https://fantasy.premierleague.com/api/bootstrap-static/) | Live 2026-27 squads, prices, and injury status for 595 players |
| Press injury trackers | Cross-check on the API's status flags — see [`news_review.md`](reports/news_review.md) |

## Method in one paragraph

Each player's per-90 scoring rate is weighted toward recent seasons, shrunk
toward a positional baseline when the sample is thin, and further blended toward
an empirically measured *newcomer* baseline when the track record is short. That
rate is multiplied by an age curve (outfielders plateau 24-28 and fall away past
32; keepers peak later), by a club-context index rebuilt from the last two
seasons of match results, and by expected minutes — which are themselves cut by
the player's live availability. A linear program then picks the best legal 15
under FPL's rules: 2/5/5/3 by position, at most 3 per club, £100.0m budget.

Backtested by rebuilding the projection from 2021-22 → 2024-25 and scoring it
against actual 2025-26 results: **r = 0.582 vs 0.469** for a naive multi-season
average, and the top 15 picks averaged **143.6** actual points against 137.2 for
the naive ranking (sample average 54.0).

## Running it

```bash
pip install -r requirements.txt
python src/build_dataset.py    # download + aggregate 5 seasons
python src/team_strength.py    # club attack/defence indices
python src/score_players.py    # projections
python src/pick_squad.py       # optimise the 15
python src/flag_risks.py       # age and fitness flags
cd src && python backtest.py   # validation
```

## Layout

```
src/
  build_dataset.py   download 5 seasons + live API -> data/processed/
  team_strength.py   club attack/defence indices from match results
  score_players.py   recency, shrinkage, age curves, fitness -> projections
  pick_squad.py      integer program for the best legal 15
  flag_risks.py      who the raw totals overrate, and why
  backtest.py        replay the method on 2025-26 and score it
reports/
  dream_team.md      the squad, the reasoning, the backtest
  news_review.md     injuries, bans, retirements and ageing as at 19 Aug 2026
data/raw/            downloaded source data
data/processed/      aggregated tables and outputs
```

## Limitations

* 121 of the 595 registered players have no Premier League minutes in the window
  and are scored on a conservative newcomer baseline. An elite signing from
  abroad will be underrated.
* The 2026 World Cup was played this summer; early-season rotation for
  tournament players is not modelled.
* Fixture difficulty is not modelled — it matters week to week but largely
  washes out over 38 games.
* The injury layer is a snapshot of 19 August 2026 and goes stale quickly.
  Re-run `build_dataset.py` and `score_players.py` to refresh it.

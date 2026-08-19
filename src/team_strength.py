"""Derive 2026-27 team attack/defence strength from recent match results.

The FPL API's own strength ratings are all zero before a season starts, so we
rebuild them from the last two seasons of gameweek data. Newly promoted clubs
with no recent Premier League record fall back to a promoted-side baseline.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

SEASON_WEIGHTS = {"2024-25": 0.35, "2025-26": 0.65}
# Promoted sides historically concede ~1.9 and score ~1.0 per game.
PROMOTED_DEFAULT = {"goals_for_pg": 1.05, "goals_against_pg": 1.85}

# The gameweek files and the current API do not always spell clubs the same way.
TEAM_ALIASES = {"Ipswich Town": "Ipswich"}


def team_match_records() -> pd.DataFrame:
    frames = []
    for season, weight in SEASON_WEIGHTS.items():
        gw = pd.read_csv(RAW / season / "merged_gw.csv",
                         usecols=["team", "fixture", "was_home",
                                  "team_h_score", "team_a_score", "GW"])
        gw = gw.dropna(subset=["team_h_score", "team_a_score"])
        # One row per team per fixture.
        matches = gw.drop_duplicates(subset=["team", "fixture"]).copy()
        matches["goals_for"] = matches.apply(
            lambda r: r["team_h_score"] if r["was_home"] else r["team_a_score"], axis=1)
        matches["goals_against"] = matches.apply(
            lambda r: r["team_a_score"] if r["was_home"] else r["team_h_score"], axis=1)
        rec = matches.groupby("team").agg(
            games=("fixture", "count"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
            clean_sheets=("goals_against", lambda s: (s == 0).sum()),
        ).reset_index()
        rec["season"] = season
        rec["weight"] = weight
        frames.append(rec)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    rec = team_match_records()
    rec["w_games"] = rec["weight"] * rec["games"]
    agg = rec.groupby("team").apply(lambda g: pd.Series({
        "goals_for_pg": (g["goals_for"] * g["weight"]).sum() / g["w_games"].sum(),
        "goals_against_pg": (g["goals_against"] * g["weight"]).sum() / g["w_games"].sum(),
        "clean_sheet_rate": (g["clean_sheets"] * g["weight"]).sum() / g["w_games"].sum(),
        "seasons_of_data": g["season"].nunique(),
    }), include_groups=False).reset_index()

    boot = json.loads((RAW / "bootstrap_2026-27.json").read_text())
    current_teams = [t["name"] for t in boot["teams"]]

    rows = []
    for name in current_teams:
        match = agg[agg["team"] == TEAM_ALIASES.get(name, name)]
        if len(match):
            r = match.iloc[0].to_dict()
            r["promoted"] = False
        else:
            r = {"team": name, **PROMOTED_DEFAULT,
                 "clean_sheet_rate": 0.15, "seasons_of_data": 0, "promoted": True}
        rows.append(r)
    teams = pd.DataFrame(rows)

    # Convert to multipliers centred on the 20-team mean.
    teams["attack_index"] = teams["goals_for_pg"] / teams["goals_for_pg"].mean()
    teams["defence_index"] = teams["goals_against_pg"].mean() / teams["goals_against_pg"]

    teams.to_csv(PROC / "team_strength.csv", index=False)
    print(teams.sort_values("defence_index", ascending=False)
          .round(3).to_string(index=False))


if __name__ == "__main__":
    main()

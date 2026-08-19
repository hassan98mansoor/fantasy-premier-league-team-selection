"""Build a 5-season Premier League / FPL player dataset.

Sources
-------
* vaastav/Fantasy-Premier-League  -- historical per-gameweek and per-season data
* fantasy.premierleague.com API   -- live 2026-27 squad list, prices, availability

Output: data/processed/player_seasons.csv  (one row per player-season)
        data/processed/current_players.csv (2026-27 registered players)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

HISTORY_SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
CURRENT_SEASON = "2026-27"

POSITION_BY_TYPE = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}

# Per-gameweek columns we sum over a season. Some only exist in later seasons.
SUM_COLS = [
    "minutes", "total_points", "goals_scored", "assists", "clean_sheets",
    "goals_conceded", "saves", "bonus", "bps", "yellow_cards", "red_cards",
    "own_goals", "penalties_missed", "penalties_saved", "starts",
    "expected_goals", "expected_assists", "expected_goal_involvements",
    "expected_goals_conceded", "defensive_contribution",
]
MEAN_COLS = ["influence", "creativity", "threat", "ict_index"]


def load_season(season: str) -> pd.DataFrame:
    """Aggregate one season of gameweek rows into one row per player."""
    gw = pd.read_csv(RAW / season / "merged_gw.csv")
    raw = pd.read_csv(RAW / season / "players_raw.csv")

    # `element` is a season-local id; `code` is FPL's stable cross-season player id.
    id_map = raw.set_index("id")
    gw["code"] = gw["element"].map(id_map["code"])
    gw["element_type"] = gw["element"].map(id_map["element_type"])

    unmapped = gw["code"].isna().sum()
    if unmapped:
        print(f"  {season}: dropping {unmapped} gw rows with no player code")
        gw = gw.dropna(subset=["code"])
    gw["code"] = gw["code"].astype(int)

    present_sum = [c for c in SUM_COLS if c in gw.columns]
    present_mean = [c for c in MEAN_COLS if c in gw.columns]
    for c in present_sum + present_mean:
        gw[c] = pd.to_numeric(gw[c], errors="coerce").fillna(0.0)

    agg = {c: "sum" for c in present_sum}
    agg.update({c: "sum" for c in present_mean})  # ICT components are per-match, sum them
    agg["GW"] = "count"

    out = gw.groupby("code").agg(agg).rename(columns={"GW": "appearances_listed"})

    # Games actually played (any minutes) and games started.
    played = gw[gw["minutes"] > 0].groupby("code").size().rename("games_played")
    out = out.join(played).fillna({"games_played": 0})

    # Identity / metadata from players_raw.
    meta_cols = ["code", "first_name", "second_name", "web_name", "element_type", "team_code"]
    if "birth_date" in raw.columns:
        meta_cols.append("birth_date")
    meta = raw[meta_cols].drop_duplicates("code").set_index("code")
    out = out.join(meta, how="left")

    # Team name as shown in the gameweek file (handles mid-season club changes: take the last).
    last_team = gw.sort_values("GW").groupby("code")["team"].last().rename("team_name")
    out = out.join(last_team)

    out["season"] = season
    out["position"] = out["element_type"].map(POSITION_BY_TYPE)
    for c in SUM_COLS + MEAN_COLS:
        if c not in out.columns:
            out[c] = pd.NA
    return out.reset_index()


def load_current() -> pd.DataFrame:
    """2026-27 registered players: prices, positions, clubs, availability flags."""
    boot = json.loads((RAW / "bootstrap_2026-27.json").read_text())
    teams = {t["id"]: t for t in boot["teams"]}
    rows = []
    for e in boot["elements"]:
        team = teams[e["team"]]
        rows.append({
            "code": e["code"],
            "fpl_id": e["id"],
            "web_name": e["web_name"],
            "full_name": f"{e['first_name']} {e['second_name']}".strip(),
            "position": POSITION_BY_TYPE[e["element_type"]],
            "team_name": team["name"],
            "team_short": team["short_name"],
            "now_cost_m": e["now_cost"] / 10.0,
            "status": e["status"],
            "news": (e.get("news") or "").strip(),
            "chance_next": e.get("chance_of_playing_next_round"),
            "chance_this": e.get("chance_of_playing_this_round"),
            "birth_date": e.get("birth_date"),
            "selected_by_percent": float(e.get("selected_by_percent") or 0),
            "penalties_order": e.get("penalties_order"),
            "team_strength_attack_home": team.get("strength_attack_home"),
            "team_strength_attack_away": team.get("strength_attack_away"),
            "team_strength_defence_home": team.get("strength_defence_home"),
            "team_strength_defence_away": team.get("strength_defence_away"),
        })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    frames = []
    for season in HISTORY_SEASONS:
        print(f"aggregating {season} ...")
        frames.append(load_season(season))
    hist = pd.concat(frames, ignore_index=True)

    current = load_current()
    hist.to_csv(OUT / "player_seasons.csv", index=False)
    current.to_csv(OUT / "current_players.csv", index=False)

    print(f"\nplayer_seasons.csv: {len(hist)} player-season rows, "
          f"{hist['code'].nunique()} distinct players")
    print(f"current_players.csv: {len(current)} players registered for {CURRENT_SEASON}")
    overlap = set(current["code"]) & set(hist["code"])
    print(f"{len(overlap)} of them have Premier League history in the last 5 seasons")


if __name__ == "__main__":
    main()

"""Pick the best legal 15-player squad from the projections.

Fantasy Premier League squad rules, which define what "a team of 15" means:
  * exactly 2 GKP, 5 DEF, 5 MID, 3 FWD
  * at most 3 players from any one club
  * total price at most GBP 100.0m
  * the starting XI is 1 GKP, 3-5 DEF, 2-5 MID, 1-3 FWD

The objective maximises the starting XI's projected points plus a small share
of the bench, so the solver spends real money on starters and buys cheap,
playing cover for the bench rather than expensive players who would sit.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pulp

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

SQUAD_QUOTA = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
XI_MIN = {"GKP": 1, "DEF": 3, "MID": 2, "FWD": 1}
XI_MAX = {"GKP": 1, "DEF": 5, "MID": 5, "FWD": 3}
BUDGET = 100.0
MAX_PER_CLUB = 3
XI_SIZE = 11
BENCH_WEIGHT = 0.12

# A player with almost no route into the side is noise in an optimiser; drop
# anyone we do not expect to reach roughly four full matches.
MIN_PROJECTED_MINUTES = 360


def solve(players: pd.DataFrame, budget: float = BUDGET,
          max_per_club: int = MAX_PER_CLUB) -> pd.DataFrame:
    prob = pulp.LpProblem("fpl_squad", pulp.LpMaximize)
    idx = list(players.index)

    pick = pulp.LpVariable.dicts("pick", idx, cat="Binary")   # in the 15
    start = pulp.LpVariable.dicts("start", idx, cat="Binary")  # in the XI

    pts = players["projected_points"].to_dict()
    prob += pulp.lpSum(
        pts[i] * (BENCH_WEIGHT * pick[i] + (1 - BENCH_WEIGHT) * start[i]) for i in idx
    )

    for i in idx:
        prob += start[i] <= pick[i]

    prob += pulp.lpSum(pick[i] for i in idx) == sum(SQUAD_QUOTA.values())
    prob += pulp.lpSum(start[i] for i in idx) == XI_SIZE
    prob += pulp.lpSum(players.loc[i, "now_cost_m"] * pick[i] for i in idx) <= budget

    for pos, n in SQUAD_QUOTA.items():
        members = [i for i in idx if players.loc[i, "position"] == pos]
        prob += pulp.lpSum(pick[i] for i in members) == n
        prob += pulp.lpSum(start[i] for i in members) >= XI_MIN[pos]
        prob += pulp.lpSum(start[i] for i in members) <= XI_MAX[pos]

    for club in players["team_name"].unique():
        members = [i for i in idx if players.loc[i, "team_name"] == club]
        prob += pulp.lpSum(pick[i] for i in members) <= max_per_club

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"solver returned {pulp.LpStatus[status]}")

    chosen = [i for i in idx if pick[i].value() > 0.5]
    squad = players.loc[chosen].copy()
    squad["starting_xi"] = [start[i].value() > 0.5 for i in chosen]
    order = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}
    squad["_o"] = squad["position"].map(order)
    return (squad.sort_values(["starting_xi", "_o", "projected_points"],
                              ascending=[False, True, False])
                 .drop(columns="_o"))


def show(squad: pd.DataFrame, title: str) -> str:
    cols = ["web_name", "position", "team_short", "now_cost_m", "age",
            "projected_points", "availability_reason"]
    xi = squad[squad["starting_xi"]]
    bench = squad[~squad["starting_xi"]]
    lines = [f"\n=== {title} ===",
             f"cost GBP {squad['now_cost_m'].sum():.1f}m | "
             f"squad projection {squad['projected_points'].sum():.0f} pts | "
             f"XI projection {xi['projected_points'].sum():.0f} pts",
             "\n-- starting XI --",
             xi[cols].round(1).to_string(index=False),
             "\n-- bench --",
             bench[cols].round(1).to_string(index=False)]
    text = "\n".join(lines)
    print(text)
    return text


def main() -> None:
    df = pd.read_csv(PROC / "player_scores.csv")
    REPORTS.mkdir(exist_ok=True)

    pool = df[df["projected_minutes"] >= MIN_PROJECTED_MINUTES].reset_index(drop=True)
    print(f"{len(pool)} players in the selectable pool "
          f"(of {len(df)} registered for 2026-27)")

    sections = []
    squad = solve(pool)
    sections.append(show(squad, "Dream team: FPL-legal 15 (GBP 100.0m, max 3 per club)"))
    squad.to_csv(PROC / "dream_team_15.csv", index=False)

    # What the same optimiser produces with the money taken away -- the
    # "best 15 regardless of price" view.
    rich = solve(pool, budget=10_000.0)
    sections.append(show(rich, "Unlimited-budget 15 (formation + 3-per-club rules only)"))
    rich.to_csv(PROC / "dream_team_15_no_budget.csv", index=False)

    # What a naive 5-season-totals ranking would have picked, for contrast.
    naive = df.sort_values("total_points", ascending=False).head(15)
    sections.append("\n=== Naive ranking: top 15 by raw 5-season points ===\n" +
                    naive[["web_name", "position", "team_short", "now_cost_m", "age",
                           "total_points", "availability_reason"]]
                    .round(1).to_string(index=False))
    print(sections[-1])

    (REPORTS / "squad_output.txt").write_text("\n".join(sections) + "\n")


if __name__ == "__main__":
    main()

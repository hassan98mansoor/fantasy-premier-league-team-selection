"""Identify players whose five-season record overstates them for 2026-27.

Two groups matter for a dream team:
  * AGE     -- the record was built by a younger player than the one available now
  * FITNESS -- currently injured, suspended or gone, so the record cannot repeat
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

# Age at which we start calling out decline explicitly in the report.
VETERAN_AGE = {"GKP": 33.0, "DEF": 31.0, "MID": 31.0, "FWD": 31.0}


def main() -> None:
    df = pd.read_csv(PROC / "player_scores.csv")
    REPORTS.mkdir(exist_ok=True)

    df["naive_rank"] = df["total_points"].rank(ascending=False, method="min").astype(int)
    df["model_rank"] = df["projected_points"].rank(ascending=False, method="min").astype(int)
    df["rank_drop"] = df["model_rank"] - df["naive_rank"]

    out = []

    # --- Players the raw totals rate highly but the model demotes -----------
    naive_top = df[df["naive_rank"] <= 60].copy()
    demoted = naive_top.nlargest(15, "rank_drop")
    out.append("## Biggest downgrades: strong 5-season record, weaker 2026-27 outlook\n")
    out.append(demoted[["web_name", "position", "team_short", "age", "total_points",
                        "naive_rank", "model_rank", "rank_drop", "age_factor",
                        "availability", "availability_reason"]]
               .round(2).to_string(index=False))

    # --- Veterans -----------------------------------------------------------
    df["veteran_threshold"] = df["position"].map(VETERAN_AGE)
    vets = df[(df["age"] >= df["veteran_threshold"]) & (df["total_points"] >= 250)]
    out.append("\n\n## Ageing risk: high five-season returns, past the positional peak\n")
    out.append(vets.sort_values("total_points", ascending=False)
               .head(20)[["web_name", "position", "team_short", "age", "total_points",
                          "last_season_points", "age_factor", "projected_points",
                          "naive_rank", "model_rank"]]
               .round(2).to_string(index=False))

    # --- Fitness ------------------------------------------------------------
    hurt = df[(df["availability"] < 1.0) & (df["total_points"] >= 150)]
    out.append("\n\n## Fitness risk: players discounted for current injury, ban or exit\n")
    out.append(hurt.sort_values("total_points", ascending=False)
               .head(25)[["web_name", "position", "team_short", "age", "total_points",
                          "availability", "projected_points", "naive_rank", "model_rank",
                          "availability_reason"]]
               .round(2).to_string(index=False))

    # --- Players the model likes more than the raw totals do ----------------
    promoted = df[df["model_rank"] <= 40].nsmallest(12, "rank_drop")
    out.append("\n\n## Biggest upgrades: the model rates them above their raw totals\n")
    out.append(promoted[["web_name", "position", "team_short", "age", "total_points",
                         "last_season_points", "naive_rank", "model_rank", "rank_drop",
                         "team_factor", "projected_points"]]
               .round(2).to_string(index=False))

    text = "\n".join(out) + "\n"
    (REPORTS / "risk_flags.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()

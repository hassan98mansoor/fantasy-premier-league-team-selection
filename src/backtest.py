"""Sanity-check the projection method by replaying it on a season we can score.

We rebuild the projection using only 2021-22 .. 2024-25, then compare it with
what players actually scored in 2025-26. This cannot validate the injury layer
(that depends on live news, which we do not have a snapshot of for August 2025)
so it tests the parts that are purely historical: recency weighting, shrinkage,
track-record confidence and the age curve.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import score_players as sp

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"

TRAIN = ["2021-22", "2022-23", "2023-24", "2024-25"]
TEST = "2025-26"
# Same exponential shape as the live model, renormalised over four seasons.
TRAIN_WEIGHTS = {"2021-22": 0.12, "2022-23": 0.18, "2023-24": 0.27, "2024-25": 0.43}


def project(hist: pd.DataFrame, ages: pd.Series) -> pd.DataFrame:
    original = sp.SEASON_WEIGHTS
    sp.SEASON_WEIGHTS = TRAIN_WEIGHTS
    try:
        agg = sp.weighted_history(hist[hist["season"].isin(TRAIN)]).reset_index()
    finally:
        sp.SEASON_WEIGHTS = original

    meta = hist.drop_duplicates("code").set_index("code")["position"]
    agg["position"] = agg["code"].map(meta)
    priors = sp.newcomer_priors(hist[hist["season"].isin(TRAIN)])
    agg["prior_p90"] = agg["position"].map(priors["prior_p90"])
    agg["prior_share"] = agg["position"].map(priors["prior_minute_share"])

    shrink = agg["w_effective_minutes"] / (agg["w_effective_minutes"] + sp.SHRINK_MINUTES)
    p90 = shrink * agg["w_points_per_90"] + (1 - shrink) * agg["prior_p90"]
    conf = agg["evidence"].clip(lower=0) ** 0.5
    p90 = conf * p90 + (1 - conf) * agg["prior_p90"]

    agg["age"] = agg["code"].map(ages)
    raw_af = np.array([sp.age_factor(a, p) for a, p in zip(agg["age"], agg["position"])])
    af = np.where(raw_af > 1.0, 1.0 + conf * (raw_af - 1.0), raw_af)

    # `last season` inside the backtest window is 2024-25.
    last = (hist[hist["season"] == "2024-25"].set_index("code")["minutes"]
            / sp.SEASON_MINUTES)
    observed_share = 0.65 * agg["w_minute_share"] + 0.35 * agg["code"].map(last).fillna(0)
    share = conf * observed_share + (1 - conf) * agg["prior_share"]

    agg["projected_minutes"] = share * sp.SEASON_MINUTES * (0.5 + 0.5 * af)
    agg["projected_points"] = p90 * af * agg["projected_minutes"] / 90.0
    # The naive alternative: just total up the four training seasons.
    agg["naive_points"] = agg["total_points"] / 4.0
    return agg


def main() -> None:
    hist = pd.read_csv(PROC / "player_seasons.csv")

    ages = {}
    for _, r in hist.dropna(subset=["birth_date"]).drop_duplicates("code").iterrows():
        # Age as at the start of the 2025-26 season.
        try:
            born = pd.Timestamp(r["birth_date"])
        except (ValueError, TypeError):
            continue
        ages[r["code"]] = (pd.Timestamp("2025-08-15") - born).days / 365.25
    ages = pd.Series(ages)

    proj = project(hist, ages)
    actual = (hist[hist["season"] == TEST]
              .groupby("code")["total_points"].sum().rename("actual_points"))

    # Only players who were in the league for both windows can be scored.
    df = proj.merge(actual, on="code", how="inner")
    df = df[df["total_minutes"] > 0]
    print(f"\nbacktest on {TEST}: {len(df)} players with history in "
          f"{TRAIN[0]}..{TRAIN[-1]} who also appeared in {TEST}\n")

    for label, col in [("model projection", "projected_points"),
                       ("naive 4-season average", "naive_points")]:
        r = df[col].corr(df["actual_points"])
        spearman = df[col].corr(df["actual_points"], method="spearman")
        mae = (df[col] - df["actual_points"]).abs().mean()
        print(f"{label:24s}  pearson r={r:.3f}  spearman={spearman:.3f}  MAE={mae:.1f} pts")

    # The question that actually matters: does the top of the ranking deliver?
    print()
    for label, col in [("model projection", "projected_points"),
                       ("naive 4-season average", "naive_points")]:
        for n in (15, 30, 50):
            top = df.nlargest(n, col)
            print(f"{label:24s}  top-{n:2d} averaged {top['actual_points'].mean():6.1f} "
                  f"actual {TEST} points")
        print()

    print(f"league-wide average for the sample: {df['actual_points'].mean():.1f}")
    df.to_csv(PROC / "backtest_2025-26.csv", index=False)


if __name__ == "__main__":
    main()

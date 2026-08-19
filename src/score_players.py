"""Score every 2026-27 Premier League player from 5 seasons of history.

The headline number is `projected_points` -- an estimate of what the player
returns over the 2026-27 season, built as:

    projected_points = points_per_90 x projected_minutes / 90

where both factors are corrected for the three things that make raw 5-season
totals misleading:

  1. RECENCY  - a 2021-22 season says much less about 2026-27 than 2025-26 does.
  2. AGE      - a 35-year-old's history overstates what is left in the tank.
  3. FITNESS  - a player currently injured cannot bank points in the autumn.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"

TODAY = dt.date(2026, 8, 19)
SEASON_MINUTES = 38 * 90  # 3420

# Exponential recency weights: the most recent season carries ~4.5x the weight
# of the oldest one.
SEASON_WEIGHTS = {
    "2021-22": 0.08,
    "2022-23": 0.12,
    "2023-24": 0.18,
    "2024-25": 0.26,
    "2025-26": 0.36,
}

# Prior strength (in minutes) used to shrink small samples toward the positional
# baseline. A player with 900 minutes is pulled halfway to the baseline.
SHRINK_MINUTES = 900.0

# One outstanding season is weaker evidence than five consistent ones, even when
# the minutes are identical. `confidence` runs from ~0.6 (a single 2025-26
# campaign) to 1.0 (a record spanning the whole window) and blends a player's
# own numbers against a newcomer prior measured from the data itself.

# How far team quality is allowed to move a projection. Defenders and keepers
# live off clean sheets, so their club matters more than it does for attackers.
TEAM_EFFECT = {"GKP": 0.30, "DEF": 0.28, "MID": 0.14, "FWD": 0.18}


# --------------------------------------------------------------------------
# Age curves
# --------------------------------------------------------------------------
# Outfielders peak around 25-28 and decline sharply past 32. Goalkeepers peak
# later and hold their level for longer, so they get their own curve.
# Values below 24 exceed 1.0 because a young player's history *understates*
# their current level -- they are still improving.
AGE_CURVE_OUTFIELD = {
    18: 1.10, 19: 1.09, 20: 1.08, 21: 1.06, 22: 1.04, 23: 1.02,
    24: 1.00, 25: 1.00, 26: 1.00, 27: 1.00, 28: 0.99,
    29: 0.97, 30: 0.94, 31: 0.91, 32: 0.87, 33: 0.82,
    34: 0.76, 35: 0.69, 36: 0.61, 37: 0.53, 38: 0.45,
}
AGE_CURVE_KEEPER = {
    18: 1.10, 19: 1.09, 20: 1.08, 21: 1.07, 22: 1.06, 23: 1.05,
    24: 1.03, 25: 1.02, 26: 1.01, 27: 1.00, 28: 1.00, 29: 1.00,
    30: 1.00, 31: 0.99, 32: 0.98, 33: 0.96, 34: 0.93,
    35: 0.89, 36: 0.84, 37: 0.78, 38: 0.70,
}


def age_factor(age: float | None, position: str) -> float:
    """Interpolate the age curve; flat outside the tabulated range."""
    if age is None or pd.isna(age):
        return 1.0
    curve = AGE_CURVE_KEEPER if position == "GKP" else AGE_CURVE_OUTFIELD
    ages = sorted(curve)
    if age <= ages[0]:
        return curve[ages[0]]
    if age >= ages[-1]:
        return curve[ages[-1]]
    return float(np.interp(age, ages, [curve[a] for a in ages]))


# --------------------------------------------------------------------------
# Fitness / availability
# --------------------------------------------------------------------------
# Fraction of the 2026-27 season we expect the player to be available for,
# given their status on the FPL API as of TODAY. Cross-checked against press
# reporting (see reports/news_review.md).
STATUS_AVAILABILITY = {
    "a": 1.00,   # available
    "d": None,   # doubtful -- derived from chance_of_playing below
    "s": 0.94,   # suspended: a few matches at the start of the season
    "i": 0.55,   # injured: default, overridden when a return date is known
    "u": 0.00,   # unavailable -- left the club
}

# Return dates parsed out of the FPL news strings give a much better estimate
# than the blanket "injured" default. Season runs 21 Aug 2026 -> late May 2027.
SEASON_START = dt.date(2026, 8, 21)
SEASON_END = dt.date(2027, 5, 23)
SEASON_DAYS = (SEASON_END - SEASON_START).days


def availability_from_news(status: str, chance: float | None, news: str,
                           return_date: dt.date | None) -> tuple[float, str]:
    """Return (fraction of season available, human-readable reason)."""
    if status == "u":
        return 0.0, "left the club"

    if return_date is not None:
        missed = max(0, (return_date - SEASON_START).days)
        frac = max(0.0, 1.0 - missed / SEASON_DAYS)
        # Players coming back from a long lay-off rarely go straight back to
        # full output, so shade it down a little further.
        frac *= 0.95
        return frac, f"out until {return_date:%d %b %Y}"

    if status == "i":
        # "Unknown return date" is the risky case: no timeline published.
        return 0.55, "injured, no published return date"

    if status == "d":
        pct = (chance if chance is not None else 50.0) / 100.0
        # A GW1 doubt costs little across 38 games, but a 25% flag usually
        # signals something that lingers.
        frac = 0.90 + 0.10 * pct if pct >= 0.75 else 0.72 + 0.24 * pct
        return frac, f"doubtful, {int(pct * 100)}% chance for GW1"

    if status == "s":
        return 0.94, "suspended for the opening matches"

    return 1.00, "fully available"


def parse_return_date(news: str) -> dt.date | None:
    """Pull 'Expected back 28 Nov' style dates out of the FPL news field."""
    if not isinstance(news, str) or "Expected back" not in news:
        return None
    tail = news.split("Expected back", 1)[1].strip().rstrip(".")
    for fmt in ("%d %b", "%d %B"):
        try:
            parsed = dt.datetime.strptime(tail, fmt).date()
        except ValueError:
            continue
        # No year in the string: pick the next occurrence after the season start.
        year = SEASON_START.year if parsed.month >= 7 else SEASON_START.year + 1
        return parsed.replace(year=year)
    return None


# --------------------------------------------------------------------------
def newcomer_priors(hist: pd.DataFrame) -> pd.DataFrame:
    """What a player with no Premier League record actually returns.

    Measured from every player whose first season inside the window was
    2022-23 or later (2021-22 is excluded because we cannot tell from this
    data whether it was really their debut). Using the median of *established*
    players as the prior instead would be survivorship bias: it assumes an
    unproven 20-year-old performs like someone who has already held down a
    place for 1500 minutes.
    """
    debut = hist.sort_values("season").groupby("code").first().reset_index()
    debut = debut[(debut["season"] != "2021-22") & (debut["minutes"] > 0)]
    priors = debut.groupby("position").apply(
        lambda g: pd.Series({
            "prior_p90": g["total_points"].sum() / (g["minutes"].sum() / 90),
            "prior_minute_share": (g["minutes"] / SEASON_MINUTES).mean(),
            "n_debutants": len(g),
        }),
        include_groups=False,
    )
    return priors


def compute_age(birth_date: str | float) -> float | None:
    if not isinstance(birth_date, str) or not birth_date:
        return None
    try:
        born = dt.date(*map(int, birth_date.split("-")))
    except ValueError:
        return None
    return round((TODAY - born).days / 365.25, 1)


def weighted_history(hist: pd.DataFrame) -> pd.DataFrame:
    """Collapse a player's seasons into recency-weighted rates."""
    hist = hist.copy()
    hist["w"] = hist["season"].map(SEASON_WEIGHTS)
    hist["w_min"] = hist["w"] * hist["minutes"]

    def agg(g: pd.DataFrame) -> pd.Series:
        w, wm = g["w"], g["w_min"]
        total_wm = wm.sum()
        out = {
            "seasons_played": int((g["minutes"] > 0).sum()),
            "total_minutes": g["minutes"].sum(),
            "total_points": g["total_points"].sum(),
            "total_goals": g["goals_scored"].sum(),
            "total_assists": g["assists"].sum(),
            "total_starts": g["starts"].sum(),
            "total_bonus": g["bonus"].sum(),
            "total_clean_sheets": g["clean_sheets"].sum(),
            # Recency-weighted per-90 rates.
            "w_points_per_90": (g["total_points"] * w).sum() / total_wm * 90 if total_wm else 0.0,
            "w_xgi_per_90": (g["expected_goal_involvements"].fillna(0) * w).sum() / total_wm * 90 if total_wm else 0.0,
            "w_bps_per_90": (g["bps"] * w).sum() / total_wm * 90 if total_wm else 0.0,
            # Recency-weighted share of the 3420 available minutes per season.
            "w_minute_share": (g["minutes"] * w).sum() / (w.sum() * SEASON_MINUTES),
            "w_effective_minutes": total_wm / w.sum() if w.sum() else 0.0,
            "evidence": w.where(g["minutes"] > 0, 0.0).sum(),
            "last_season_minutes": g.loc[g["season"] == "2025-26", "minutes"].sum(),
            "last_season_points": g.loc[g["season"] == "2025-26", "total_points"].sum(),
        }
        return pd.Series(out)

    return hist.groupby("code", group_keys=False)[hist.columns].apply(agg)


def main() -> None:
    hist = pd.read_csv(PROC / "player_seasons.csv")
    current = pd.read_csv(PROC / "current_players.csv")

    agg = weighted_history(hist).reset_index()
    df = current.merge(agg, on="code", how="left")

    # Players with no Premier League minutes in the window (new signings from
    # abroad, academy graduates) cannot be assessed on this data.
    df["has_history"] = df["total_minutes"].fillna(0) > 0
    df = df.fillna({c: 0.0 for c in agg.columns if c != "code"})

    df["age"] = df["birth_date"].apply(compute_age)

    # --- 1. Shrink per-90 rates toward the newcomer baseline ---------------
    priors = newcomer_priors(hist)
    print("newcomer priors measured from the data:")
    print(priors.round(3).to_string(), "\n")
    df["position_baseline_p90"] = df["position"].map(priors["prior_p90"])
    df["position_prior_share"] = df["position"].map(priors["prior_minute_share"])

    shrink = df["w_effective_minutes"] / (df["w_effective_minutes"] + SHRINK_MINUTES)
    df["shrunk_points_per_90"] = (
        shrink * df["w_points_per_90"] + (1 - shrink) * df["position_baseline_p90"]
    )

    # --- 1b. Discount a thin track record ----------------------------------
    df["confidence"] = df["evidence"].clip(lower=0.0) ** 0.5
    df["shrunk_points_per_90"] = (
        df["confidence"] * df["shrunk_points_per_90"]
        + (1 - df["confidence"]) * df["position_baseline_p90"]
    )

    # --- 1c. Team context ---------------------------------------------------
    # History is recorded at the player's old club; the projection belongs to
    # the new one. Attackers are indexed on their club's scoring, defenders and
    # keepers on how few goals it concedes.
    teams = pd.read_csv(PROC / "team_strength.csv").set_index("team")
    attack = df["team_name"].map(teams["attack_index"]).fillna(1.0)
    defence = df["team_name"].map(teams["defence_index"]).fillna(1.0)
    club_index = np.where(df["position"].isin(["GKP", "DEF"]), defence, attack)
    effect = df["position"].map(TEAM_EFFECT).fillna(0.15).to_numpy()
    df["team_factor"] = np.clip(1.0 + effect * (club_index - 1.0), 0.80, 1.22)

    # --- 2. Age correction --------------------------------------------------
    # Decline is physiological and applies whatever the sample size, but the
    # improvement credited to a young player is a forecast, so it is only
    # granted in proportion to the evidence that they already play.
    raw_age_factor = np.array([
        age_factor(a, p) for a, p in zip(df["age"], df["position"])
    ])
    df["age_factor"] = np.where(
        raw_age_factor > 1.0,
        1.0 + df["confidence"].to_numpy() * (raw_age_factor - 1.0),
        raw_age_factor,
    )

    # --- 3. Fitness correction ---------------------------------------------
    df["return_date"] = df["news"].apply(parse_return_date)
    avail = [
        availability_from_news(s, ch, n, rd)
        for s, ch, n, rd in zip(df["status"], df["chance_next"], df["news"], df["return_date"])
    ]
    df["availability"] = [a for a, _ in avail]
    df["availability_reason"] = [r for _, r in avail]

    # --- Projection ---------------------------------------------------------
    # Baseline minutes come from the recency-weighted share of a full season,
    # nudged toward last season's workload, then cut by age and fitness.
    observed_share = (
        0.65 * df["w_minute_share"] + 0.35 * (df["last_season_minutes"] / SEASON_MINUTES)
    )
    df["expected_minute_share"] = (
        df["confidence"] * observed_share
        + (1 - df["confidence"]) * df["position_prior_share"]
    )
    df["projected_minutes"] = (
        df["expected_minute_share"] * SEASON_MINUTES
        * df["availability"]
        * (0.5 + 0.5 * df["age_factor"])  # ageing costs starts as well as output
    )
    df["adjusted_points_per_90"] = (
        df["shrunk_points_per_90"] * df["age_factor"] * df["team_factor"]
    )
    df["projected_points"] = df["adjusted_points_per_90"] * df["projected_minutes"] / 90.0

    # Raw 5-season view, for the "what the naive numbers said" comparison.
    df["naive_points_per_season"] = df["total_points"] / 5.0
    df["points_per_million"] = df["projected_points"] / df["now_cost_m"]

    df = df.sort_values("projected_points", ascending=False)
    cols = [
        "code", "web_name", "full_name", "position", "team_name", "team_short",
        "now_cost_m", "age", "status", "availability", "availability_reason",
        "news", "seasons_played", "total_minutes", "total_points",
        "total_goals", "total_assists", "last_season_points",
        "w_points_per_90", "shrunk_points_per_90", "age_factor",
        "adjusted_points_per_90", "confidence", "team_factor",
        "expected_minute_share", "projected_minutes",
        "projected_points", "points_per_million", "naive_points_per_season",
        "selected_by_percent", "has_history",
    ]
    df[cols].to_csv(PROC / "player_scores.csv", index=False)
    print(f"scored {len(df)} players -> data/processed/player_scores.csv")
    print(df.head(30)[["web_name", "position", "team_short", "now_cost_m", "age",
                       "availability", "confidence", "team_factor",
                       "adjusted_points_per_90", "projected_minutes",
                       "projected_points"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()

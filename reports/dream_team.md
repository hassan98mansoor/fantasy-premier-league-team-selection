# Premier League Dream Team — 15 players for 2026-27

**Built 19 August 2026, two days before the season opens.**
Five seasons of data (2021-22 → 2025-26), adjusted for current injuries, ageing
and club moves.

---

## The squad

Formation **3-5-2**, cost **£100.0m of £100.0m**, projected **1,657 points from
the starting XI** and 1,896 across all 15.

### Starting XI

| # | Player | Pos | Club | Price | Age | 5-season pts | Pts/90 | Projected 26-27 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | **David Raya** | GKP | Arsenal | £6.0m | 30.9 | 700 | 4.15 | **168.7** |
| 2 | **Gabriel Magalhães** | DEF | Arsenal | £8.0m | 28.7 | 767 | 5.19 | **168.0** |
| 3 | **Marc Guéhi** | DEF | Man City | £6.0m | 26.1 | 579 | 3.90 | **135.7** |
| 4 | **Tyrick Mitchell** | DEF | Crystal Palace | £4.5m | 27.0 | 579 | 3.49 | **119.5** |
| 5 | **Bryan Mbeumo** | MID | Man Utd | £8.0m | 27.0 | 780 | 5.38 | **152.7** |
| 6 | **Declan Rice** | MID | Arsenal | £7.5m | 27.6 | 687 | 4.40 | **150.9** |
| 7 | **Dominik Szoboszlai** | MID | Liverpool | £7.0m | 25.8 | 402 | 4.63 | **136.1** |
| 8 | **Phil Foden** | MID | Man City | £7.0m | 26.2 | 745 | 6.13 | **133.8** |
| 9 | **Alexis Mac Allister** | MID | Liverpool | £5.5m | 27.7 | 572 | 3.94 | **117.8** |
| 10 | **Erling Haaland** | FWD | Man City | £15.5m | 26.1 | 909 | 7.18 | **216.8** |
| 11 | **Ollie Watkins** | FWD | Aston Villa | £8.0m | 30.6 | 887 | 5.65 | **156.5** |

### Bench

| Player | Pos | Club | Price | Age | Projected | Role |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Vitalii Mykolenko | DEF | Everton | £4.5m | 27.2 | 99.0 | Genuine cover — a starter in his own right |
| Martin Dúbravka | GKP | Spurs | £4.0m | 37.6 | 50.2 | Cheapest viable second keeper |
| Dara O'Shea | DEF | Ipswich | £4.0m | 27.5 | 42.5 | Budget filler |
| Sindre Walle Egeli | FWD | Ipswich | £4.5m | 20.2 | 47.9 | Budget filler |

Club distribution: Arsenal 3, Man City 3, Liverpool 2, Ipswich 2, and one each
from Crystal Palace, Man Utd, Aston Villa, Spurs, Everton — legal under the
three-per-club rule.

**Captain: Erling Haaland.** 216.8 projected points is 29% clear of the next
player. He has scored 112 goals in four Premier League seasons and came off 27
goals and 239 points last year.

---

## Why these players and not the obvious ones

A ranking on raw five-season totals would pick a materially different team. The
differences are the whole point of the exercise.

### Dropped despite a top-50 five-season record

| Player | 5-season pts | Naive rank | Model rank | Reason |
| --- | ---: | ---: | ---: | --- |
| **Virgil van Dijk** | 745 | 7 | 91 | 35.1 years old; age factor 0.68; expected to leave Liverpool in 2027 |
| **Rodrigo** | 466 | 53 | — | Joined Barcelona; cannot score in England |
| **William Saliba** | 548 | 27 | 131 | Back injury, no published return date |
| **Fabian Schär** | 519 | 37 | 256 | 34.7; scored 51 last season, down from a 100+ peak |
| **Chris Wood** | 516 | 38 | 212 | 34.7; 41 points last season |
| **Danny Welbeck** | 510 | 40 | 170 | 35.7; age factor 0.63 |
| **Andy Robertson** | 529 | 32 | 210 | 32.4; 55 points last season |
| **Pascal Groß** | 478 | 48 | 285 | 35.2; age factor 0.67 |
| **Alisson Becker** | 648 | 13 | 61 | 33.9; 91 points last season |
| **Bruno Fernandes** | 902 | 2 | 9 | Not dropped on merit — £12.0m is unaffordable inside the budget |

### Promoted well above their five-season totals

| Player | 5-season pts | Naive rank | Model rank | Reason |
| --- | ---: | ---: | ---: | --- |
| **Dominik Szoboszlai** | 402 | 76 | 12 | Only three PL seasons, all improving: 99 → 143 → 160 |
| **Marc Guéhi** | 579 | 21 | 13 | Career-best 179 last season, and a move to a much stronger defence |
| **Antoine Semenyo** | 492 | 45 | 7 | 107 → 165 → 202 trajectory, now at Man City |
| **Morgan Rogers** | 365 | 91 | 16 | 24, 169 points last season |
| **Igor Thiago** | 190 | 201 | 24 | 181 of those 190 points came last season |

---

## Method

```
projected_points = adjusted_points_per_90 × projected_minutes ÷ 90
```

Five corrections turn a five-year record into a forward-looking number.

**1. Recency weighting.** Seasons are weighted 0.08 / 0.12 / 0.18 / 0.26 / 0.36
from 2021-22 to 2025-26. The most recent season counts 4.5× the oldest.

**2. Small-sample shrinkage.** Per-90 rates are pulled toward a positional
baseline with a 900-minute prior, so a player with three good games does not
outrank one with three good seasons.

**3. Track-record confidence.** `confidence = (sum of weights of seasons played)^0.5`,
running from 0.6 for a single 2025-26 campaign to 1.0 for a full five-year
record. It blends both the per-90 rate and the expected minutes toward a
newcomer baseline **measured from the data itself** — every player whose first
season fell inside the window (622 of them):

| Position | Debut-season pts/90 | Debut-season share of minutes |
| --- | ---: | ---: |
| GKP | 2.99 | 0.386 |
| DEF | 2.83 | 0.353 |
| MID | 3.79 | 0.245 |
| FWD | 5.00 | 0.252 |

Using the median of *established* players here instead would be survivorship
bias — it would assume an unproven 20-year-old performs like someone who has
already held down a place for 1,500 minutes. That single change moved Ludovic
Truffert (one excellent Bournemouth season, no other PL history) from 2nd overall
to 29th, and dropped the best zero-history player from a projected 120 points to
48.

**4. Age curves.** Outfielders hold a plateau from 24-28 and fall away sharply
past 32; goalkeepers peak later and decline more slowly. Decline is applied in
full regardless of sample size, because it is physiological. Improvement credited
to a young player is only granted in proportion to `confidence`, because it is a
forecast rather than an observation.

| Age | 24-28 | 30 | 32 | 34 | 35 | 36 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Outfield | 1.00 | 0.94 | 0.87 | 0.76 | 0.69 | 0.61 |
| Goalkeeper | 1.00-1.03 | 1.00 | 0.98 | 0.93 | 0.89 | 0.84 |

**5. Fitness.** Each player's live FPL status becomes a fraction of the season
they are expected to be available for. Published return dates are converted into
the share of the 21 Aug – 23 May campaign that is lost; "unknown return date"
takes a flat 0.55; suspensions 0.94; short-term doubts are scaled by the
published chance of playing. Players who have left the league are zeroed.
Full detail and sources are in [`news_review.md`](news_review.md).

**Plus club context.** History is recorded at the player's old club and the
projection belongs to the new one — which matters when Guéhi and Semenyo have
both moved to Man City. Attack and defence indices are rebuilt from the last two
seasons of actual match results, because the FPL API's own strength ratings are
all zero before a season starts. Keepers and defenders are indexed on how few
goals their club concedes (weight 0.30 / 0.28), attackers on how many it scores
(0.14 / 0.18), capped at ±22%.

---

## Does it work? A backtest

The method was rebuilt using only 2021-22 → 2024-25 and used to project 2025-26,
then scored against what actually happened, for the 510 players present in both
windows.

| | Pearson r | Spearman | MAE | Top-15 picks averaged | Top-30 | Top-50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **This model** | **0.582** | **0.602** | **33.3** | **143.6** | **123.7** | **103.4** |
| Naive 4-season average | 0.469 | 0.501 | 37.0 | 137.2 | 107.7 | 97.1 |
| Sample average | | | | 54.0 | 54.0 | 54.0 |

The model beats the naive baseline on every measure, and the gap widens as you
go deeper down the list — which is where a 15-player squad actually gets decided.

Two honest caveats: the backtest can only score players who appeared in both
windows, so it does not penalise either method for picking someone who left the
league; and it cannot test the injury layer at all, because that depends on live
news and we have no August 2025 snapshot of it.

---

## Alternative: no budget limit

Removing the £100m cap (keeping formation and three-per-club) gives a squad
costing £118.5m and projecting 1,719 XI points — only 62 more, or 3.8%, for 18.5%
more money. Bukayo Saka, Antoine Semenyo, Bruno Fernandes and Morgan Gibbs-White
come in for Szoboszlai, Foden, Mac Allister and Rice.

That narrow gap is the real finding: the budget constraint costs very little,
because the value is concentrated in mid-priced players like Mbeumo (£8.0m),
Rice (£7.5m) and Guéhi (£6.0m) rather than the premium names.

---

## Reproducing this

```bash
pip install -r requirements.txt
python src/build_dataset.py    # download + aggregate 5 seasons
python src/team_strength.py    # club attack/defence indices
python src/score_players.py    # projections
python src/pick_squad.py       # optimise the 15
python src/flag_risks.py       # age and fitness flags
cd src && python backtest.py   # validation
```

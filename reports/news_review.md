# Current-news review: injuries, bans and ageing (as at 19 August 2026)

The 2026-27 Premier League season opens on **Friday 21 August 2026**. Five-season
statistics are a record of the past; this file records the present-day facts that
decide whether that record can repeat, and how they were folded into the model.

## Sources used

| Source | What it gave us |
| --- | --- |
| [Fantasy Premier League API](https://fantasy.premierleague.com/api/bootstrap-static/) | Machine-readable `status`, `news`, `chance_of_playing_next_round` for all 595 registered players, updated daily by the Premier League |
| [Premier League injury hub](https://www.premierleague.com/en/latest-player-injuries) | Official club-by-club absentee list (75 absentees tracked across 20 clubs as of 12 Aug) |
| [RotoWire PL injuries](https://www.rotowire.com/soccer/article/premier-league-injuries-latest-injury-news-updates-suspensions-128516) | Injury types and estimated return dates |
| [OneFPL GW1 absentees](https://onefpl.com/blog/who-will-miss-fpl-gameweek-1-2026-27) | Confirmed outs, major doubts and monitor list for the opening weekend |
| [PlanetFootball](https://www.planetfootball.com/lists-and-rankings/big-name-footballers-retired-2026) / [GiveMeSport](https://www.givemesport.com/football-soccer-players-who-retired-2026/) | 2026 retirements |
| [Liverpool.com](https://www.liverpool.com/liverpool-fc-news/features/virgil-van-dijk-among-11-34238889) / [CaughtOffside](https://www.caughtoffside.com/2026/04/16/liverpool-virgil-van-dijk-exit-2027-contract-future/) | Van Dijk's contract and expected 2027 exit |

The API list was cross-checked against the press reporting and the two agree on
every significant case (Saliba, Timber, Kulusevski, Mitoma, Ekitiké, Kroupi,
Minteh, Ferguson, Mount, Fofana's ban). Where the press gave a return date that
the API did not, the API's own "Expected back" strings were used, because they
are the ones the league updates daily.

## 1. Players already retired — removed automatically

Retirement is handled by construction rather than by hand: the candidate pool is
the list of players **registered with a club for 2026-27**, so anyone who has
hung up their boots simply is not in it. The 2026 retirement class included
**James Milner**, **Ashley Young** (40), **Aaron Ramsey** (35), **Kasper
Schmeichel** (39), **Łukasz Fabiański** (41), **Lukas Podolski** (40), **Jonny
Evans** and **James Tomkins** — none appear in the 2026-27 player list, so none
could be selected however good their five-year record looks.

## 2. Players who have left the Premier League — hard-excluded

37 players carry FPL status `u`. Their history is in our data but they cannot
score a point in England this season. The notable ones by five-season points:

| Player | Five-season points | Destination |
| --- | ---: | --- |
| Rodrigo (Man City) | 466 | Barcelona |
| Jack Harrison (Leeds) | 436 | New England Revolution |
| Trevoh Chalobah (Chelsea) | 416 | Como |
| Lucas Digne (Aston Villa) | 404 | Paris Saint-Germain |
| Cristian Romero (Spurs) | 376 | Atlético Madrid |
| Guglielmo Vicario (Spurs) | 268 | Juventus (loan) |

## 3. Currently injured — discounted, not deleted

47 players carry status `i`. The model converts each into a *fraction of the
season available*: a published return date is turned into the share of the
21 Aug – 23 May campaign the player will miss, then shaded a further 5% for the
time it takes to get back to full output. "Unknown return date" is the dangerous
category and takes a flat 0.55.

| Player | Club | Reported problem | Availability used |
| --- | --- | --- | ---: |
| William Saliba | Arsenal | Back injury, no return date; told to rest two weeks, "out for an extended period" | 0.55 |
| Jurriën Timber | Arsenal | Groin, still weeks from full training | 0.55 |
| Dejan Kulusevski | Spurs | Knee/patella — **out over a year**, missed the 2026 World Cup | 0.55 |
| Kaoru Mitoma | Brighton | Hamstring, no return date | 0.55 |
| Hugo Ekitiké | Liverpool | Achilles | 0.55 |
| Joelinton | Newcastle | Unspecified, no return date | 0.55 |
| Yankuba Minteh | Brighton | Leg — expected back 28 Nov | 0.61 |
| Evan Ferguson | Brighton | Ankle — expected back 10 Oct | 0.75 |
| Tom Cairney | Fulham | Knee — expected back 10 Oct | 0.75 |
| Carlos Baleba | Brighton | Ankle — expected back 23 Aug | 0.95 |

Suspensions are a much smaller haircut, because they cost a handful of matches
at most: **Wesley Fofana** (Chelsea, until 6 Sep), **Joachim Andersen** (Fulham,
until 30 Aug) and **Ryan Christie** (Bournemouth, until 29 Aug) are all set to
0.94.

Short-term doubts are scaled by the published chance of playing. **Jérémy Doku**,
**Matheus Nunes**, **Mohammed Kudus** and **Curtis Jones** (all 75%) lose about
2% of a season; **Christian Nørgaard** and **Willy Gnonto** (25%) lose about 22%,
because a 25% flag usually signals something that lingers.

## 4. Ageing players — the subtler trap

Nobody in this group is injured or retired, which is exactly why they are
dangerous: their five-season totals look outstanding and their availability flag
reads "fully available". The decline is in the age curve, not the news feed.

**Virgil van Dijk is the clearest case.** He is 35.1, has the 7th-highest
five-season total of any registered player (745 points), and started all of last
season. But he is in the final year of his contract, [Liverpool are expected to
let him go in 2027 as part of a defensive rebuild](https://www.caughtoffside.com/2026/04/16/liverpool-virgil-van-dijk-exit-2027-contract-future/),
and a 35-year-old centre-back is well past the point where the previous four
seasons predict the next one. The age curve puts him at **0.68** — he falls from
naive rank 7 to model rank 91 and is not selected.

Others in the same bracket, all "available" and all downgraded on age alone:

| Player | Age | Five-season points | Last season | Age factor | Naive rank → model rank |
| --- | ---: | ---: | ---: | ---: | --- |
| Virgil van Dijk | 35.1 | 745 | 175 | 0.68 | 7 → 91 |
| Alisson Becker | 33.9 | 648 | 91 | 0.93 | 13 → 61 |
| Emiliano Martínez | 34.0 | 610 | 120 | 0.93 | 16 → 41 |
| James Tarkowski | 33.7 | 581 | 170 | 0.78 | 20 → 79 |
| Nick Pope | 34.3 | 542 | 96 | 0.92 | 29 → 90 |
| Andy Robertson | 32.4 | 529 | 55 | 0.85 | 32 → 210 |
| Dan Burn | 34.3 | 526 | 93 | 0.74 | 34 → 174 |
| Fabian Schär | 34.7 | 519 | 51 | 0.71 | 37 → 256 |
| Chris Wood | 34.7 | 516 | 41 | 0.71 | 38 → 212 |
| Danny Welbeck | 35.7 | 510 | 126 | 0.63 | 40 → 170 |
| Pascal Groß | 35.2 | 478 | 78 | 0.67 | 48 → 285 |

The "last season" column is the tell. Robertson (55), Schär (51) and Wood (41)
have already fallen off a cliff; the five-season total is carrying weight the
player no longer does.

**Bruno Fernandes is the borderline call.** At 31.9 he takes a 0.87 age factor,
yet he scored 235 points last season and still projects 9th overall. He is not
excluded on age — he is excluded on **price**: at £12.0m the budget optimiser
prefers to spend that money elsewhere. He starts in the unlimited-budget XI.

## 5. What this review does *not* cover

* **The 2026 World Cup.** It was played this summer, and clubs are managing the
  load: Ollie Watkins, Ezri Konsa and Emiliano Martínez were all rested from the
  UEFA Super Cup, and Declan Rice only got his first 45 minutes back in the
  Community Shield. Early-season rotation for tournament players is a real risk
  the model does not price.
* **Players with no Premier League record.** 121 of the 595 registered players
  have no minutes in the last five seasons. They are scored on a measured
  newcomer baseline, which is honest but deliberately conservative — a genuinely
  elite signing from abroad would be underrated by this method.
* **Fixture difficulty and rotation**, which matter enormously week to week but
  wash out over a 38-game projection.

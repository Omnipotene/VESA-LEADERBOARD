# VESA League S12 Rating Formula

**Complete Documentation of the Team Rating and Division Assignment System**

---

## Overview

The VESA League S12 rating system calculates player and team ratings based on:
1. **Individual performance** (placement + kills across 4 days)
2. **Lobby consistency bonuses** (extreme multipliers for high-tier lobbies)
3. **Fairness adjustments** (average per day, not total)
4. **Team composition** (sum of 3 player ratings)

---

## Step-by-Step Formula

### STEP 1: S12 Placement Scoring (Per Day)

```
Raw Score Per Day = Placement Points + Kills
```

**Where:**
- **Placement Points**: Based on final placement in lobby (1st = most points)
- **Kills**: Total eliminations during that day
- **Damage**: Tracked but not used in base rating calculation

This gives each player a score for each day they participated.

---

### STEP 2: Aggregate Player Performance

For each player across all 4 placement days:

```
Total Score = Σ(Placement Points + Kills) for all days
Days Played = Count of days participated

Base S12 Rating = Total Score ÷ Days Played
```

**Why Average Per Day?**
- ✅ Fair to players who played fewer days (injury, schedule conflicts, etc.)
- ✅ Prevents penalizing partial participation
- ✅ Rewards consistent high performance over time

---

### STEP 3: Lobby Bonus System

Each lobby appearance adds a **percentage bonus** to the player's rating.

#### Lobby Bonus Percentages (Additive):

| Lobby | Bonus Per Appearance | Multiplier |
|-------|---------------------|------------|
| 1     | 8192%               | 81.92x     |
| 1.5   | 4096%               | 40.96x     |
| 2     | 2048%               | 20.48x     |
| 2.5   | 1024%               | 10.24x     |
| 3     | 512%                | 5.12x      |
| 3.5   | 256%                | 2.56x      |
| 4     | 128%                | 1.28x      |
| 4.5   | 64%                 | 0.64x      |
| 5     | 32%                 | 0.32x      |
| 5.5   | 16%                 | 0.16x      |
| 6     | 8%                  | 0.08x      |
| 6.5   | 4%                  | 0.04x      |
| 7     | 2%                  | 0.02x      |

#### Special Case - Day 1 Lobby Remapping:

- **Day 1 Lobby 3** → treated as **Lobby 3.5** (256%)
- **Day 1 Lobby 5** → treated as **Lobby 5.5** (16%)

**Reason:** Day 1 had multiple "3" lobbies (3A, 3B) and "5" lobbies (5A, 5B) that couldn't be distinguished in the data, so they're treated as the intermediate tier.

```
Total Lobby Bonus = Σ(Lobby Bonus %) for all 4 days
```

**Example:**
```
Player plays: Lobby 1, Lobby 1.5, Lobby 1, Lobby 1.5
Total Bonus = 8192% + 4096% + 8192% + 4096% = 24,576%
```

---

### STEP 4: Apply Lobby Bonus to Base Rating

```
Final S12 Rating = Base S12 Rating × (1 + Total Lobby Bonus)
```

**Example:**
```
Base Rating = 100 points (average per day)
Lobby Bonus = 24,576% (245.76 as decimal)

Final Rating = 100 × (1 + 245.76)
             = 100 × 246.76
             = 24,676 points
```

This dramatically amplifies ratings based on:
1. ✅ Consistency in high lobbies
2. ✅ Number of days played in top lobbies
3. ✅ Base performance (kills + placement)

---

### STEP 5: Combine with S11 Ratings (Optional Weight)

**Current System:** 100% S12 Weight, 0% S11 Weight

```
Combined Rating = S12 Rating × 1.00 + S11 Rating × 0.00
                = S12 Rating only
```

**Note:** S11 ratings are tracked but not currently used in the formula. They could be blended if desired (e.g., 70% S12 + 30% S11).

---

### STEP 6: Calculate Team Ratings

For each team with 3 players:

```
Team Rating = Player1 Rating + Player2 Rating + Player3 Rating
```

**Where:**
- Each player's rating is their **Final S12 Rating** (with lobby bonuses)
- Missing players are assigned a **default rating of 80 points**
- Teams are then ranked by total rating

---

### STEP 7: Assign Tiers

Teams are assigned tiers based on their total rating:

| Tier | Minimum Rating | Description |
|------|----------------|-------------|
| S+   | 8000+          | Top teams with exceptional ratings |
| S    | 4000+          | Very strong teams |
| A+   | 2000+          | Strong teams |
| A    | 1000+          | Above average teams |
| B+   | 500+           | Average teams |
| B    | 250+           | Below average teams |
| C+   | 125+           | Lower tier teams |
| C    | 62.5+          | Novice teams |
| C-   | 31.25+         | Entry level |
| D+   | 15.625+        | Very new |
| D    | 7.8+           | Beginner |
| D-   | 0+             | Starting level |

**Note:** Most teams (101/140) ended up in S+ tier due to the extreme lobby bonus multipliers (8192%, 4096%, etc.)

---

### STEP 8: Division Assignment

Teams are placed into **7 divisions of 20 teams each**:

1. Sort all 140 teams by Team Rating (highest to lowest)
2. Consider scheduling constraints for each team
3. Assign teams to divisions based on:
   - ✅ Skill grouping (similar ratings in same division)
   - ✅ Schedule compatibility (teams can't play on certain days)
   - ✅ Balanced division sizes (exactly 20 teams per division)

#### Division Schedule:
- **Division 1:** Thursday
- **Division 2:** Wednesday
- **Division 3:** Monday
- **Division 4:** Thursday
- **Division 5:** Monday
- **Division 6:** Wednesday
- **Division 7:** Monday

**Result:** 140 teams evenly distributed across 7 divisions

---

## Complete Formula Summary

### For Player i:

```
1. Days_Played_i = count(days where player i participated)
2. Total_Score_i = Σ(Placement_Points_d + Kills_d) for all days d
3. Base_Rating_i = Total_Score_i ÷ Days_Played_i
4. Lobby_Bonus_i = Σ(Lobby_Bonus_Percentage_d) for all days d
5. Final_Rating_i = Base_Rating_i × (1 + Lobby_Bonus_i)
```

### For Team t with players {p1, p2, p3}:

```
Team_Rating_t = Final_Rating_p1 + Final_Rating_p2 + Final_Rating_p3
```

### Division Assignment:

```
Sort teams by Team_Rating_t descending
Assign to divisions 1-7 (20 teams each) with schedule constraints
```

---

## Key Features

✅ **Fair to partial participation** (average per day)
✅ **Rewards high lobby placement** (massive bonuses)
✅ **Values consistency** (multiple high lobby days)
✅ **Considers team composition** (3-player sum)
✅ **Respects scheduling constraints**
✅ **Creates balanced divisions** (20 teams each)
✅ **Transparent and reproducible**
✅ **Handles name changes** via alias system
✅ **Stored in SQL database** for queries

---

## Example Calculation

**Player: Haki (Top ranked player)**

| Day | Lobby | Score | Kills | Daily Score |
|-----|-------|-------|-------|-------------|
| 1   | 1     | 65    | 15    | 80          |
| 2   | 1.5   | 70    | 18    | 88          |
| 3   | 1     | 68    | 20    | 88          |
| 4   | 1.5   | 72    | 16    | 88          |

**Step 1:** Total Score = 80 + 88 + 88 + 88 = **344**
**Step 2:** Days Played = **4**
**Step 3:** Base Rating = 344 ÷ 4 = **86 points/day**

**Step 4:** Lobby Bonuses
- Day 1: Lobby 1 → +8192%
- Day 2: Lobby 1.5 → +4096%
- Day 3: Lobby 1 → +8192%
- Day 4: Lobby 1.5 → +4096%
- **Total Bonus = 24,576%**

**Step 5:** Final Rating = 86 × (1 + 245.76) = 86 × 246.76 = **21,221**

*(Actual value may differ based on exact placement scoring)*

---

## Data Pipeline

1. **Scrape S12 placement data** from Overstat.gg
2. **Fix Day 1 lobbies** (3→3.5, 5→5.5)
3. **Extract lobby bonuses** for all 547 players
4. **Aggregate by average** per day
5. **Apply lobby bonuses** (8192% system)
6. **Calculate team ratings** (sum of 3 players)
7. **Assign divisions** (7 divisions × 20 teams)
8. **Export to CSV** and SQL database
9. **Compare with FINAL PLACEMENTS** for validation

---

## Output Files

- `output/division_assignments_with_changes.csv` - Full rankings with rank changes
- `output/division_summary.csv` - Statistical summary by division
- `vesa_league.db` - SQLite database with all data
- `output/combined_all_seasons_ratings_with_bonus.json` - All player ratings

---

**System Version:** S12 (2025)
**Last Updated:** After Day 1 lobby remapping fix
**Total Teams:** 140 active teams
**Total Players:** 547 players with ratings

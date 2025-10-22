# Quick Start Guide

## 1. Install Dependencies

```bash
./setup.sh
```

Or manually:
```bash
pip3 install -r requirements.txt
playwright install chromium
```

## 2. Test the Scraper

Before running the full pipeline, test with a single URL:

```bash
python3 test_scraper.py "YOUR_OVERSTAT_URL" player
```

This will:
- Open a visible browser window
- Show you what's being scraped
- Display sample data
- Help you verify the scraper works

## 3. Prepare Your URL List

1. Copy the template:
   ```bash
   cp config/urls_template.csv config/urls.csv
   ```

2. Edit `config/urls.csv` with your actual URLs:
   ```csv
   url,day,lobby,type,description
   https://overstat.gg/tournament/.../player-standings,1,1,player,Day 1 Lobby 1
   https://overstat.gg/tournament/.../player-standings,1,2,player,Day 1 Lobby 2
   ```

## 4. Run the Scraper

```bash
python3 main.py --urls config/urls.csv
```

## 5. Check Output

Look in the `output/` directory for:
- `player_leaderboard_*.csv` - Your rankings!
- `summary_stats_*.txt` - Overall statistics
- `debug_page.html` - If something went wrong

## Common Issues

### Browser doesn't open
```bash
playwright install chromium
```

### No data scraped
1. Run test_scraper.py to see what's happening
2. Check if the URL is correct
3. Look at `output/debug_page.html`

### Wrong data in results
The HTML selectors might need adjustment. Edit `src/scraper.py` around lines 93-105 and 145-157.

## Understanding the Output

### player_leaderboard.csv

```csv
Rank,Player Name,Total Points,Total Kills,Total Damage,Matches Played,Avg Points/Match
1,PlayerName,1250.45,127,45678,12,104.20
```

- **Rank**: Overall ranking by weighted score
- **Total Points**: Sum of all weighted scores
- **Total Kills**: Total kills across all matches
- **Total Damage**: Total damage across all matches
- **Matches Played**: Number of matches found for this player
- **Avg Points/Match**: Average weighted score per match

### How Weighting Works

Each match score is weighted by:

**Weighted Score = Raw Score × Lobby Weight × Day Weight**

Example for 50 points in Lobby 2 on Day 3:
- Raw: 50
- Lobby 2 weight: 0.80
- Day 3 weight: 1.35
- **Result: 50 × 0.80 × 1.35 = 54.0 weighted points**

Higher lobbies and later days count for more!

## Next Steps

Once this works, you can:
1. Add more URLs to scrape more matches
2. Adjust weights in `config/weights.json`
3. Export detailed breakdowns with `--export-detailed`
4. Build team ratings (Version 2!)

## Need Help?

1. Run test_scraper.py first
2. Check output/debug_page.html
3. Run with `--no-headless` to see the browser
4. Check the logs for error messages

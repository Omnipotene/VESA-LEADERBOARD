# VESA League Player Statistics Scraper

A comprehensive web scraping and data analysis system for VESA Apex Legends league statistics from Overstat.gg.

## Features

- **Web Scraping**: Uses Playwright to scrape JavaScript-rendered pages from Overstat.gg
- **Weighted Scoring**: Implements lobby difficulty and day progression weighting
- **Database Storage**: SQLite database for persistent storage and analysis
- **Player Leaderboards**: Generates CSV leaderboards with individual player rankings
- **Flexible Configuration**: JSON-based configuration for weights and parameters

## Project Structure

```
vesa-scraper/
├── config/
│   ├── weights.json          # Lobby and day weight configuration
│   └── urls_template.csv     # Template for URL list
├── data/
│   └── vesa.db              # SQLite database (created on first run)
├── output/
│   ├── player_leaderboard_*.csv
│   ├── summary_stats_*.txt
│   └── error_*.png          # Debug screenshots
├── src/
│   ├── __init__.py
│   ├── database.py          # Database management
│   ├── scraper.py           # Playwright web scraper
│   ├── weights.py           # Weighting system
│   ├── aggregator.py        # Player statistics aggregation
│   └── exporter.py          # CSV export functionality
├── main.py                  # Main orchestrator script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

### 1. Install Python Dependencies

```bash
cd vesa-scraper
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

Playwright requires browser binaries to be installed:

```bash
playwright install chromium
```

## Configuration

### 1. Weight Configuration

Edit `config/weights.json` to adjust lobby and day weights:

```json
{
  "lobby_weights": {
    "system": "aggressive",
    "decay_factor": 0.80,
    "weights": {
      "1": 1.00,
      "2": 0.80,
      "7": 0.26
    }
  },
  "day_weights": {
    "system": "optionB",
    "weights": {
      "1": 1.0,
      "2": 1.15,
      "3": 1.35,
      "4": 1.6
    }
  }
}
```

### 2. URL List Configuration

Create a CSV file with your Overstat.gg URLs (copy from `config/urls_template.csv`):

```csv
url,day,lobby,type,description
https://overstat.gg/tournament/.../player-standings,1,1,player,Day 1 Lobby 1
https://overstat.gg/tournament/.../scoreboard,1,2,team,Day 1 Lobby 2
```

**Columns:**
- `url`: Full Overstat.gg URL
- `day`: Day number (1-4)
- `lobby`: Lobby identifier (1, 1.5, 2, etc.)
- `type`: "player" or "team"
- `description`: Human-readable description

## Usage

### Basic Usage

Scrape URLs and generate leaderboard:

```bash
python main.py --urls config/urls.csv
```

### Advanced Options

```bash
# Clear database before scraping (fresh start)
python main.py --urls config/urls.csv --clear-db

# Export detailed match-by-match breakdown
python main.py --urls config/urls.csv --export-detailed

# Show browser during scraping (for debugging)
python main.py --urls config/urls.csv --no-headless

# Only aggregate existing data (skip scraping)
python main.py --aggregate-only

# Use custom database location
python main.py --urls config/urls.csv --db data/custom.db
```

### Command-Line Arguments

- `--urls`: Path to CSV file with URLs to scrape
- `--db`: Database path (default: data/vesa.db)
- `--clear-db`: Clear database before scraping
- `--export-detailed`: Export detailed match breakdown
- `--no-headless`: Show browser (for debugging)
- `--aggregate-only`: Skip scraping, only aggregate/export

## How It Works

### 1. Web Scraping

The scraper uses Playwright to:
1. Launch a headless Chromium browser
2. Navigate to each Overstat.gg URL
3. Wait for React components to render
4. Extract player/team statistics from tables
5. Save raw data to database

### 2. Weighting System

Each match score is weighted by:

**Weighted Score = Raw Score × Lobby Weight × Day Weight**

Example:
- Raw score: 50 points
- Lobby 2 weight: 0.80
- Day 3 weight: 1.35
- **Weighted score: 50 × 0.80 × 1.35 = 54.0**

### 3. Aggregation

For each player:
1. Sum all weighted scores across matches
2. Sum total kills and damage (unweighted)
3. Count matches played
4. Calculate averages

### 4. Export

Generates CSV files with:
- Player rankings by weighted score
- Total kills and damage
- Matches played
- Optional: Per-match breakdowns

## Output Files

### player_leaderboard_YYYYMMDD_HHMMSS.csv

```csv
Rank,Player Name,Total Points,Total Kills,Total Damage,Matches Played,Avg Points/Match
1,Anteater,1250.45,127,45678,12,104.20
2,LUMI,1198.32,119,43210,12,99.86
```

### summary_stats_YYYYMMDD_HHMMSS.txt

```
VESA LEAGUE PLAYER STATISTICS SUMMARY
================================================================

OVERVIEW
----------------------------------------------------------------
Total Players:           140
Total Matches Recorded:  1680
Total Kills:             15234
Total Damage:            5,678,901

TOP 10 PLAYERS
----------------------------------------------------------------
Rank  Player                   Points      Kills     Damage
1     Anteater                 1250.45     127       45,678
```

## Troubleshooting

### Issue: "We're sorry but apex-tourney-frontend doesn't work properly without JavaScript enabled"

This error means Playwright isn't waiting long enough for React to render.

**Solutions:**
1. Increase timeout in scraper (edit `src/scraper.py`)
2. Run with `--no-headless` to see what's happening
3. Check if URL is correct

### Issue: Empty or missing player data

The scraper may need adjustment for Overstat's HTML structure.

**Solutions:**
1. Run with `--no-headless` to debug
2. Check `output/debug_page.html` for the actual page structure
3. Adjust selectors in `src/scraper.py` (lines 93-105, 145-157)

### Issue: Playwright browser not installed

```bash
playwright install chromium
```

## Customization

### Adjusting Table Selectors

Edit `src/scraper.py` around line 93:

```python
possible_selectors = [
    "table tbody tr",              # Standard table
    ".your-custom-class tbody tr", # Add your selector
]
```

### Changing Weight Formulas

Edit `config/weights.json` or modify `src/weights.py` for custom calculations.

### Adding New Exports

Edit `src/exporter.py` to add new export formats or statistics.

## Development

### Running Tests

(Tests not yet implemented - coming soon!)

### Debugging

1. Use `--no-headless` to see browser
2. Check `output/debug_page.html` for page structure
3. Check `output/error_*.png` for screenshots of errors
4. Increase logging level in `main.py`

## Next Steps (Future Enhancements)

- [ ] Team-based seeding (Version 2)
- [ ] Season 11 player ratings integration
- [ ] Tier assignment system
- [ ] Automated scheduling for periodic scrapes
- [ ] Web dashboard for viewing results
- [ ] API for external access

## License

MIT License - feel free to modify and use for your league!

## Support

For issues or questions, please open an issue on GitHub or contact the league administrators.

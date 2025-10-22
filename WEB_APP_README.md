# VESA League Rating System - Web Dashboard

A Streamlit web application for viewing and managing VESA League S12 team divisions and ratings.

## Features

### 📊 Dashboard (Home)
- Season overview with key statistics
- Tier distribution visualization
- Division summary table

### 🎯 Divisions
- View all 7 divisions
- See teams ranked within each division
- Export division assignments to CSV

### 👥 Teams
- Browse all 140 teams
- Search by team name
- View team rosters with player ratings
- See tier and rating information

### 🎮 Player Search
- Search players by name (handles aliases)
- View individual player stats:
  - Total rating
  - Base rating
  - Lobby bonus percentage
- See which team they're on

### 📈 Analytics
- Team rating distribution histogram
- Division balance analysis
- Top 10 teams leaderboard

### ⚙️ Settings (Coming Soon)
- View current formula configuration
- Lobby bonus percentages
- Season weighting
- Scoring method

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the `vesa_league.db` database file in the same directory

## Running the App

### Local Development
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Production Deployment

#### Option 1: Streamlit Cloud (Recommended)
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy!

#### Option 2: Docker
```bash
docker build -t vesa-dashboard .
docker run -p 8501:8501 vesa-dashboard
```

## File Structure

```
vesa-scraper/
├── app.py                    # Main Streamlit app
├── vesa_league.db            # SQLite database
├── requirements.txt          # Python dependencies
├── RATING_FORMULA.md         # Formula documentation
└── output/
    ├── division_assignments_with_changes.csv
    └── division_summary.csv
```

## Database Schema

The app reads from the following main tables:
- `divisions` - Division information (number, day, season)
- `teams` - Team data (name, rating, tier)
- `players` - Player information (name, aliases)
- `player_ratings` - Individual player ratings and bonuses
- `team_rosters` - Team composition (3 players per team)
- `division_assignments` - Team placement in divisions

## Usage

### For Players (Read-Only)
- Browse divisions to see where your team is placed
- Search for your name to see your individual rating
- View your team's roster and combined rating
- Check out analytics and league-wide statistics

### For Admins
- View all divisions and assignments
- Export data to CSV for announcements
- (Future) Adjust formula parameters
- (Future) Re-calculate with new settings

## Future Features

- ✅ View divisions and teams
- ✅ Player search
- ✅ Export to CSV
- ✅ Charts and analytics
- ⏳ Interactive lobby bonus configuration
- ⏳ Real-time preview of setting changes
- ⏳ Discord export format
- ⏳ Comparison mode
- ⏳ Upload new season data via UI

## Technical Details

- **Framework**: Streamlit 1.28+
- **Database**: SQLite 3
- **Visualizations**: Plotly 5.17+
- **Data Processing**: Pandas 2.0+

## Support

For issues or questions:
1. Check the RATING_FORMULA.md for formula details
2. Review the database using SQLite tools
3. Contact league administrators

## License

Internal use for VESA League only.

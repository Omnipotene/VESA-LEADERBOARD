#!/usr/bin/env python3
"""
VESA League Player Statistics Scraper - Main Entry Point

This script orchestrates the entire scraping, aggregation, and export pipeline.

Usage:
    python main.py --urls config/urls.csv
    python main.py --urls config/urls.csv --export-detailed
    python main.py --clear-db  # Clear database before scraping
"""

import argparse
import csv
import sys
import logging
from pathlib import Path
from tqdm import tqdm

# Import our modules
from src.database import Database
from src.scraper import OverstatScraper
from src.weights import WeightingSystem
from src.aggregator import PlayerAggregator
from src.exporter import CSVExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_urls_from_csv(csv_path: str) -> list:
    """
    Load URLs and metadata from CSV file.

    Args:
        csv_path: Path to CSV file with columns: url, day, lobby, type, description

    Returns:
        List of dictionaries with URL metadata
    """
    urls = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append({
                'url': row['url'],
                'day': int(row['day']),
                'lobby': row['lobby'],
                'type': row['type'],
                'description': row.get('description', '')
            })
    return urls


def scrape_matches(urls: list, db: Database, headless: bool = True):
    """
    Scrape all matches from URL list.

    Args:
        urls: List of URL metadata dictionaries
        db: Database instance
        headless: Run browser in headless mode
    """
    logger.info(f"Starting scrape of {len(urls)} URLs")

    with OverstatScraper(headless=headless) as scraper:
        for url_data in tqdm(urls, desc="Scraping matches"):
            try:
                logger.info(f"Scraping: {url_data['description']}")

                # Scrape the URL
                stats = scraper.scrape_url(
                    url=url_data['url'],
                    data_type=url_data['type']
                )

                # Save match to database
                match_id = db.insert_match(
                    url=url_data['url'],
                    day=url_data['day'],
                    lobby=url_data['lobby'],
                    match_type=url_data['type'],
                    raw_data={'stats': stats}
                )

                # Save player stats
                for stat in stats:
                    db.insert_player_stat(
                        match_id=match_id,
                        player_name=stat['player_name'],
                        team_name=stat.get('team_name'),
                        score=stat['score'],
                        kills=stat['kills'],
                        damage=stat['damage'],
                        day=url_data['day'],
                        lobby=url_data['lobby'],
                        placement=stat.get('placement')
                    )

                logger.info(f"Saved {len(stats)} player records")

            except Exception as e:
                logger.error(f"Error scraping {url_data['url']}: {str(e)}")
                continue

    logger.info("Scraping complete")


def aggregate_and_export(db: Database, export_detailed: bool = False):
    """
    Aggregate player stats and export to CSV.

    Args:
        db: Database instance
        export_detailed: Export detailed match-by-match breakdown
    """
    logger.info("Starting aggregation and export...")

    # Initialize components
    weighting = WeightingSystem()
    aggregator = PlayerAggregator(db, weighting)
    exporter = CSVExporter()

    # Print weight configuration
    weighting.print_weight_table()

    # Aggregate all player stats
    aggregated = aggregator.aggregate_all_players()

    if not aggregated:
        logger.error("No player data to aggregate")
        return

    # Save to database
    aggregator.save_aggregated_stats(aggregated)

    # Sort by weighted score
    sorted_players = sorted(
        aggregated.values(),
        key=lambda x: x['total_weighted_score'],
        reverse=True
    )

    # Export to CSV
    csv_path = exporter.export_leaderboard(sorted_players)
    logger.info(f"Leaderboard exported to: {csv_path}")

    # Export detailed version if requested
    if export_detailed:
        detailed_path = exporter.export_detailed_leaderboard(sorted_players)
        logger.info(f"Detailed leaderboard exported to: {detailed_path}")

    # Export summary statistics
    summary_path = exporter.export_summary_stats(sorted_players)
    logger.info(f"Summary statistics exported to: {summary_path}")

    # Print top 10
    print("\n" + "="*70)
    print("TOP 10 PLAYERS")
    print("="*70)
    print(f"{'Rank':<6}{'Player':<25}{'Points':<12}{'Kills':<10}{'Damage':<12}{'Matches'}")
    print("-"*70)

    for rank, player in enumerate(sorted_players[:10], start=1):
        print(f"{rank:<6}{player['player_name']:<25}"
              f"{player['total_weighted_score']:<12.2f}"
              f"{player['total_kills']:<10}"
              f"{player['total_damage']:<12,}"
              f"{player['matches_played']}")

    print("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='VESA League Player Statistics Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --urls config/urls.csv
  python main.py --urls config/urls.csv --export-detailed
  python main.py --clear-db
  python main.py --urls config/urls.csv --no-headless  # Show browser
        """
    )

    parser.add_argument(
        '--urls',
        type=str,
        help='Path to CSV file containing URLs to scrape'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='data/vesa.db',
        help='Path to SQLite database (default: data/vesa.db)'
    )

    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear all data from database before scraping'
    )

    parser.add_argument(
        '--export-detailed',
        action='store_true',
        help='Export detailed match-by-match breakdown'
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Show browser window during scraping (for debugging)'
    )

    parser.add_argument(
        '--aggregate-only',
        action='store_true',
        help='Skip scraping, only aggregate existing data and export'
    )

    args = parser.parse_args()

    # Initialize database
    db = Database(args.db)

    # Clear database if requested
    if args.clear_db:
        logger.info("Clearing database...")
        db.clear_all_data()
        logger.info("Database cleared")

    # Scrape if URLs provided and not aggregate-only mode
    if args.urls and not args.aggregate_only:
        if not Path(args.urls).exists():
            logger.error(f"URL file not found: {args.urls}")
            sys.exit(1)

        urls = load_urls_from_csv(args.urls)
        scrape_matches(urls, db, headless=not args.no_headless)

    # Aggregate and export
    aggregate_and_export(db, export_detailed=args.export_detailed)

    # Close database
    db.close()

    logger.info("Pipeline complete!")


if __name__ == "__main__":
    main()

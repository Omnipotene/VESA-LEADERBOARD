"""
Overstat.gg web scraper using Playwright.
Handles both player-level and team-level statistics pages.
"""

from playwright.sync_api import sync_playwright, Page, Browser
from typing import List, Dict, Optional
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OverstatScraper:
    """Scrapes match data from Overstat.gg using Playwright."""

    def __init__(self, headless: bool = True, timeout: int = 60000, slow_mo: int = 0):
        """
        Initialize the scraper.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds (default 60s)
            slow_mo: Slow down operations by N milliseconds (useful for debugging)
        """
        self.headless = headless
        self.timeout = timeout
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None

    def __enter__(self):
        """Start Playwright and browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up Playwright resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def scrape_url(self, url: str, data_type: str) -> List[Dict]:
        """
        Scrape a single URL.

        Args:
            url: Overstat.gg URL to scrape
            data_type: "player" or "team" - determines parsing strategy

        Returns:
            List of player/team stat dictionaries
        """
        logger.info(f"Scraping {data_type} data from: {url}")

        page = self.browser.new_page()
        page.set_default_timeout(self.timeout)

        try:
            # Navigate to URL
            page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

            # Wait for the table to appear (more reliable than networkidle)
            logger.info("Waiting for table to load...")
            page.wait_for_selector("table tbody tr", timeout=self.timeout)

            # Give extra time for React components to fully render
            logger.info("Waiting for React to finish rendering...")
            time.sleep(5)

            # Try multiple selectors to find the data table
            stats_data = self._extract_stats(page, data_type)

            logger.info(f"Scraped {len(stats_data)} entries")
            return stats_data

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            # Save screenshot for debugging
            page.screenshot(path=f"output/error_{int(time.time())}.png")
            raise

        finally:
            page.close()

    def _extract_stats(self, page: Page, data_type: str) -> List[Dict]:
        """
        Extract statistics from the page.

        Args:
            page: Playwright page object
            data_type: "player" or "team"

        Returns:
            List of stat dictionaries
        """
        if data_type == "player":
            return self._extract_player_stats(page)
        elif data_type == "team":
            return self._extract_team_stats(page)
        else:
            raise ValueError(f"Invalid data_type: {data_type}")

    def _extract_player_stats(self, page: Page) -> List[Dict]:
        """
        Extract player-level statistics using JavaScript evaluation.

        This avoids DOM reference memory issues by extracting all data
        in a single JavaScript execution context.

        Returns:
            List of player stat dictionaries
        """
        # Wait for table to be present
        try:
            page.wait_for_selector("table tbody tr", timeout=10000)
        except:
            logger.warning("Table not found within timeout")
            return []

        # Extract all player data using JavaScript
        players = page.evaluate("""
            () => {
                const players = [];
                const rows = document.querySelectorAll('table tbody tr');

                rows.forEach((row) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 6) {
                        try {
                            players.push({
                                player_name: cells[1].innerText.trim(),
                                team_name: cells[2].innerText.trim(),
                                score: parseFloat(cells[3].innerText.replace(/,/g, '')) || 0,
                                kills: parseInt(cells[4].innerText.replace(/,/g, '')) || 0,
                                damage: parseInt(cells[5].innerText.replace(/,/g, '')) || 0
                            });
                        } catch (e) {
                            // Skip rows that can't be parsed
                        }
                    }
                });

                return players;
            }
        """)

        logger.info(f"Extracted {len(players)} players using JavaScript")
        return players

    def _extract_team_stats(self, page: Page) -> List[Dict]:
        """
        Extract team-level statistics and derive player stats.

        When only team stats are available, we need to:
        1. Get team totals (score, kills, damage)
        2. Divide by 3 to estimate per-player averages
        OR
        3. Try to find individual player breakdowns if available

        Returns:
            List of player stat dictionaries (estimated from team data)
        """
        teams = []

        # Find table rows
        possible_selectors = [
            "table tbody tr",
            ".scoreboard tbody tr",
            "[class*='scoreboard'] tbody tr",
            "[class*='table'] tbody tr",
        ]

        rows = None
        for selector in possible_selectors:
            rows = page.query_selector_all(selector)
            if rows and len(rows) > 0:
                logger.info(f"Found {len(rows)} rows using selector: {selector}")
                break

        if not rows:
            logger.warning("Could not find table rows")
            content = page.content()
            with open("output/debug_page.html", "w") as f:
                f.write(content)
            logger.info("Saved page HTML to output/debug_page.html")
            return []

        # Parse each row
        for row in rows:
            try:
                cells = row.query_selector_all("td")

                if len(cells) < 4:  # Need at least: rank, team, score, kills
                    continue

                # Typical team scoreboard:
                # Rank | Team | Total Score | Kills | Damage | Placement

                team_name = cells[1].inner_text().strip()
                total_score = self._parse_number(cells[2].inner_text()) if len(cells) > 2 else 0
                total_kills = self._parse_number(cells[3].inner_text()) if len(cells) > 3 else 0
                total_damage = self._parse_number(cells[4].inner_text()) if len(cells) > 4 else 0
                placement = self._parse_number(cells[5].inner_text()) if len(cells) > 5 else None

                teams.append({
                    "team_name": team_name,
                    "total_score": total_score,
                    "total_kills": total_kills,
                    "total_damage": total_damage,
                    "placement": placement
                })

            except Exception as e:
                logger.warning(f"Error parsing row: {str(e)}")
                continue

        # Now try to expand team stats to player stats
        # Check if there's a roster section or player breakdown
        player_stats = self._expand_team_to_players(page, teams)

        return player_stats

    def _expand_team_to_players(self, page: Page, teams: List[Dict]) -> List[Dict]:
        """
        Try to expand team stats into individual player stats.

        Strategy:
        1. Look for expandable rows or player details
        2. If found, extract player-specific stats
        3. If not found, create estimated player records (team_total / 3)

        Args:
            page: Playwright page
            teams: List of team stat dictionaries

        Returns:
            List of player stat dictionaries
        """
        players = []

        # TODO: This is a placeholder - actual implementation depends on
        # the specific HTML structure of Overstat's team pages

        # For now, we'll create placeholder entries for each team
        # In a real scenario, you might need to:
        # - Click on team rows to expand player details
        # - Navigate to team-specific pages
        # - Parse nested HTML structures

        for team in teams:
            # Create estimated player records
            # Note: This is a simplification - ideally we'd get actual player data
            for i in range(3):  # Assume 3 players per team
                players.append({
                    "player_name": f"{team['team_name']}_Player{i+1}",
                    "team_name": team['team_name'],
                    "score": team['total_score'] / 3,  # Estimate
                    "kills": team['total_kills'] // 3,  # Estimate
                    "damage": team['total_damage'] // 3,  # Estimate
                    "placement": team.get('placement'),
                    "is_estimated": True  # Flag for data quality
                })

        logger.warning(f"Team stats expanded to {len(players)} estimated player records")
        logger.warning("Consider using player-specific URLs for accurate data")

        return players

    @staticmethod
    def _parse_number(text: str) -> float:
        """
        Parse a number from text, handling commas and various formats.

        Args:
            text: String containing a number

        Returns:
            Parsed number as float
        """
        try:
            # Remove commas, spaces, and other non-numeric characters
            cleaned = text.replace(",", "").replace(" ", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0

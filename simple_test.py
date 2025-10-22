#!/usr/bin/env python3
"""
Simple scraper test - saves HTML to file for inspection
"""

from playwright.sync_api import sync_playwright
import time

url = "https://overstat.gg/tournament/VESA%20League/13938.VESA_S11_Pinnacle_I_all_weeks_/standings/overall/player-standings"

print(f"Loading URL: {url}")
print("Opening browser (visible mode)...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Visible browser
    page = browser.new_page()

    print("Navigating to page...")
    page.goto(url, timeout=60000)

    print("Waiting for page to load...")
    page.wait_for_load_state("networkidle", timeout=60000)

    print("Waiting extra 5 seconds for React...")
    time.sleep(5)

    # Save HTML
    html = page.content()
    with open("output/page_source.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved HTML to output/page_source.html")

    # Take screenshot
    page.screenshot(path="output/screenshot.png")
    print("Saved screenshot to output/screenshot.png")

    #Try to find table
    print("\nLooking for tables...")
    tables = page.query_selector_all("table")
    print(f"Found {len(tables)} table elements")

    if tables:
        print("\nTrying to extract data from first table...")
        rows = tables[0].query_selector_all("tbody tr")
        print(f"Found {len(rows)} rows in tbody")

        if rows and len(rows) > 0:
            print("\nFirst row cells:")
            cells = rows[0].query_selector_all("td, th")
            for i, cell in enumerate(cells):
                print(f"  Cell {i}: {cell.inner_text()[:50]}")

    print("\nBrowser will stay open for 30 seconds for you to inspect...")
    time.sleep(30)

    browser.close()
    print("Done!")

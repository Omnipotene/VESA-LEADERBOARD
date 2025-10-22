#!/usr/bin/env python3
"""
Headless test - runs without opening a browser window
"""

import sys
import traceback
import time

print("Starting headless test (no browser window will open)...")

try:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        print("Launching browser in headless mode...")
        browser = p.chromium.launch(headless=True)

        print("Creating page...")
        page = browser.new_page()

        print("Navigating to Overstat...")
        url = "https://overstat.gg/tournament/VESA%20League/13938.VESA_S11_Pinnacle_I_all_weeks_/standings/overall/player-standings"
        page.goto(url, timeout=60000)

        print("Waiting for page to load...")
        page.wait_for_load_state("networkidle", timeout=60000)

        print("Waiting for React to render...")
        time.sleep(3)

        print("Taking screenshot...")
        page.screenshot(path="output/headless_screenshot.png", full_page=True)

        print("Saving HTML...")
        html = page.content()
        with open("output/headless_page.html", "w", encoding="utf-8") as f:
            f.write(html)

        print(f"HTML saved: {len(html)} bytes")

        print("\nLooking for tables...")
        tables = page.query_selector_all("table")
        print(f"Found {len(tables)} table(s)")

        if tables:
            rows = tables[0].query_selector_all("tbody tr")
            print(f"Found {len(rows)} rows in first table")

            if rows:
                print("\nFirst 3 rows:")
                for i, row in enumerate(rows[:3]):
                    cells = row.query_selector_all("td, th")
                    print(f"\nRow {i+1}:")
                    for j, cell in enumerate(cells[:8]):  # First 8 cells
                        text = cell.inner_text().strip()
                        print(f"  Cell {j}: {text[:40]}")

        print("\nClosing browser...")
        browser.close()

        print("\n✅ SUCCESS!")
        print("Check these files:")
        print("  - output/headless_screenshot.png")
        print("  - output/headless_page.html")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python3
"""
Debug version - more error handling and diagnostics
"""

import sys
import traceback

print("Starting debug test...")
print(f"Python version: {sys.version}")

try:
    print("\n1. Importing playwright...")
    from playwright.sync_api import sync_playwright
    print("   ✓ Playwright imported successfully")

    print("\n2. Starting playwright...")
    playwright = sync_playwright().start()
    print("   ✓ Playwright started")

    print("\n3. Launching browser...")
    browser = playwright.chromium.launch(
        headless=False,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled'
        ]
    )
    print("   ✓ Browser launched")

    print("\n4. Creating new page...")
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    print("   ✓ Page created")

    print("\n5. Navigating to URL...")
    url = "https://overstat.gg/tournament/VESA%20League/13938.VESA_S11_Pinnacle_I_all_weeks_/standings/overall/player-standings"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    print("   ✓ Navigation complete")

    print("\n6. Waiting for network to be idle...")
    page.wait_for_load_state("networkidle", timeout=60000)
    print("   ✓ Network idle")

    print("\n7. Waiting 3 seconds for React to render...")
    import time
    time.sleep(3)
    print("   ✓ Wait complete")

    print("\n8. Taking screenshot...")
    page.screenshot(path="output/debug_screenshot.png", full_page=True)
    print("   ✓ Screenshot saved to output/debug_screenshot.png")

    print("\n9. Saving HTML...")
    html = page.content()
    with open("output/debug_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"   ✓ HTML saved to output/debug_page.html ({len(html)} bytes)")

    print("\n10. Looking for tables...")
    tables = page.query_selector_all("table")
    print(f"   ✓ Found {len(tables)} table(s)")

    if tables:
        print("\n11. Analyzing first table...")
        rows = tables[0].query_selector_all("tbody tr")
        print(f"   ✓ Found {len(rows)} row(s) in first table")

        if len(rows) > 0:
            print("\n12. First row analysis:")
            first_row = rows[0]
            cells = first_row.query_selector_all("td, th")
            print(f"   ✓ First row has {len(cells)} cell(s)")

            for i, cell in enumerate(cells[:10]):  # First 10 cells
                text = cell.inner_text().strip()
                print(f"      Cell {i}: '{text[:50]}'")

    print("\n13. Keeping browser open for 10 seconds...")
    print("   (You can inspect the page now)")
    time.sleep(10)

    print("\n14. Closing browser...")
    browser.close()
    playwright.stop()
    print("   ✓ Browser closed cleanly")

    print("\n✅ SUCCESS! All steps completed.")
    print("\nNext steps:")
    print("  1. Check output/debug_screenshot.png to see the page")
    print("  2. Check output/debug_page.html to see the HTML structure")

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user")
    sys.exit(0)

except Exception as e:
    print(f"\n\n❌ ERROR at current step:")
    print(f"   {type(e).__name__}: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("  1. Make sure Chrome is not already running")
    print("  2. Try running: playwright install chromium --with-deps")
    print("  3. Check if you have permissions to launch applications")
    sys.exit(1)

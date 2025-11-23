#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "playwright>=1.40.0",
# ]
# ///
"""
Explore Jobber Developer Portal to understand OAuth app configuration.

Captures screenshots and inspects DOM structure.
"""

from playwright.sync_api import sync_playwright
import json

def explore_jobber_portal():
    """Navigate to Jobber Developer Portal and capture information."""

    print("=== Jobber Developer Portal Exploration ===\n")

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        # Enable console logging
        console_messages = []
        page.on('console', lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

        try:
            # URL 1: Apps listing page
            print("1. Navigating to https://developer.getjobber.com/apps")
            page.goto('https://developer.getjobber.com/apps', wait_until='networkidle')
            page.wait_for_timeout(2000)  # Wait for dynamic content

            # Take screenshot
            screenshot_path = '/tmp/jobber_apps_listing.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"   ✅ Screenshot saved: {screenshot_path}")

            # Get page title
            title = page.title()
            print(f"   Page title: {title}")

            # Check if login required
            if 'login' in page.url.lower() or 'sign in' in title.lower():
                print("   ⚠️  Login required - capturing login page")
                login_screenshot = '/tmp/jobber_login.png'
                page.screenshot(path=login_screenshot, full_page=True)
                print(f"   ✅ Login screenshot: {login_screenshot}")

                # Inspect login form
                print("\n   Login form elements:")
                email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first
                if email_input.count() > 0:
                    print(f"   - Email field found: {email_input.get_attribute('name') or email_input.get_attribute('id')}")

                password_input = page.locator('input[type="password"]').first
                if password_input.count() > 0:
                    print(f"   - Password field found: {password_input.get_attribute('name') or password_input.get_attribute('id')}")

                submit_button = page.locator('button[type="submit"], input[type="submit"]').first
                if submit_button.count() > 0:
                    button_text = submit_button.text_content() or submit_button.get_attribute('value')
                    print(f"   - Submit button: '{button_text}'")
            else:
                print("   ✅ No login required - inspecting apps page")

                # Look for app cards/links
                print("\n   App elements found:")
                apps = page.locator('[class*="app" i], [id*="app" i]').all()
                print(f"   - Found {len(apps)} elements with 'app' in class/id")

                # Look for headings
                headings = page.locator('h1, h2, h3').all()
                for i, h in enumerate(headings[:5]):
                    text = h.text_content().strip()
                    if text:
                        print(f"   - Heading {i+1}: {text}")

            print()

            # URL 2: Specific app page
            print("2. Navigating to https://developer.getjobber.com/apps/MTI3NTIw")
            page.goto('https://developer.getjobber.com/apps/MTI3NTIw', wait_until='networkidle')
            page.wait_for_timeout(2000)

            # Take screenshot
            screenshot_path = '/tmp/jobber_app_detail.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"   ✅ Screenshot saved: {screenshot_path}")

            # Get page title
            title = page.title()
            print(f"   Page title: {title}")

            # Check if login required
            if 'login' in page.url.lower() or 'sign in' in title.lower():
                print("   ⚠️  Login required for app details")
            else:
                print("   ✅ App details accessible")

                # Look for OAuth credentials
                print("\n   OAuth-related elements:")

                # Search for client ID
                client_id_elements = page.locator('text=/client.{0,5}id/i').all()
                print(f"   - Found {len(client_id_elements)} 'Client ID' mentions")

                # Search for client secret
                secret_elements = page.locator('text=/client.{0,5}secret/i').all()
                print(f"   - Found {len(secret_elements)} 'Client Secret' mentions")

                # Search for redirect URI
                redirect_elements = page.locator('text=/redirect.{0,10}uri/i').all()
                print(f"   - Found {len(redirect_elements)} 'Redirect URI' mentions")

                # Look for form inputs
                inputs = page.locator('input[type="text"], input[type="url"]').all()
                print(f"\n   Form inputs found: {len(inputs)}")
                for i, inp in enumerate(inputs[:10]):
                    name = inp.get_attribute('name') or inp.get_attribute('id') or inp.get_attribute('placeholder')
                    print(f"   - Input {i+1}: {name}")

                # Look for buttons
                buttons = page.locator('button').all()
                print(f"\n   Buttons found: {len(buttons)}")
                for i, btn in enumerate(buttons[:10]):
                    text = btn.text_content().strip()
                    if text:
                        print(f"   - Button {i+1}: {text}")

            print()

            # Console messages
            if console_messages:
                print("3. Console Messages:")
                for msg in console_messages[:20]:
                    print(f"   {msg}")
            else:
                print("3. No console messages captured")

            print()

            # Page HTML structure (first 2000 chars)
            print("4. Page HTML Structure Preview:")
            html = page.content()
            print(f"   Total HTML length: {len(html)} characters")
            print(f"   First 2000 characters:")
            print(f"   {html[:2000]}")

            # Save full HTML for inspection
            html_path = '/tmp/jobber_app_detail.html'
            with open(html_path, 'w') as f:
                f.write(html)
            print(f"\n   ✅ Full HTML saved: {html_path}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

    print("\n=== Exploration Complete ===")
    print("\nScreenshots captured:")
    print("  - /tmp/jobber_apps_listing.png")
    print("  - /tmp/jobber_app_detail.png")
    print("  - /tmp/jobber_login.png (if login required)")
    print("\nHTML saved:")
    print("  - /tmp/jobber_app_detail.html")

if __name__ == '__main__':
    explore_jobber_portal()

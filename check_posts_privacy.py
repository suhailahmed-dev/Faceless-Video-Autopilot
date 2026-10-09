import time
from playwright.sync_api import sync_playwright
import config

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"

def check_posts():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(TIKTOK_SESSION_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.tiktok.com/tiktokstudio/content", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6)
        
        # Check if privacy dropdown can be set to Public / Everyone
        privacy_btn = page.locator("div:has-text('Only me'), button:has-text('Only me')").first
        if privacy_btn.count() > 0:
            print("[TIKTOK] Found 'Only me' privacy button, checking options...")
            privacy_btn.click()
            time.sleep(1)
            page.screenshot(path="tiktok_privacy_menu.png")
            everyone_opt = page.locator("div:has-text('Everyone'), li:has-text('Everyone'), span:has-text('Everyone')").first
            if everyone_opt.count() > 0:
                print("[TIKTOK] Selecting 'Everyone'...")
                everyone_opt.click()
                time.sleep(2)
                # Confirm modal if any
                confirm_btn = page.locator("button:has-text('Confirm'), button:has-text('Save'), button:has-text('Update')")
                if confirm_btn.count() > 0:
                    confirm_btn.first.click()
                    time.sleep(2)

        page.screenshot(path="tiktok_posts_live.png")
        print("[TIKTOK] Saved tiktok_posts_live.png")
        context.close()

if __name__ == "__main__":
    check_posts()

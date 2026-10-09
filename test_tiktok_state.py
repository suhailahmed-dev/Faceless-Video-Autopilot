import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"

def test_session():
    print("[TEST] Launching Edge to test TikTok session...")
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
        
        # 1. Check main page
        print("[TEST] Navigating to https://www.tiktok.com ...")
        page.goto("https://www.tiktok.com", timeout=60000, wait_until="domcontentloaded")
        time.sleep(8)
        
        print(f"[TEST] Current URL: {page.url}")
        print(f"[TEST] Page Title: {page.title()}")
        page.screenshot(path="test_tiktok_main.png")
        print("[TEST] Saved test_tiktok_main.png")
        
        # Check cookies
        cookies = context.cookies()
        session_cookies = [c['name'] for c in cookies if 'tiktok' in c.get('domain', '')]
        print(f"[TEST] TikTok cookies found: {len(session_cookies)} ({session_cookies[:5]})")
        
        has_sessionid = any(c['name'] == 'sessionid' for c in cookies)
        print(f"[TEST] Has 'sessionid' cookie (Login indicator): {has_sessionid}")
        
        # 2. Check upload page
        print("[TEST] Navigating to upload page...")
        page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000, wait_until="domcontentloaded")
        time.sleep(8)
        print(f"[TEST] Upload URL: {page.url}")
        print(f"[TEST] Upload Title: {page.title()}")
        page.screenshot(path="test_tiktok_upload.png")
        print("[TEST] Saved test_tiktok_upload.png")
        
        context.close()

if __name__ == "__main__":
    test_session()

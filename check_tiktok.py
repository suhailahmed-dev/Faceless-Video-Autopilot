import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"
SCREENSHOT_PATH = config.BASE_DIR / "tiktok_diagnostic.png"

def check_tiktok_posts():
    print("[DIAGNOSTIC] Checking TikTok content status...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(TIKTOK_SESSION_DIR),
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            print("[DIAGNOSTIC] Navigating to TikTok Creator Center content manager...")
            page.goto("https://www.tiktok.com/creator-center/content", timeout=60000, wait_until="domcontentloaded")
            time.sleep(6)
            
            current_url = page.url
            print(f"[DIAGNOSTIC] Current URL: {current_url}")
            
            # Save screenshot
            page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            print(f"[DIAGNOSTIC] Screenshot saved to: {SCREENSHOT_PATH}")
            
            # Check draft / published elements
            content_text = page.inner_text("body")
            has_drafts = "Draft" in content_text or "draft" in content_text
            has_posts = "Post" in content_text
            print(f"[DIAGNOSTIC] Page text sample: {content_text[:300].strip()}")
            print(f"[DIAGNOSTIC] Drafts mentioned: {has_drafts}, Posts mentioned: {has_posts}")

            context.close()
            return {"url": current_url, "screenshot": str(SCREENSHOT_PATH)}
        except Exception as e:
            print(f"[DIAGNOSTIC] Error: {e}")
            context.close()
            return {"error": str(e)}

if __name__ == "__main__":
    res = check_tiktok_posts()
    print("RESULT:", res)

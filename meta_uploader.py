import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

META_SESSION_DIR = config.BASE_DIR / ".meta_session"

def upload_instagram_reel(video_path: Path, caption: str) -> dict:
    """
    Automates uploading a Reel directly to Instagram via Playwright.
    """
    if not video_path.exists():
        return {"status": "error", "error": f"Video not found: {video_path}"}

    print(f"\n[INSTAGRAM] Starting Instagram Reel upload: {video_path.name}", flush=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(META_SESSION_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            print("[INSTAGRAM] Navigating to Instagram...", flush=True)
            page.goto("https://www.instagram.com/", timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
            
            # Check if logged in
            if "/accounts/login" in page.url or "login" in page.url:
                context.close()
                return {"status": "error", "error": "Instagram session not logged in. Run meta_login.py first."}

            print("[INSTAGRAM] Logged in! Finding 'Create' button...", flush=True)
            # Find Create button (sidebar)
            create_btn = page.locator("svg[aria-label='New post'], span:has-text('Create'), a:has-text('Create')")
            if create_btn.count() > 0:
                create_btn.first.click()
                time.sleep(3)
            else:
                page.goto("https://www.instagram.com/create/select/", timeout=30000)
                time.sleep(3)
                
            # File chooser
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                print(f"[INSTAGRAM] Setting video file: {video_path.name}", flush=True)
                file_input.first.set_input_files(str(video_path))
                time.sleep(6)
                
                # Check for "Post as reel" modal / "OK" button
                ok_btn = page.locator("button:has-text('OK'), button:has-text('Discard')")
                if ok_btn.count() > 0 and ok_btn.first.is_visible():
                    if "OK" in ok_btn.first.inner_text():
                        ok_btn.first.click()
                        time.sleep(2)
                
                # Next button (crop screen)
                next_btn = page.locator("div[role='button']:has-text('Next'), button:has-text('Next')")
                if next_btn.count() > 0 and next_btn.first.is_visible():
                    next_btn.first.click()
                    time.sleep(3)
                    
                # Next button (filter screen)
                next_btn = page.locator("div[role='button']:has-text('Next'), button:has-text('Next')")
                if next_btn.count() > 0 and next_btn.first.is_visible():
                    next_btn.first.click()
                    time.sleep(3)
                    
                # Fill caption
                caption_area = page.locator("div[aria-label='Write a caption...'], div[contenteditable='true']").first
                if caption_area.count() > 0:
                    caption_area.fill(caption[:2000])
                    print("[INSTAGRAM] Caption & hashtags inserted.", flush=True)
                    time.sleep(2)
                    
                # Share button
                share_btn = page.locator("div[role='button']:has-text('Share'), button:has-text('Share')")
                if share_btn.count() > 0 and share_btn.first.is_visible():
                    share_btn.first.click()
                    print("[INSTAGRAM] Clicked 'Share'! Waiting for processing...", flush=True)
                    time.sleep(15)
                    
                    proof_path = config.BASE_DIR / "instagram_published_proof.png"
                    page.screenshot(path=str(proof_path))
                    print(f"[INSTAGRAM] ✅ Reel shared successfully! Proof: {proof_path}", flush=True)
                    context.close()
                    return {"status": "success", "platform": "instagram", "proof": str(proof_path)}
                    
            context.close()
            return {"status": "error", "error": "Could not locate file uploader on Instagram."}
        except Exception as e:
            context.close()
            return {"status": "error", "error": str(e)}

def upload_facebook_reel(video_path: Path, caption: str) -> dict:
    """
    Automates uploading a Reel to Facebook via Facebook Reels Creator.
    """
    if not video_path.exists():
        return {"status": "error", "error": f"Video not found: {video_path}"}

    print(f"\n[FACEBOOK] Starting Facebook Reel upload: {video_path.name}", flush=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(META_SESSION_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            print("[FACEBOOK] Navigating to Facebook Reels composer...", flush=True)
            page.goto("https://www.facebook.com/reel/create", timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
            
            # Check login
            if "/login" in page.url:
                context.close()
                return {"status": "error", "error": "Facebook session not logged in. Run meta_login.py first."}

            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                print(f"[FACEBOOK] Uploading video file: {video_path.name}", flush=True)
                file_input.first.set_input_files(str(video_path))
                time.sleep(8)
                
                # Caption area
                desc_input = page.locator("div[role='textbox'], textarea").first
                if desc_input.count() > 0:
                    desc_input.fill(caption[:2000])
                    print("[FACEBOOK] Storytelling caption inserted.", flush=True)
                    time.sleep(2)
                    
                # Next button
                next_btns = page.locator("div[aria-label='Next'], button:has-text('Next')")
                for _ in range(2):
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        
                # Publish button
                pub_btn = page.locator("div[aria-label='Publish'], button:has-text('Publish')")
                if pub_btn.count() > 0 and pub_btn.first.is_visible():
                    pub_btn.first.click()
                    print("[FACEBOOK] ✅ Clicked 'Publish'! Processing Reel...", flush=True)
                    time.sleep(12)
                    
                    proof_path = config.BASE_DIR / "facebook_published_proof.png"
                    page.screenshot(path=str(proof_path))
                    context.close()
                    return {"status": "success", "platform": "facebook", "proof": str(proof_path)}

            context.close()
            return {"status": "error", "error": "Could not locate file input on Facebook."}
        except Exception as e:
            context.close()
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print("Meta Uploader Ready.")

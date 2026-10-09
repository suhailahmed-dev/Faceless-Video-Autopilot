import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"
VIDEO_PATH = Path(r"C:\Users\nasee\Desktop\faceless_video_bot\output_videos\2026-09-25\video_1_How_High-Value_People_Speak_3_Rules\final_video_1.mp4")
CAPTION = "Yeh 3 vocal rules kisi ko bhi respect lene par majboor kar dete hain! #fyp #psychology #lifehacks #mindset #viral"

def upload_flow():
    print(f"[TIKTOK] Starting upload flow for: {VIDEO_PATH.name}")
    if not VIDEO_PATH.exists():
        print(f"[ERROR] Video file does not exist at {VIDEO_PATH}")
        return

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

        try:
            print("[TIKTOK] Navigating to https://www.tiktok.com/tiktokstudio/upload ...")
            page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
            
            # Check login
            if "login" in page.url:
                print(f"[ERROR] Redirected to login: {page.url}")
                page.screenshot(path="tiktok_error_login.png")
                context.close()
                return

            print(f"[TIKTOK] Current Page Title: {page.title()} | URL: {page.url}")

            # Find file input
            print("[TIKTOK] Finding file input...")
            file_input = page.locator("input[type='file']")
            if file_input.count() == 0:
                # Search frames
                for f in page.frames:
                    fi = f.locator("input[type='file']")
                    if fi.count() > 0:
                        file_input = fi
                        break
            
            if file_input.count() == 0:
                print("[ERROR] No input[type='file'] found!")
                page.screenshot(path="tiktok_error_no_input.png")
                context.close()
                return

            print(f"[TIKTOK] Setting video file: {VIDEO_PATH}")
            file_input.first.set_input_files(str(VIDEO_PATH))

            # Wait for upload & editor screen to load
            print("[TIKTOK] Waiting 12 seconds for video processing & form loading...")
            time.sleep(12)
            page.screenshot(path="tiktok_step1_uploaded.png")
            print("[TIKTOK] Saved tiktok_step1_uploaded.png")

            # Look for caption input
            print("[TIKTOK] Finding caption field...")
            # Look for common caption inputs in TikTok Studio:
            # Often .public-DraftEditor-content, or div[contenteditable="true"], or textarea
            caption_elem = page.locator(".public-DraftEditor-content, div[contenteditable='true'], textarea, [data-text='true']").first
            if caption_elem.count() > 0:
                print("[TIKTOK] Caption element found. Setting caption...")
                caption_elem.click()
                time.sleep(1)
                # Select all and delete default file name
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                time.sleep(1)
                caption_elem.fill(CAPTION)
                time.sleep(2)
            else:
                print("[TIKTOK] Caption element not found via selectors, checking all text inputs...")

            page.screenshot(path="tiktok_step2_caption.png")
            print("[TIKTOK] Saved tiktok_step2_caption.png")

            # Wait for Post button to become active
            print("[TIKTOK] Looking for Post button...")
            # In TikTok Studio, Post button might say "Post"
            for attempt in range(12):
                post_btns = page.locator("button:has-text('Post'), div[role='button']:has-text('Post')")
                count = post_btns.count()
                print(f"[TIKTOK] Attempt {attempt+1}: found {count} 'Post' buttons")
                if count > 0:
                    btn = post_btns.first
                    is_disabled = btn.get_attribute("disabled") is not None or "disabled" in (btn.get_attribute("class") or "")
                    print(f"[TIKTOK] Button disabled status: {is_disabled}")
                    if not is_disabled:
                        print("[TIKTOK] Post button is ACTIVE! Clicking Post...")
                        btn.click()
                        time.sleep(6)
                        page.screenshot(path="tiktok_step3_posted.png")
                        print("[TIKTOK] Clicked Post! Saved tiktok_step3_posted.png")
                        break
                time.sleep(4)

            # Wait another 8s to confirm redirect or modal
            time.sleep(8)
            page.screenshot(path="tiktok_final_result.png")
            print(f"[TIKTOK] Final URL: {page.url}")
            print("[TIKTOK] Saved tiktok_final_result.png")

            # Check if modal "Manage your posts" appeared or redirected
            content = page.content()
            if "Manage your posts" in content or "Your video has been uploaded" in content or "uploaded" in content.lower():
                print("🎉 SUCCESS: Video has been published to TikTok!")
            else:
                print("[TIKTOK] Upload completed. Check screenshots for visual verification.")

        except Exception as e:
            print(f"[ERROR] Exception during TikTok upload: {e}")
            page.screenshot(path="tiktok_exception.png")
        finally:
            context.close()

if __name__ == "__main__":
    upload_flow()

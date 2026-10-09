import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

# Ensure UTF-8 output encoding for Windows command line
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"
TIKTOK_SESSION_DIR.mkdir(parents=True, exist_ok=True)

def login_tiktok():
    """
    Opens a visible browser for the user to log in to TikTok once.
    Cookies are permanently saved in TIKTOK_SESSION_DIR.
    """
    print("=" * 60)
    print("        TIKTOK ONE-TIME LOGIN SETUP")
    print("=" * 60)
    print("Browser khul raha hai... Apna TikTok account sign in karein.")
    print("Sign in hone ke baad is command window mein ENTER dabayein.")
    print("=" * 60)

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
        page.goto("https://www.tiktok.com/login", timeout=60000, wait_until="domcontentloaded")
        
        input("\n[?] TikTok login mukammal karne ke baad yahan ENTER dabayein: ")
        print("Login session save ho gaya! Window close ho rahi hai...")
        context.close()
        print("[SUCCESS] TikTok login session permanently saved!")

def upload_tiktok_video(video_path: Path, caption: str) -> dict:
    """
    Uploads a vertical video directly to TikTok Studio via Playwright with complete
    modal dismissal, Joyride handling, initial Post click, and final 'Post now' confirmation.
    """
    if not video_path.exists():
        return {"status": "error", "error": f"Video not found: {video_path}"}

    print(f"\n[TIKTOK] Starting autonomous TikTok upload: {video_path.name}")

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
            print("[TIKTOK] Opening TikTok Studio upload portal...")
            page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000, wait_until="domcontentloaded")

            # 1. Wait for Select video button
            print("[TIKTOK] Waiting for upload button to mount...")
            select_btn = None
            for sec in range(35):
                b = page.locator("button:has-text('Select video'), div[role='button']:has-text('Select video')")
                if b.count() > 0:
                    select_btn = b.first
                    break
                for f in page.frames:
                    b_frame = f.locator("button:has-text('Select video'), div[role='button']:has-text('Select video')")
                    if b_frame.count() > 0:
                        select_btn = b_frame.first
                        break
                if select_btn:
                    break
                time.sleep(1)

            # Check if redirected to login
            if "login" in page.url:
                print("[TIKTOK] Session expired or not logged in! Run 'login_tiktok.bat' first.")
                context.close()
                return {"status": "error", "error": "Not logged in. Please run login_tiktok.bat first."}

            if not select_btn:
                context.close()
                return {"status": "error", "error": "Could not find 'Select video' button on TikTok Studio."}

            # 2. Select file via file chooser
            print(f"[TIKTOK] Selecting video file: {video_path.name}...")
            with page.expect_file_chooser(timeout=20000) as fc_info:
                select_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(video_path))
            print("[TIKTOK] Video file sent to TikTok!")

            # 3. Wait for video upload to process & dismiss popups
            print("[TIKTOK] Waiting for video processing and dialogs...")
            time.sleep(8)

            # Dismiss Content checks modal ("Turn on")
            turn_on = page.locator("button:has-text('Turn on')")
            if turn_on.count() > 0:
                print("[TIKTOK] Dismissing Content checks modal...")
                turn_on.first.click()
                time.sleep(2)

            # Dismiss Joyride onboarding modal ("Got it")
            got_it = page.locator("button:has-text('Got it')")
            if got_it.count() > 0:
                print("[TIKTOK] Dismissing 'Got it' Joyride onboarding...")
                got_it.first.click()
                time.sleep(2)

            # Clean any leftover Joyride overlays from DOM
            page.evaluate("""() => {
                document.querySelectorAll('#react-joyride-portal, .react-joyride__overlay, div[data-test-id="overlay"]').forEach(el => el.remove());
            }""")
            time.sleep(1)

            # 4. Fill Caption
            print("[TIKTOK] Scrolling to top and entering caption...")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)

            caption_box = page.locator(".public-DraftEditor-content, div[contenteditable='true'], textarea").first
            if caption_box.count() > 0:
                caption_box.click(force=True)
                time.sleep(1)
                page.keyboard.press("Control+A")
                time.sleep(0.3)
                page.keyboard.press("Backspace")
                time.sleep(0.3)
                page.keyboard.type(caption[:2000], delay=15)
                time.sleep(1)
                # Press Escape to close any hashtag suggestion popup
                page.keyboard.press("Escape")
                print("[TIKTOK] Caption entered and hashtag popup dismissed!")
                time.sleep(2)

            # 5. Scroll to bottom and locate initial Post button
            print("[TIKTOK] Scrolling to Post button...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Extra cleanup of any joyride overlay
            page.evaluate("""() => {
                document.querySelectorAll('#react-joyride-portal, .react-joyride__overlay, div[data-test-id="overlay"]').forEach(el => el.remove());
            }""")

            posted = False
            for attempt in range(25):
                post_btns = page.locator("button:has-text('Post'), div[role='button']:has-text('Post')")
                count = post_btns.count()
                for i in range(count):
                    btn = post_btns.nth(i)
                    txt = btn.inner_text().strip()
                    if txt == "Post":
                        disabled = btn.get_attribute("disabled")
                        cls = btn.get_attribute("class") or ""
                        if disabled is None and "disabled" not in cls.lower():
                            print(f"[TIKTOK] Initial Post button active! Clicking Post now (attempt {attempt+1})...")
                            btn.click(force=True)
                            posted = True
                            break
                if posted:
                    break
                time.sleep(2)

            if not posted:
                context.close()
                return {"status": "error", "error": "Post button did not become active in time."}

            # 6. Check for confirmation modal: "Post now" / "Continue to post?"
            print("[TIKTOK] Checking for secondary 'Post now' confirmation modal...")
            time.sleep(3)
            post_now_clicked = False
            for _ in range(10):
                post_now_btn = page.locator("button:has-text('Post now'), div[role='button']:has-text('Post now')")
                if post_now_btn.count() > 0:
                    print("[TIKTOK] 'Post now' confirmation modal found! Clicking 'Post now'...")
                    post_now_btn.first.click(force=True)
                    post_now_clicked = True
                    break
                time.sleep(1)

            if not post_now_clicked:
                print("[TIKTOK] No secondary 'Post now' modal appeared (or check completed already).")

            # 7. Wait for final redirection / "Manage your posts" / uploaded confirmation
            print("[TIKTOK] Waiting for publication confirmation...")
            time.sleep(10)
            
            # Capture final proof screenshot
            proof_path = config.BASE_DIR / "tiktok_published_proof.png"
            page.screenshot(path=str(proof_path))
            print(f"[TIKTOK] Final proof screenshot saved: {proof_path}")

            # Check page state
            body_text = page.inner_text("body")
            success_indicators = ["Manage your posts", "Upload another video", "Your video has been uploaded", "uploaded"]
            is_success = any(ind.lower() in body_text.lower() for ind in success_indicators) or "content" in page.url or "manage" in page.url

            context.close()
            return {
                "status": "success",
                "message": "Video successfully published to TikTok!",
                "proof": str(proof_path),
                "verified": is_success
            }

        except Exception as e:
            print(f"[TIKTOK] Upload error: {e}")
            context.close()
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--login":
        login_tiktok()
    elif len(sys.argv) > 2 and sys.argv[1] == "--upload":
        v_file = Path(sys.argv[2])
        cap = sys.argv[3] if len(sys.argv) > 3 else "High Value Psychology #Shorts #fyp"
        res = upload_tiktok_video(v_file, cap)
        print("RESULT:", res)
    else:
        print("Usage:")
        print("  python tiktok_uploader.py --login")
        print("  python tiktok_uploader.py --upload <video_path> <caption_text>")

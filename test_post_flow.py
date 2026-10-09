import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"
VIDEO_PATH = Path(r"C:\Users\nasee\Desktop\faceless_video_bot\output_videos\2026-09-25\video_1_How_High-Value_People_Speak_3_Rules\final_video_1.mp4")
CAPTION = "Yeh 3 vocal rules kisi ko bhi respect dene par majboor kar dete hain! 🧠 #fyp #psychology #lifehacks #mindset #viral #shorts"

def run_upload_and_post():
    print(f"[TIKTOK] Starting robust upload for: {VIDEO_PATH.name}")
    if not VIDEO_PATH.exists():
        print(f"[ERROR] Video file not found: {VIDEO_PATH}")
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

            # 1. Wait for Select video button
            print("[TIKTOK] Waiting for upload button...")
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

            if not select_btn:
                print("[ERROR] Timeout waiting for 'Select video' button!")
                return

            # 2. Select file via file chooser
            print(f"[TIKTOK] Triggering file chooser for {VIDEO_PATH.name}...")
            with page.expect_file_chooser(timeout=15000) as fc_info:
                select_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(VIDEO_PATH))
            print("[TIKTOK] Video file selected! Waiting for editor to mount...")

            # 3. Dismiss initial popups & Joyride overlays
            time.sleep(8)
            print("[TIKTOK] Handling onboarding dialogs and Joyride...")

            # Click Turn on if exists
            turn_on = page.locator("button:has-text('Turn on')")
            if turn_on.count() > 0:
                print("[TIKTOK] Dismissing Content checks modal...")
                turn_on.first.click()
                time.sleep(2)

            # Click Got it if exists
            got_it = page.locator("button:has-text('Got it')")
            if got_it.count() > 0:
                print("[TIKTOK] Dismissing 'Got it' Joyride popup...")
                got_it.first.click()
                time.sleep(2)

            # Extra safety: remove any leftover Joyride overlay from DOM
            page.evaluate("""() => {
                document.querySelectorAll('#react-joyride-portal, .react-joyride__overlay, div[data-test-id="overlay"]').forEach(el => el.remove());
            }""")
            time.sleep(1)

            page.screenshot(path="stage2_clean_editor.png")
            print("[TIKTOK] Saved stage2_clean_editor.png")

            # 4. Fill Caption
            print("[TIKTOK] Scrolling to top and filling caption...")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)

            caption_box = page.locator(".public-DraftEditor-content, div[contenteditable='true'], textarea").first
            if caption_box.count() > 0:
                caption_box.click(force=True)
                time.sleep(1)
                page.keyboard.press("Control+A")
                time.sleep(0.5)
                page.keyboard.press("Backspace")
                time.sleep(0.5)
                page.keyboard.type(CAPTION, delay=20)
                print("[TIKTOK] Caption successfully set!")
                time.sleep(2)

            page.screenshot(path="stage3_caption_filled.png")
            print("[TIKTOK] Saved stage3_caption_filled.png")

            # 5. Scroll down and locate Post button
            print("[TIKTOK] Scrolling to bottom for Post button...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Ensure any new overlay is cleared
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
                        print(f"[TIKTOK] Attempt {attempt+1}: Post button found. disabled={disabled}")
                        if disabled is None and "disabled" not in cls.lower():
                            print("🎯 [TIKTOK] Post button is enabled! Clicking Post...")
                            btn.click(force=True)
                            posted = True
                            break
                if posted:
                    break
                time.sleep(2)

            if posted:
                print("[TIKTOK] Post clicked! Waiting 12 seconds for publication confirmation...")
                time.sleep(12)
                page.screenshot(path="stage4_post_submitted.png")
                print("[TIKTOK] Saved stage4_post_submitted.png")
                
                # Check for "Manage your posts" modal button or redirection
                manage_btn = page.locator("button:has-text('Manage your posts'), a:has-text('Manage your posts')")
                if manage_btn.count() > 0:
                    print("🎉 [TIKTOK] 'Manage your posts' modal confirmed! Video successfully published!")
                else:
                    text_all = page.inner_text("body")
                    if "uploaded" in text_all.lower() or "manage your posts" in text_all.lower():
                        print("🎉 [TIKTOK] Success confirmed in page content!")
                    else:
                        print(f"[TIKTOK] Post completed. Final URL: {page.url}")
            else:
                print("[ERROR] Post button did not become active!")
                page.screenshot(path="stage4_error_disabled.png")

        except Exception as e:
            print(f"[ERROR] Exception during TikTok automation: {e}")
            page.screenshot(path="tiktok_final_exception.png")
        finally:
            context.close()

if __name__ == "__main__":
    run_upload_and_post()

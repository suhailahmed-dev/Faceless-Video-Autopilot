import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

TIKTOK_SESSION_DIR = config.BASE_DIR / ".tiktok_session"
VIDEO_PATH = Path(r"C:\Users\nasee\Desktop\faceless_video_bot\output_videos\2026-09-25\video_1_How_High-Value_People_Speak_3_Rules\final_video_1.mp4")

def test_file_chooser():
    print("[TEST] Launching to test file chooser...")
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

        page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6)

        # Inspect iframes
        print(f"[TEST] Total frames: {len(page.frames)}")
        for idx, f in enumerate(page.frames):
            print(f" Frame {idx}: name='{f.name}', url='{f.url}'")
            inputs = f.locator("input").all()
            print(f"   Inputs count: {len(inputs)}")
            for inp in inputs:
                print(f"     type={inp.get_attribute('type')}, accept={inp.get_attribute('accept')}")

        # Look for the Select video button
        btn = page.locator("button:has-text('Select video'), div[role='button']:has-text('Select video')").first
        print(f"[TEST] Select video button count: {btn.count()}")

        # Try expect_file_chooser
        print("[TEST] Triggering file chooser...")
        try:
            with page.expect_file_chooser(timeout=10000) as fc_info:
                btn.click()
            file_chooser = fc_info.value
            print(f"[TEST] File chooser intercepted! Is multiple: {file_chooser.is_multiple()}")
            file_chooser.set_files(str(VIDEO_PATH))
            print("[TEST] File set successfully via file chooser!")
        except Exception as e:
            print(f"[TEST] Error with file chooser: {e}")
            # Try frame iframes
            for f in page.frames:
                frame_btn = f.locator("button:has-text('Select video')")
                if frame_btn.count() > 0:
                    print(f"[TEST] Found button in frame {f.name}")
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        frame_btn.click()
                    fc = fc_info.value
                    fc.set_files(str(VIDEO_PATH))
                    print("[TEST] Set files via frame file chooser!")
                    break

        print("[TEST] Waiting 15s to observe what happens after file selection...")
        time.sleep(15)
        page.screenshot(path="test_after_file_select.png")
        print("[TEST] Saved test_after_file_select.png")

        # Log page text
        body_text = page.inner_text("body")
        print(f"[TEST] Body text sample after select:\n{body_text[:500]}")

        context.close()

if __name__ == "__main__":
    test_file_chooser()

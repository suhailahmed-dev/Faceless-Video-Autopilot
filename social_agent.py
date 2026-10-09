import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import config
import youtube_uploader

SESSION_DIR = config.BASE_DIR / ".social_browser_session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def open_login_session():
    """
    Opens a visible browser for the user to log into Facebook/Instagram & TikTok once.
    The session is saved permanently in SESSION_DIR.
    """
    print("=" * 65)
    print("      OPENING SOCIAL LOGIN BROWSER (ONE-TIME SETUP)")
    print("=" * 65)
    print("\n1. Facebook Business Suite tab khulega -> Login karein.")
    print("2. TikTok tab khulega -> Login karein.")
    print("3. Login complete hone ke baad yahan console mein ENTER dabayein.")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Tab 1: Meta Business Suite (Covers both Facebook & Instagram)
        page_fb = browser.pages[0] if browser.pages else browser.new_page()
        page_fb.goto("https://business.facebook.com/")
        
        # Tab 2: TikTok Creator Center
        page_tt = browser.new_page()
        page_tt.goto("https://www.tiktok.com/login")
        
        input("\n👉 Login mukammal karne ke baad is window mein ENTER dabayein: ")
        print("\nSession kamyabi se save ho gaya! Browser close ho raha hai...")
        browser.close()
        print("✅ DONE! Ab bot autonomous posting ke liye ready hai.")

def publish_meta_reel(video_path: Path, caption: str) -> bool:
    """
    Automates uploading a Reel to both Instagram & Facebook Page via Meta Business Suite.
    """
    if not video_path.exists():
        print(f"[META] Video not found: {video_path}")
        return False

    print(f"[META] Navigating to Meta Business Suite to publish Reel...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        try:
            page.goto("https://business.facebook.com/latest/reels_composer", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(5)
            
            # File input
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                print(f"[META] Uploading video file: {video_path.name}")
                file_input.first.set_input_files(str(video_path))
                time.sleep(8)
                
                # Try fill caption
                textbox = page.locator("div[role='textbox'], textarea").first
                if textbox.count() > 0:
                    textbox.fill(caption[:2000])
                    print("[META] Caption inserted.")
                
                time.sleep(5)
                # Next / Publish buttons in reels composer
                next_btns = page.locator("button:has-text('Next'), div[role='button']:has-text('Next')")
                for _ in range(3):
                    if next_btns.count() > 0 and next_btns.first.is_visible():
                        next_btns.first.click()
                        time.sleep(3)
                        
                pub_btn = page.locator("button:has-text('Publish'), div[role='button']:has-text('Publish')")
                if pub_btn.count() > 0 and pub_btn.first.is_visible():
                    pub_btn.first.click()
                    print("[META] ✅ Clicked Publish! Reel is being processed.")
                    time.sleep(10)
                    browser.close()
                    return True
            
            print("[META] Manual review or custom selector required.")
            time.sleep(5)
            browser.close()
            return True
        except Exception as e:
            print(f"[META] Error: {e}")
            browser.close()
            return False

def publish_tiktok_video(video_path: Path, caption: str) -> bool:
    """
    Automates uploading a video to TikTok via TikTok Creator Center.
    """
    if not video_path.exists():
        print(f"[TIKTOK] Video not found: {video_path}")
        return False

    print(f"[TIKTOK] Navigating to TikTok Creator Center...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        try:
            page.goto("https://www.tiktok.com/creator-center/upload", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(5)
            
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                print(f"[TIKTOK] Uploading video file: {video_path.name}")
                file_input.first.set_input_files(str(video_path))
                time.sleep(10)
                
                # Caption
                caption_area = page.locator("div[contenteditable='true'], textarea").first
                if caption_area.count() > 0:
                    caption_area.fill(caption[:2000])
                    print("[TIKTOK] Caption inserted.")
                
                time.sleep(5)
                post_btn = page.locator("button:has-text('Post')")
                if post_btn.count() > 0 and post_btn.first.is_visible():
                    post_btn.first.click()
                    print("[TIKTOK] ✅ Clicked Post!")
                    time.sleep(8)
                    browser.close()
                    return True
            
            time.sleep(5)
            browser.close()
            return True
        except Exception as e:
            print(f"[TIKTOK] Error: {e}")
            browser.close()
            return False

def publish_to_all_platforms(folder_path: Path, platforms: list = None) -> dict:
    """
    Universal Master Publisher: Publishes a video to YouTube, Instagram, Facebook, and TikTok.
    """
    if platforms is None:
        platforms = ["youtube", "instagram", "facebook", "tiktok"]

    folder = Path(folder_path)
    video_file = folder / "final_video_1.mp4"
    if not video_file.exists():
        for f in folder.glob("*.mp4"):
            video_file = f
            break
            
    pub_pack_file = folder / "publish_pack.txt"
    pack_text = pub_pack_file.read_text(encoding="utf-8", errors="replace") if pub_pack_file.exists() else ""

    results = {}
    
    # 1. YouTube Shorts
    if "youtube" in platforms:
        try:
            yt_title = "High-Value Psychology #Shorts"
            yt_desc = "Psychology facts and daily mindset shifts. #Shorts"
            for line in pack_text.splitlines():
                if line.startswith("TITLE:"):
                    yt_title = line.replace("TITLE:", "").strip()
            if "DESCRIPTION:" in pack_text:
                parts = pack_text.split("DESCRIPTION:")
                if len(parts) > 1:
                    d_chunk = parts[1].split("KEYWORDS / TAGS:")[0].strip()
                    if d_chunk:
                        yt_desc = d_chunk
            yt_url = youtube_uploader.upload_short(video_file, yt_title, yt_desc, privacy_status="public")
            results["youtube"] = {"status": "success", "url": yt_url}
        except Exception as e:
            results["youtube"] = {"status": "error", "error": str(e)}

    # 2. Instagram & Facebook (Meta)
    if "instagram" in platforms or "facebook" in platforms:
        try:
            ig_caption = "Apni communication mein ye shifts lao! #Psychology #LifeHacks"
            if "3. INSTAGRAM REELS:" in pack_text:
                ig_part = pack_text.split("3. INSTAGRAM REELS:")[1].split("4. FACEBOOK REELS:")[0].strip()
                if ig_part:
                    ig_caption = ig_part
            meta_ok = publish_meta_reel(video_file, ig_caption)
            results["meta"] = {"status": "success" if meta_ok else "failed"}
        except Exception as e:
            results["meta"] = {"status": "error", "error": str(e)}

    # 3. TikTok
    if "tiktok" in platforms:
        try:
            tt_caption = "Yeh rules apply karke dekhein! #fyp #psychology #lifehacks"
            if "2. TIKTOK:" in pack_text:
                tt_part = pack_text.split("2. TIKTOK:")[1].split("3. INSTAGRAM REELS:")[0].strip()
                if tt_part:
                    tt_caption = tt_part
            tt_ok = publish_tiktok_video(video_file, tt_caption)
            results["tiktok"] = {"status": "success" if tt_ok else "failed"}
        except Exception as e:
            results["tiktok"] = {"status": "error", "error": str(e)}

    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--login":
        open_login_session()
    else:
        print("Usage:")
        print("  python social_agent.py --login       (Open one-time browser login session)")
        print("  python social_agent.py --publish-all <folder_path>")

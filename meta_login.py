import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

META_SESSION_DIR = config.BASE_DIR / ".meta_session"
META_SESSION_DIR.mkdir(parents=True, exist_ok=True)

def run_meta_login(timeout_seconds: int = 360):
    print("=" * 65, flush=True)
    print("      🌐 META (INSTAGRAM & FACEBOOK) LOGIN SESSION", flush=True)
    print("=" * 65, flush=True)
    print("Launching maximized Edge browser to foreground...", flush=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(META_SESSION_DIR),
            channel="msedge",
            headless=False,
            no_viewport=True,
            args=[
                "--start-maximized",
                "--new-window",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        # Tab 1: Instagram
        page_ig = context.pages[0] if context.pages else context.new_page()
        page_ig.goto("https://www.instagram.com/accounts/login/", timeout=60000)
        page_ig.bring_to_front()
        print("Tab 1 (Instagram) ready.", flush=True)
        
        # Tab 2: Facebook
        page_fb = context.new_page()
        page_fb.goto("https://www.facebook.com/login/", timeout=60000)
        print("Tab 2 (Facebook) ready.", flush=True)
        
        print("\n[INFO] Both tabs are open on your screen! Please log in.", flush=True)
        print("[INFO] Waiting for login confirmation...", flush=True)
        
        start_time = time.time()
        ig_logged_in = False
        fb_logged_in = False
        
        while time.time() - start_time < timeout_seconds:
            cookies = context.cookies()
            
            for c in cookies:
                if "instagram.com" in c.get("domain", "") and c.get("name") == "sessionid":
                    if not ig_logged_in:
                        print("🎉 [DETECTED] Instagram Login Success!", flush=True)
                        ig_logged_in = True
                if "facebook.com" in c.get("domain", "") and c.get("name") in ("c_user", "xs"):
                    if not fb_logged_in:
                        print("🎉 [DETECTED] Facebook Login Success!", flush=True)
                        fb_logged_in = True
                        
            if ig_logged_in and fb_logged_in:
                print("\n✅ Both Instagram and Facebook logins confirmed!", flush=True)
                print("Session successfully saved! Closing browser in 3 seconds...", flush=True)
                time.sleep(3)
                break
                
            time.sleep(3)
            
        context.close()
        print("=" * 65, flush=True)
        print(f"FINAL RESULT: Instagram={'LOGGED IN' if ig_logged_in else 'PENDING'} | Facebook={'LOGGED IN' if fb_logged_in else 'PENDING'}", flush=True)
        print("=" * 65, flush=True)
        return {"instagram": ig_logged_in, "facebook": fb_logged_in}

if __name__ == "__main__":
    run_meta_login()

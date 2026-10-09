import os
import sys
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

import config

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

SRC_ROOT = Path(os.environ['LOCALAPPDATA']) / r'Google\Chrome\User Data'
DST_ROOT = config.BASE_DIR / ".meta_session"

def sync_session_from_chrome():
    print("=" * 65, flush=True)
    print("      🔄 SYNCING INSTAGRAM & FACEBOOK FROM GOOGLE CHROME", flush=True)
    print("=" * 65, flush=True)
    
    # Wait for Chrome to close if running
    import subprocess
    def is_chrome_running():
        res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq chrome.exe"], capture_output=True, text=True)
        return "chrome.exe" in res.stdout

    if is_chrome_running():
        print("[WAIT] Google Chrome is currently open.", flush=True)
        print("[ACTION NEEDED] Please close Google Chrome for 5 seconds...", flush=True)
        wait_start = time.time()
        while is_chrome_running():
            time.sleep(1)
            if time.time() - wait_start > 60:
                print("[TIMEOUT] Chrome was not closed. Please close Chrome and try again.", flush=True)
                return False
                
    print("[SUCCESS] Chrome is closed! Copying profile cookies...", flush=True)
    time.sleep(1)
    
    DST_ROOT.mkdir(parents=True, exist_ok=True)
    
    # Copy Local State
    src_ls = SRC_ROOT / "Local State"
    if src_ls.exists():
        shutil.copy2(src_ls, DST_ROOT / "Local State")
        print("  ✓ Local State copied", flush=True)

    # Copy Profile 1 as Default
    dst_default = DST_ROOT / "Default"
    dst_default.mkdir(parents=True, exist_ok=True)
    
    for folder_name in ["Network", "Local Storage", "Session Storage"]:
        src_f = SRC_ROOT / "Profile 1" / folder_name
        dst_f = dst_default / folder_name
        if src_f.exists():
            shutil.copytree(src_f, dst_f, dirs_exist_ok=True)
            print(f"  ✓ {folder_name} copied", flush=True)
            
    # Copy preferences & secure preferences
    for pref_file in ["Preferences", "Secure Preferences"]:
        src_p = SRC_ROOT / "Profile 1" / pref_file
        if src_p.exists():
            shutil.copy2(src_p, dst_default / pref_file)
            print(f"  ✓ {pref_file} copied", flush=True)

    print("\n[VERIFY] Launching background check on Instagram & Facebook...", flush=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(DST_ROOT),
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        
        # Verify Instagram
        page_ig = context.pages[0] if context.pages else context.new_page()
        page_ig.goto("https://www.instagram.com/", timeout=40000, wait_until="domcontentloaded")
        time.sleep(4)
        ig_url = page_ig.url
        ig_logged_in = "login" not in ig_url and "accounts" not in ig_url
        print(f"  ✓ Instagram Status: {'LOGGED IN (' + ig_url + ')' if ig_logged_in else 'PENDING'}", flush=True)
        
        # Verify Facebook
        page_fb = context.new_page()
        page_fb.goto("https://www.facebook.com/", timeout=40000, wait_until="domcontentloaded")
        time.sleep(4)
        fb_url = page_fb.url
        fb_logged_in = "login" not in fb_url
        print(f"  ✓ Facebook Status:  {'LOGGED IN (' + fb_url + ')' if fb_logged_in else 'PENDING'}", flush=True)
        
        context.close()
        
    print("=" * 65, flush=True)
    print("🎉 META SESSION READY! You can now reopen Google Chrome!", flush=True)
    print("=" * 65, flush=True)
    return True

if __name__ == "__main__":
    sync_session_from_chrome()

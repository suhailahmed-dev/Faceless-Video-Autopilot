import subprocess
import re
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CLOUDFLARED_EXE = BASE_DIR / "cloudflared.exe"
URL_FILE = BASE_DIR / "mobile_url.txt"

def run_tunnel():
    if not CLOUDFLARED_EXE.exists():
        print(f"[ERROR] cloudflared.exe not found at {CLOUDFLARED_EXE}")
        return

    print("[TUNNEL] Starting Cloudflare Tunnel to http://127.0.0.1:9999 ...")
    cmd = [str(CLOUDFLARED_EXE), "tunnel", "--url", "http://127.0.0.1:9999"]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    url_found = None
    for line in proc.stdout:
        print(line, end="")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            url_found = match.group(0)
            print(f"\n==================================================")
            print(f"🚀 LIVE MOBILE ACCESS URL FOR OFFICE:")
            print(f"👉 {url_found}")
            print(f"==================================================\n")
            URL_FILE.write_text(url_found, encoding="utf-8")
            break

    # Keep tunnel alive
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    run_tunnel()

import os
import sys
from pathlib import Path
import json

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = config.BASE_DIR / "client_secrets.json"
TOKEN_FILE = config.BASE_DIR / "youtube_token.json"

def get_authenticated_service():
    """
    Authenticates with YouTube Data API v3 and saves persistent credentials.
    """
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing '{CLIENT_SECRETS_FILE.name}'! "
                    "Download your OAuth Client ID JSON from Google Cloud Console and save it here."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            # Use isolated loopback port 9090 so it never touches port 8000 or anything else
            creds = flow.run_local_server(port=9090)
            
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_short(
    video_path: Path,
    title: str,
    description: str,
    tags: list = None,
    privacy_status: str = "public"
) -> str:
    """
    Uploads a 9:16 vertical video directly as a YouTube Short.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    youtube = get_authenticated_service()

    # Ensure #Shorts tag in title
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["shorts", "psychology", "motivation"],
            "categoryId": "27"  # Education category
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=1024*1024*5,
        resumable=True,
        mimetype="video/*"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print(f"[YOUTUBE] Uploading '{title}' to YouTube Shorts...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   Upload progress: {pct}%")

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    print(f"[SUCCESS] YouTube Short is LIVE at: {video_url}")
    return video_url

if __name__ == "__main__":
    if not CLIENT_SECRETS_FILE.exists():
        print(f"Note: To enable 1-click auto-upload to YouTube, place '{CLIENT_SECRETS_FILE.name}' in project folder.")
    else:
        print("client_secrets.json detected. Starting Authentication...")
        try:
            yt = get_authenticated_service()
            print("\n🎉 SUCCESS! Authenticated with YouTube Upload API.")
            print("✅ youtube_token.json saved! Auto-upload is now ready to use.")
        except Exception as e:
            print("\n❌ Authentication Error:", e)
            print("Tip: Agar 'access_denied' aaye, to Google Cloud Console mein OAuth Consent Screen par 'Test users' mein apna Gmail add karein.")

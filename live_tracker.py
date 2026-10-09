import urllib.request
import json
import re

def get_youtube_video_stats(video_id: str):
    """
    Fetches real live views and title from public YouTube data.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
        views_match = re.search(r'"viewCount":"(\d+)"', html)
        likes_match = re.search(r'"defaultText":\{"accessibility":\{"accessibilityData":\{"label":"(\d+) likes"\}\}\}', html)
        views = int(views_match.group(1)) if views_match else 0
        likes = likes_match.group(1) if likes_match else "0"
        return {"views": views, "likes": likes, "url": f"https://youtu.be/{video_id}"}
    except Exception as e:
        return {"views": 0, "likes": "0", "error": str(e)}

if __name__ == "__main__":
    stats = get_youtube_video_stats("c2hXRx36PHQ")
    print("REAL_LIVE_STATS:", stats)

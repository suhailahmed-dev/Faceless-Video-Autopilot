import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

import config
from trend_radar import get_daily_trending_topic, get_live_radar_summary
import youtube_uploader
import tiktok_uploader
import meta_uploader

# Fix Windows console encoding for UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG_FILE = config.BASE_DIR / "autopilot_config.json"
QUEUE_FILE = config.BASE_DIR / "scheduled_queue.json"
APPROVALS_FILE = config.BASE_DIR / "approvals_tracker.json"

DEFAULT_CONFIG = {
    "enabled": True,
    "white_label_brand": "APEX MEDIA HQ",
    "timezone": "PKT (UTC+5)",
    "peak_windows": {
        "youtube": [
            {"time": "13:30", "slot": "Lunch Break Quick Hook", "traffic": "Peak Mobile"},
            {"time": "18:30", "slot": "Evening Commute Psychology", "traffic": "High Retention"},
            {"time": "21:45", "slot": "Night Relax Stoic Story", "traffic": "Maximum Watch-Time"}
        ],
        "tiktok": [
            {"time": "14:00", "slot": "Afternoon FYP Wave", "traffic": "Youth Traffic"},
            {"time": "19:00", "slot": "Evening Rush", "traffic": "High Engagement"},
            {"time": "22:30", "slot": "Late-Night Viral Scroll", "traffic": "Maximum Algorithm Velocity"}
        ],
        "instagram": [
            {"time": "12:45", "slot": "Midday Aesthetic Reel", "traffic": "Active Saves"},
            {"time": "20:15", "slot": "Prime Social Hour", "traffic": "High Shares"}
        ],
        "facebook": [
            {"time": "15:00", "slot": "Afternoon Tea Break", "traffic": "Family Browsing"},
            {"time": "21:00", "slot": "Family Evening Relaxation", "traffic": "Maximum Viral Shares"}
        ]
    },
    "nightly_prep_time": "23:45",
    "last_nightly_prep": "",
    "auto_publish_enabled": True
}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def load_queue() -> list:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_queue(q: list):
    QUEUE_FILE.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")

def get_current_pkt() -> datetime:
    """Returns current datetime."""
    return datetime.now()

def seed_initial_schedule_if_empty():
    """Seeds the queue with upcoming scheduled drops if empty."""
    q = load_queue()
    if q:
        return

    # Check available generated videos in output folder
    from run_daily import create_multiplatform_bundle
    now = get_current_pkt()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    initial_items = [
        {
            "id": "sched_yt_1",
            "platform": "youtube",
            "title": "The Power of Tactical Silence #Shorts",
            "target_date": today_str,
            "target_time": "13:30",
            "scheduled_timestamp": f"{today_str} 13:30:00",
            "slot_label": "Lunch Break Quick Hook",
            "video_name": "final_video_2.mp4",
            "folder_path": str(config.OUTPUT_DIR / "2026-09-25" / "video_2_Rule_1_of_Stoicism_The_Power_of_Absolute"),
            "status": "published",
            "live_url": "https://youtu.be/Y3xZmZKuiRE"
        },
        {
            "id": "sched_tt_1",
            "platform": "tiktok",
            "title": "Disrespect ko Unhi Par Ultana Seekho 🔥",
            "target_date": today_str,
            "target_time": "14:00",
            "scheduled_timestamp": f"{today_str} 14:00:00",
            "slot_label": "Afternoon FYP Wave",
            "video_name": "final_video_2.mp4",
            "folder_path": str(config.OUTPUT_DIR / "2026-09-25" / "video_2_Rule_1_of_Stoicism_The_Power_of_Absolute"),
            "status": "published",
            "live_url": "Live on TikTok"
        },
        {
            "id": "sched_yt_2",
            "platform": "youtube",
            "title": "Foot Angle Psychology: Escape Signals #Shorts",
            "target_date": today_str,
            "target_time": "18:30",
            "scheduled_timestamp": f"{today_str} 18:30:00",
            "slot_label": "Evening Commute Psychology",
            "video_name": "youtube_short.mp4",
            "folder_path": str(config.OUTPUT_DIR / "2026-09-25" / "video_1_How_High-Value_People_Speak_3_Rules"),
            "status": "ready",
            "live_url": ""
        },
        {
            "id": "sched_ig_1",
            "platform": "instagram",
            "title": "Sabke Hote Huway Bhi Akelapan... 💔",
            "target_date": today_str,
            "target_time": "20:15",
            "scheduled_timestamp": f"{today_str} 20:15:00",
            "slot_label": "Prime Social Hour",
            "video_name": "instagram_reel.mp4",
            "folder_path": str(config.OUTPUT_DIR / "2026-09-25" / "video_1_How_High-Value_People_Speak_3_Rules"),
            "status": "ready",
            "live_url": ""
        },
        {
            "id": "sched_fb_1",
            "platform": "facebook",
            "title": "Desi Rishtaydaron Ke Taane Aur Classy Jawab 😂",
            "target_date": today_str,
            "target_time": "21:00",
            "scheduled_timestamp": f"{today_str} 21:00:00",
            "slot_label": "Family Evening Relaxation",
            "video_name": "facebook_reel.mp4",
            "folder_path": str(config.OUTPUT_DIR / "2026-09-25" / "video_1_How_High-Value_People_Speak_3_Rules"),
            "status": "ready",
            "live_url": ""
        },
        {
            "id": "sched_trend_1",
            "platform": "all",
            "title": "🌟 DAILY TREND BREAKTHROUGH (Auto Nightly Prep)",
            "target_date": tomorrow_str,
            "target_time": "12:00",
            "scheduled_timestamp": f"{tomorrow_str} 12:00:00",
            "slot_label": "Breaking Trend Spotlight",
            "video_name": "bundle_trending.mp4",
            "folder_path": "",
            "status": "queued_for_nightly_prep",
            "live_url": ""
        }
    ]
    save_queue(initial_items)

def run_nightly_prep():
    """
    Executes nightly autonomous content synthesis:
    1. Scrapes real-time trends
    2. Builds 1 Dedicated Daily Trending Video
    3. Populates tomorrow's peak posting schedule
    """
    cfg = load_config()
    now = get_current_pkt()
    tomorrow = now + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    print(f"\n🌙 [NIGHTLY PREP] Starting Autonomous Content Prep for {tomorrow_str}...")
    
    try:
        from run_daily import create_multiplatform_bundle
        trend_res = create_multiplatform_bundle(index=99, is_trending=True)
        bundle_path = trend_res.get("bundle_dir", "")
        topic = trend_res.get("topic", "Daily Trend")
        
        # Schedule the new bundle for tomorrow across platforms
        q = load_queue()
        cfg_windows = cfg.get("peak_windows", {})

        new_items = [
            {
                "id": f"drop_yt_{tomorrow_str}",
                "platform": "youtube",
                "title": f"The Psychology Behind {topic[:30]} #Shorts",
                "target_date": tomorrow_str,
                "target_time": "13:30",
                "scheduled_timestamp": f"{tomorrow_str} 13:30:00",
                "slot_label": "Lunch Break Quick Hook",
                "video_name": "youtube_short.mp4",
                "folder_path": bundle_path,
                "status": "ready",
                "live_url": ""
            },
            {
                "id": f"drop_tt_{tomorrow_str}",
                "platform": "tiktok",
                "title": f"Trend Alert: {topic[:30]} 🔥",
                "target_date": tomorrow_str,
                "target_time": "14:00",
                "scheduled_timestamp": f"{tomorrow_str} 14:00:00",
                "slot_label": "Afternoon FYP Wave",
                "video_name": "tiktok_reel.mp4",
                "folder_path": bundle_path,
                "status": "ready",
                "live_url": ""
            },
            {
                "id": f"drop_ig_{tomorrow_str}",
                "platform": "instagram",
                "title": f"Emotional Reality: {topic[:30]}",
                "target_date": tomorrow_str,
                "target_time": "20:15",
                "scheduled_timestamp": f"{tomorrow_str} 20:15:00",
                "slot_label": "Prime Social Hour",
                "video_name": "instagram_reel.mp4",
                "folder_path": bundle_path,
                "status": "ready",
                "live_url": ""
            },
            {
                "id": f"drop_fb_{tomorrow_str}",
                "platform": "facebook",
                "title": f"Desi Lesson: {topic[:30]}",
                "target_date": tomorrow_str,
                "target_time": "21:00",
                "scheduled_timestamp": f"{tomorrow_str} 21:00:00",
                "slot_label": "Family Evening Relaxation",
                "video_name": "facebook_reel.mp4",
                "folder_path": bundle_path,
                "status": "ready",
                "live_url": ""
            }
        ]

        q.extend(new_items)
        save_queue(q)

        cfg["last_nightly_prep"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_config(cfg)
        print(f"✅ [NIGHTLY PREP] Complete! 4 Platform Drops Scheduled for {tomorrow_str}.")
        return {"status": "success", "message": f"Nightly prep completed for {tomorrow_str}"}
    except Exception as e:
        print(f"❌ [NIGHTLY PREP ERROR]: {e}")
        return {"status": "error", "message": str(e)}

def dispatch_scheduled_item(item: dict) -> bool:
    """Executes upload for a scheduled item."""
    platform = item.get("platform", "").lower()
    folder_path = item.get("folder_path", "")
    video_name = item.get("video_name", "final_video_2.mp4")
    vid_file = Path(folder_path) / video_name
    
    if not vid_file.exists():
        # Try fallback to final_video_*.mp4
        compat = list(Path(folder_path).glob("final_video_*.mp4"))
        if compat:
            vid_file = compat[0]
        else:
            print(f"⚠️ Video file not found: {vid_file}")
            return False

    pub_file = Path(folder_path) / "publish_pack.txt"
    title = item.get("title", "High-Value Psychology")
    caption = title

    print(f"🚀 [AUTO-PILOT DISPATCH] Uploading to {platform.upper()}: '{title}'...")
    try:
        if platform == "youtube":
            url = youtube_uploader.upload_short(vid_file, title, title + " #Shorts #Psychology", tags=["shorts", "psychology"])
            item["live_url"] = url
        elif platform == "tiktok":
            res = tiktok_uploader.upload_tiktok_video(vid_file, caption + " #fyp #viral")
            item["live_url"] = "Live on TikTok"
        elif platform == "instagram":
            res = meta_uploader.upload_instagram_reel(vid_file, caption + " #reels #psychology")
            item["live_url"] = "Live on Instagram Reels"
        elif platform == "facebook":
            res = meta_uploader.upload_facebook_reel(vid_file, caption)
            item["live_url"] = "Live on Facebook Reels"

        item["status"] = "published"
        item["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True
    except Exception as e:
        print(f"❌ Dispatch failed for {platform}: {e}")
        item["status"] = "failed"
        item["error"] = str(e)
        return False

def scheduler_daemon_loop():
    """Background worker continuously checking scheduled drop timestamps."""
    print("⏰ [AUTOPILOT SCHEDULER] Daemon active and monitoring peak windows...")
    seed_initial_schedule_if_empty()

    while True:
        try:
            cfg = load_config()
            if cfg.get("enabled", True):
                now = get_current_pkt()
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                time_str = now.strftime("%H:%M")
                
                # Check nightly prep time (default 23:45)
                prep_time = cfg.get("nightly_prep_time", "23:45")
                last_prep = cfg.get("last_nightly_prep", "")
                if time_str == prep_time and (not last_prep or not last_prep.startswith(now.strftime("%Y-%m-%d"))):
                    run_nightly_prep()

                # Check auto-publish queue
                if cfg.get("auto_publish_enabled", True):
                    queue = load_queue()
                    updated = False
                    for item in queue:
                        if item.get("status") == "ready":
                            sched_ts = item.get("scheduled_timestamp", "")
                            if sched_ts and now_str >= sched_ts:
                                success = dispatch_scheduled_item(item)
                                updated = True
                    if updated:
                        save_queue(queue)
        except Exception as e:
            print(f"⚠️ Scheduler iteration error: {e}")

        time.sleep(30)

def start_scheduler_thread():
    t = threading.Thread(target=scheduler_daemon_loop, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    print("Testing Auto-Pilot Scheduler & Nightly Prep Engine...")
    cfg = load_config()
    print("Config:", cfg)
    seed_initial_schedule_if_empty()
    q = load_queue()
    print(f"Current Queue: {len(q)} items scheduled.")
    for item in q[:3]:
        print(f" - [{item['platform'].upper()}] {item['slot_label']} @ {item.get('scheduled_timestamp')} -> {item['status']}")

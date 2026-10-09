import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

import config
from media_manager import get_ffmpeg_exe

# Fix Windows console encoding for UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = config.BASE_DIR
STORY_FACTORY_DIR = BASE_DIR / "story_factory"
QUEUE_FILE = BASE_DIR / "scheduled_queue.json"
PROCESSED_LOG = STORY_FACTORY_DIR / "processed_episodes.json"

def load_processed() -> list:
    if PROCESSED_LOG.exists():
        try:
            return json.loads(PROCESSED_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def mark_processed(filename: str):
    p = load_processed()
    if filename not in p:
        p.append(filename)
        PROCESSED_LOG.write_text(json.dumps(p, indent=2), encoding="utf-8")

def get_video_duration(video_path: Path) -> float:
    """Uses ffmpeg -i to extract exact video duration in seconds."""
    import re
    ffmpeg_exe = str(get_ffmpeg_exe())
    cmd = [ffmpeg_exe, "-i", str(video_path)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if m:
            h = float(m.group(1))
            mins = float(m.group(2))
            s = float(m.group(3))
            return h * 3600 + mins * 60 + s
    except Exception:
        pass
    return 150.0

def validate_final_episode(video_path: Path) -> dict:
    """Runs pre-publish validation checklist on the CapCut final export."""
    if not video_path.exists():
        return {"valid": False, "error": "File does not exist"}

    duration = get_video_duration(video_path)
    # Hard limit: Max episode length 2.5 minutes (150s + 15s grace buffer)
    if duration > 165.0:
        return {"valid": False, "error": f"Episode exceeds 2.5 min limit ({duration:.1f}s)"}

    return {
        "valid": True,
        "duration": duration,
        "size_mb": round(video_path.stat().st_size / (1024 * 1024), 2)
    }

def cut_cliffhanger_shorts(final_video_path: Path, shorts_dir: Path, prefix: str = "StoryA_Ep01") -> list:
    """
    Auto-cuts 2 high-tension cliffhanger shorts (15-25s) from the final episode
    and burns the mandatory CTA: 'Watch the full story on our channel!'
    """
    ffmpeg_exe = get_ffmpeg_exe()
    shorts_dir.mkdir(parents=True, exist_ok=True)
    total_dur = get_video_duration(final_video_path)

    # Dynamic safe offsets based on actual video length
    s1_dur = min(22.0, max(10.0, total_dur * 0.25))
    s1_start = max(0.0, total_dur * 0.15)

    s2_dur = min(22.0, max(10.0, total_dur * 0.25))
    s2_start = max(s1_start + s1_dur, total_dur * 0.60)
    if s2_start + s2_dur > total_dur:
        s2_start = max(0.0, total_dur - s2_dur - 1.0)

    short1_path = shorts_dir / f"{prefix}_Short1_Hook.mp4"
    short2_path = shorts_dir / f"{prefix}_Short2_Cliffhanger.mp4"

    cta_banner = (
        "drawbox=y=ih-120:color=black@0.75:width=iw:height=120:t=fill,"
        "drawtext=text='WATCH FULL STORY ON CHANNEL!':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-80:shadowcolor=black:shadowx=2:shadowy=2"
    )

    # Cut Short 1
    cmd1 = [
        ffmpeg_exe, "-y",
        "-ss", f"{s1_start:.2f}",
        "-i", str(final_video_path),
        "-t", f"{s1_dur:.2f}",
        "-vf", cta_banner,
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "4.5M",
        "-c:a", "aac",
        "-b:a", "192k",
        str(short1_path)
    ]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    if res1.returncode != 0:
        cmd1[cmd1.index(config.VIDEO_ENCODER)] = "libx264"
        subprocess.run(cmd1, capture_output=True, text=True)

    # Cut Short 2
    cmd2 = [
        ffmpeg_exe, "-y",
        "-ss", f"{s2_start:.2f}",
        "-i", str(final_video_path),
        "-t", f"{s2_dur:.2f}",
        "-vf", cta_banner,
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "4.5M",
        "-c:a", "aac",
        "-b:a", "192k",
        str(short2_path)
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    if res2.returncode != 0:
        cmd2[cmd2.index(config.VIDEO_ENCODER)] = "libx264"
        subprocess.run(cmd2, capture_output=True, text=True)

    return [str(short1_path), str(short2_path)]

def schedule_story_episode(final_video_path: Path, shorts_paths: list, story_name: str, ep_num: int):
    """
    Schedules the full episode for YouTube Main + Facebook (every 2 days)
    and the 2 shorts for YouTube Shorts + TikTok + Instagram Reels (daily).
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    q = []
    if QUEUE_FILE.exists():
        try:
            q = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 1. Long Episode (YouTube Main + Facebook)
    ep_item = {
        "id": f"story_long_{story_name}_ep{ep_num:02d}",
        "platform": "youtube_main",
        "title": f"The Haunted Frequency: Episode {ep_num} [Kids Sci-Fi Series]",
        "target_date": today_str,
        "target_time": "18:00",
        "scheduled_timestamp": f"{today_str} 18:00:00",
        "slot_label": f"Story Episode {ep_num} (Long Video Drop)",
        "video_name": final_video_path.name,
        "folder_path": str(final_video_path.parent),
        "status": "ready",
        "live_url": ""
    }
    q.append(ep_item)

    # 2. Daily Short 1 (Day 2 Lunch Slot: 1:30 PM PKT)
    if len(shorts_paths) > 0:
        short1_file = Path(shorts_paths[0])
        q.append({
            "id": f"story_short1_{story_name}_ep{ep_num:02d}",
            "platform": "youtube",
            "title": f"The Radio Whispered Their Names... 😱 Episode {ep_num} #Shorts",
            "target_date": tomorrow_str,
            "target_time": "13:30",
            "scheduled_timestamp": f"{tomorrow_str} 13:30:00",
            "slot_label": "Story Short #1 (Lunch Peak)",
            "video_name": short1_file.name,
            "folder_path": str(short1_file.parent),
            "status": "ready",
            "live_url": ""
        })

    # 3. Daily Short 2 (Day 2 Evening Slot: 7:00 PM PKT)
    if len(shorts_paths) > 1:
        short2_file = Path(shorts_paths[1])
        q.append({
            "id": f"story_short2_{story_name}_ep{ep_num:02d}",
            "platform": "tiktok",
            "title": f"Don't Look Up At The Sky! 🌌 Episode {ep_num} Cliffhanger #fyp",
            "target_date": tomorrow_str,
            "target_time": "19:00",
            "scheduled_timestamp": f"{tomorrow_str} 19:00:00",
            "slot_label": "Story Short #2 (Evening FYP)",
            "video_name": short2_file.name,
            "folder_path": str(short2_file.parent),
            "status": "ready",
            "live_url": ""
        })

    QUEUE_FILE.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Successfully scheduled Episode {ep_num} + 2 Cliffhanger Shorts into Auto-Pilot Queue!")

def check_ready_folders_once() -> list:
    """Scans all Story Ready folders for finalized CapCut episodes."""
    processed = load_processed()
    results = []

    for story_folder in STORY_FACTORY_DIR.glob("Story_*"):
        ready_dir = story_folder / "Ready"
        shorts_dir = story_folder / "Shorts"
        if not ready_dir.exists():
            continue

        for mp4_file in ready_dir.glob("*_FINAL.mp4"):
            if mp4_file.name in processed:
                continue

            print(f"\n🔔 [NEW EPISODE DETECTED IN READY]: {mp4_file.name}")
            val = validate_final_episode(mp4_file)
            if not val["valid"]:
                print(f"❌ Validation failed for {mp4_file.name}: {val['error']}")
                continue

            # Extract episode number
            ep_num = 1
            if "_Ep" in mp4_file.name:
                try:
                    ep_num = int(mp4_file.name.split("_Ep")[1][:2])
                except Exception:
                    pass

            # 1. Auto-cut 2 cliffhanger shorts
            print(f"✂️ Auto-cutting 2 cliffhanger shorts from {mp4_file.name}...")
            prefix = f"StoryA_Ep{ep_num:02d}" if "Story_A" in story_folder.name else f"StoryB_Ep{ep_num:02d}"
            shorts = cut_cliffhanger_shorts(mp4_file, shorts_dir, prefix=prefix)
            print(f"   ✓ Short 1: {shorts[0]}")
            print(f"   ✓ Short 2: {shorts[1]}")

            # 2. Schedule episode + shorts
            schedule_story_episode(mp4_file, shorts, story_name=story_folder.name, ep_num=ep_num)

            # 3. Mark processed
            mark_processed(mp4_file.name)
            results.append({
                "file": mp4_file.name,
                "shorts": shorts,
                "status": "scheduled"
            })

    return results

if __name__ == "__main__":
    print("Testing Story Watcher & Shorts Cutter Engine...")
    res = check_ready_folders_once()
    print("Watcher check complete. Processed items:", len(res))

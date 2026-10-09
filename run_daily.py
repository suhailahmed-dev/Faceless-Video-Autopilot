import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import shutil

import config

# Fix Windows console encoding for UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gemini_generator import (
    generate_youtube_script,
    generate_tiktok_script,
    generate_instagram_script,
    generate_facebook_script,
    generate_trending_topic_script,
    generate_viral_script
)
from voice_generator import generate_voiceover
from subtitle_engine import create_ass_subtitles
from media_manager import prepare_contextual_background, prepare_music
from video_builder import assemble_final_video
from trend_radar import get_platform_topic, get_daily_trending_topic, get_todays_winning_topic
from memory_tracker import log_generated_video

# Mapping platform to optimal voice
PLATFORM_VOICE_MAP = {
    "youtube": "english",       # en-US-ChristopherNeural (Authoritative, high-monetization baritone)
    "tiktok": "urdu",           # ur-PK-AsadNeural (Authentic, fast street-smart Roman Urdu)
    "instagram": "urdu",        # ur-PK-AsadNeural (Emotional, high-resonance)
    "facebook": "urdu"          # ur-PK-AsadNeural (Desi storytelling, relatable)
}

def render_pipeline_video(
    script_text: str,
    output_video_path: Path,
    voice: str = "english",
    temp_suffix: str = "1",
    scenes_dir: Path = None
) -> dict:
    """
    Core video generation engine:
    Voiceover -> ASS Subtitles -> Dynamic 3D Scenes -> Ambient BGM -> NVENC Render
    """
    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    scenes_dir = scenes_dir or config.TEMP_DIR / f"scenes_{temp_suffix}"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover
    voice_res = generate_voiceover(script_text, output_filename=f"voice_{temp_suffix}.mp3", voice=voice)
    audio_path = Path(voice_res["audio_path"])
    duration = voice_res["duration"]
    subtitles = voice_res["subtitles"]

    # 2. Dynamic Subtitles
    ass_path = config.TEMP_DIR / f"subtitles_{temp_suffix}.ass"
    create_ass_subtitles(subtitles, ass_path)

    # 3. Dynamic 3D Background
    bg_video_path = config.TEMP_DIR / f"bg_{temp_suffix}.mp4"
    prepare_contextual_background(voice_res.get("sentences", []), duration, bg_video_path, scenes_dir=scenes_dir)

    # 4. Soundscape
    bg_music_path = config.TEMP_DIR / f"music_{temp_suffix}.mp3"
    prepare_music(duration, bg_music_path)

    # 5. Assemble Video
    assemble_final_video(
        background_path=bg_video_path,
        voice_audio_path=audio_path,
        music_audio_path=bg_music_path,
        ass_subtitle_path=ass_path,
        output_video_path=output_video_path,
        duration=duration
    )

    return {
        "video_path": str(output_video_path),
        "duration": duration,
        "audio_path": str(audio_path)
    }

def create_platform_video(
    platform: str,
    topic: str = None,
    index: int = 1,
    mode: str = "short"
) -> dict:
    """
    Generates a dedicated, platform-native video file tailored specifically
    in language, voice, pacing, and metadata for a single platform.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    batch_dir = config.OUTPUT_DIR / today_str
    batch_dir.mkdir(parents=True, exist_ok=True)

    platform = platform.lower()
    voice = PLATFORM_VOICE_MAP.get(platform, "english")

    if not topic:
        topic_info = get_platform_topic(platform)
        selected_topic = topic_info["chosen_topic"]
        category = topic_info.get("category", "Psychology")
    else:
        selected_topic = topic
        category = "Custom Topic"

    print(f"\n==========================================")
    print(f"🎬 Generating Platform-Dedicated Video: [{platform.upper()}] (Slot #{index})")
    print(f"📌 Topic: '{selected_topic}' ({category})")
    print(f"🎙️ Target Voice: {voice.upper()} | Mode: {mode.upper()}")
    print(f"==========================================")

    # Generate dedicated script
    if platform == "youtube":
        script_data = generate_youtube_script(selected_topic, mode=mode)
        vid_filename = f"youtube_{mode}.mp4"
    elif platform == "tiktok":
        script_data = generate_tiktok_script(selected_topic)
        vid_filename = "tiktok_reel.mp4"
    elif platform == "instagram":
        script_data = generate_instagram_script(selected_topic, style="urdu_emotional")
        vid_filename = "instagram_reel.mp4"
    elif platform == "facebook":
        script_data = generate_facebook_script(selected_topic, style="moral_story")
        vid_filename = "facebook_reel.mp4"
    else:
        script_data = generate_youtube_script(selected_topic, mode="short")
        vid_filename = f"{platform}_video.mp4"

    title = script_data.get("title", f"{platform.capitalize()} Video {index}")
    script_text = script_data.get("script", "")
    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()[:35].replace(" ", "_")

    video_dir = batch_dir / f"{platform}_{index}_{clean_title}"
    video_dir.mkdir(parents=True, exist_ok=True)
    out_video_path = video_dir / vid_filename
    scenes_dir = video_dir / "scenes"

    render_res = render_pipeline_video(
        script_text=script_text,
        output_video_path=out_video_path,
        voice=voice,
        temp_suffix=f"{platform}_{index}",
        scenes_dir=scenes_dir
    )

    # Save dedicated platform metadata
    meta_path = video_dir / f"{platform}_meta.json"
    meta_payload = {
        "platform": platform,
        "title": title,
        "hook": script_data.get("hook", ""),
        "script": script_text,
        "metadata": script_data,
        "duration": render_res["duration"],
        "video_file": str(out_video_path),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2, ensure_ascii=False)

    # Also save standard publish pack for human review
    pack_path = video_dir / "publish_pack.txt"
    with open(pack_path, "w", encoding="utf-8") as f:
        f.write(f"=== {platform.upper()} DEDICATED PACK ===\nTitle: {title}\nCaption/Desc: {json.dumps(script_data, indent=2, ensure_ascii=False)}\n")

    log_generated_video(
        title=f"[{platform.upper()}] {title}",
        topic=selected_topic,
        category=category,
        folder_path=str(video_dir),
        duration=render_res["duration"]
    )

    print(f"✅ [{platform.upper()}] Video Successfully Rendered: {out_video_path} ({render_res['duration']:.1f}s)")
    return {
        "platform": platform,
        "title": title,
        "video_path": str(out_video_path),
        "folder_path": str(video_dir),
        "duration": render_res["duration"]
    }

def create_multiplatform_bundle(
    index: int = 1,
    topic: str = None,
    is_trending: bool = False
) -> dict:
    """
    Creates a full 4-Platform Dedicated Video Bundle in one folder:
    - youtube_short.mp4 (English deep baritone)
    - tiktok_reel.mp4 (Roman Urdu street-smart 0.8s shock hook)
    - instagram_reel.mp4 (Roman Urdu emotional / relational)
    - facebook_reel.mp4 (Roman Urdu moral / desi humor)
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    batch_dir = config.OUTPUT_DIR / today_str
    batch_dir.mkdir(parents=True, exist_ok=True)

    if is_trending:
        trend_info = get_daily_trending_topic()
        selected_topic = trend_info["chosen_topic"]
        raw_trend = trend_info["raw_trend"]
        category = "Breaking Daily Trend"
        bundle_tag = "TRENDING"
        scripts_pack = generate_trending_topic_script(raw_trend)
    elif topic:
        selected_topic = topic
        category = "Custom Strategy"
        bundle_tag = "CUSTOM"
        scripts_pack = generate_viral_script(selected_topic)
    else:
        topic_info = get_todays_winning_topic()
        selected_topic = topic_info["chosen_topic"]
        category = topic_info.get("category", "Psychology")
        bundle_tag = "VIRAL"
        scripts_pack = generate_viral_script(selected_topic)

    clean_name = "".join(c for c in selected_topic if c.isalnum() or c in (" ", "_", "-")).rstrip()[:35].replace(" ", "_")
    bundle_dir = batch_dir / f"bundle_{index}_{bundle_tag}_{clean_name}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir = bundle_dir / "scenes"

    print(f"\n=======================================================")
    print(f"📦 CREATING 4-PLATFORM DEDICATED BUNDLE #{index} [{bundle_tag}]")
    print(f"🎯 Master Topic: '{selected_topic}' ({category})")
    print(f"=======================================================")

    platforms_data = scripts_pack.get("platforms", {})
    created_videos = {}

    for plat in ["youtube", "tiktok", "instagram", "facebook"]:
        plat_script_info = platforms_data.get(plat, {})
        script_text = plat_script_info.get("script", "")
        voice = PLATFORM_VOICE_MAP.get(plat, "english")
        out_vid_name = f"{plat}_short.mp4" if plat == "youtube" else f"{plat}_reel.mp4"
        out_vid_path = bundle_dir / out_vid_name

        print(f"   🎬 Rendering dedicated {plat.upper()} video ({voice.upper()})...")
        try:
            render_res = render_pipeline_video(
                script_text=script_text,
                output_video_path=out_vid_path,
                voice=voice,
                temp_suffix=f"{plat}_{index}",
                scenes_dir=scenes_dir
            )
            created_videos[plat] = {
                "file": str(out_vid_path),
                "duration": render_res["duration"],
                "title": plat_script_info.get("title", f"{plat.capitalize()} #{index}")
            }
        except Exception as e:
            print(f"   ⚠️ Warning: Failed rendering {plat}: {e}")

    # Backward compatibility: copy youtube_short.mp4 as final_video_{index}.mp4
    yt_vid = bundle_dir / "youtube_short.mp4"
    compat_vid = bundle_dir / f"final_video_{index}.mp4"
    if yt_vid.exists():
        shutil.copyfile(yt_vid, compat_vid)

    # Save comprehensive publish pack
    yt = platforms_data.get("youtube", {})
    tt = platforms_data.get("tiktok", {})
    ig = platforms_data.get("instagram", {})
    fb = platforms_data.get("facebook", {})

    pack_content = f"""======================================================
🚀 4-PLATFORM PUBLISHING PACK (COPY & PASTE READY)
Date: {today_str} | Topic: {selected_topic} | Category: {category}
======================================================

🔴 1. YOUTUBE SHORTS (Video: youtube_short.mp4):
------------------------------------------------------
TITLE:
{yt.get('title', selected_topic)}

DESCRIPTION:
{yt.get('description', '')}

KEYWORDS / TAGS:
{', '.join(yt.get('tags', []))}

📌 PINNED COMMENT:
{yt.get('pinned_comment', '')}

------------------------------------------------------
⚫ 2. TIKTOK (Video: tiktok_reel.mp4):
------------------------------------------------------
CAPTION:
{tt.get('caption', '')} {tt.get('hashtags', '')}

------------------------------------------------------
🟣 3. INSTAGRAM REELS (Video: instagram_reel.mp4):
------------------------------------------------------
CAPTION:
{ig.get('caption', '')}

HASHTAGS:
{ig.get('hashtags', '')}

------------------------------------------------------
🔵 4. FACEBOOK REELS (Video: facebook_reel.mp4):
------------------------------------------------------
CAPTION:
{fb.get('caption', '')}

======================================================
"""
    with open(bundle_dir / "publish_pack.txt", "w", encoding="utf-8") as f:
        f.write(pack_content)

    log_generated_video(
        title=f"Bundle #{index}: {selected_topic}",
        topic=selected_topic,
        category=category,
        folder_path=str(bundle_dir),
        duration=created_videos.get("youtube", {}).get("duration", 35.0)
    )

    print(f"🎉 4-Platform Bundle #{index} Complete! Saved in: {bundle_dir}\n")
    return {
        "bundle_dir": str(bundle_dir),
        "topic": selected_topic,
        "category": category,
        "videos": created_videos
    }

def create_single_video(index: int = 1, topic: str = None, mode: str = "short", voice: str = "english") -> dict:
    """Standard entry point for backward compatibility."""
    res = create_platform_video(platform="youtube", topic=topic, index=index, mode=mode)
    return {
        "title": res["title"],
        "video_path": res["video_path"],
        "publish_pack_path": str(Path(res["folder_path"]) / "publish_pack.txt"),
        "duration": res["duration"]
    }

def main():
    parser = argparse.ArgumentParser(description="Autonomous Platform-Dedicated Video Generator")
    parser.add_argument("--platform", type=str, default="bundle", choices=["youtube", "tiktok", "instagram", "facebook", "bundle", "trending"], help="Platform or bundle mode")
    parser.add_argument("--count", type=int, default=1, help="Number of items to generate (default: 1)")
    parser.add_argument("--index", type=int, default=1, help="Starting index (default: 1)")
    parser.add_argument("--topic", type=str, default=None, help="Optional specific topic")
    parser.add_argument("--mode", type=str, default="short", choices=["short", "long"], help="Video duration mode for YouTube")
    args = parser.parse_args()

    print("\n" + "="*50)
    print("🚀 STARTING APEX MEDIA AUTONOMOUS ENGINE")
    print(f"🎯 Target: {args.platform.upper()} | Count: {args.count} | Mode: {args.mode.upper()}")
    print("="*50)

    for i in range(args.index, args.index + args.count):
        if args.platform == "bundle":
            create_multiplatform_bundle(index=i, topic=args.topic, is_trending=False)
        elif args.platform == "trending":
            create_multiplatform_bundle(index=i, topic=args.topic, is_trending=True)
        else:
            create_platform_video(platform=args.platform, topic=args.topic, index=i, mode=args.mode)

    print("\n✅ All jobs completed successfully!")

if __name__ == "__main__":
    main()

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import config
from voice_generator import generate_voiceover
from media_manager import download_3d_image, get_ffmpeg_exe, FALLBACK_VISUALS, ULTRA_VISUALS_DIR
import subprocess

# Fix Windows console encoding for UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = config.BASE_DIR
STORY_FACTORY_DIR = BASE_DIR / "story_factory"
SFX_DIR = config.ASSETS_DIR / "sfx"

# Default kid-friendly storytelling voice
STORY_VOICE = "english"  # en-US-ChristopherNeural (or en-IN-PrabhatNeural)

def render_batch_video(
    batch_info: dict,
    scenes_list: list,
    output_mp4: Path,
    voice: str = STORY_VOICE,
    batch_idx: int = 1
) -> dict:
    """
    Renders one 30-40 second video batch for CapCut editing:
    - Combines scene texts into a continuous storytelling voiceover.
    - Generates 3D visual scenes matching the locked Character Bible.
    - Creates Ken Burns pan/zoom animation.
    - Blends subtle ambient music.
    - Compiles to a 1080x1920 MP4 file.
    """
    ffmpeg_exe = get_ffmpeg_exe()
    temp_dir = config.TEMP_DIR / f"story_batch_{batch_idx}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🎬 Rendering {batch_info['filename']} ({batch_info['duration']}s)...")

    # 1. Combine spoken dialogue/narration
    full_batch_script = " ".join(s["spoken_english"] for s in scenes_list)
    voice_res = generate_voiceover(full_batch_script, output_filename=f"voice_batch_{batch_idx}.mp3", voice=voice)
    audio_path = Path(voice_res["audio_path"])
    actual_duration = max(voice_res["duration"], float(batch_info["duration"]))

    # 2. Generate 3D visuals for each scene in the batch
    scene_clips = []
    duration_per_scene = actual_duration / len(scenes_list)

    for idx, sc in enumerate(scenes_list):
        img_path = temp_dir / f"scene_{sc['scene']}_3d.jpg"
        prompt = sc.get("visual_prompt", "3D animation, Suhail and Sophia in dark mystery forest, unreal engine 5")
        
        print(f"   🎨 Generating 3D Scene #{sc['scene']}: '{sc['spoken_english'][:40]}...'")
        success = download_3d_image(prompt, img_path)
        if not success or not img_path.exists():
            # Use diverse high-res fallback
            fallback_name = FALLBACK_VISUALS[(sc['scene'] - 1) % len(FALLBACK_VISUALS)]
            local_fb = ULTRA_VISUALS_DIR / fallback_name
            if local_fb.exists():
                import shutil
                shutil.copyfile(local_fb, img_path)

        # Generate animated video clip for this scene (Ken Burns effect)
        clip_path = temp_dir / f"clip_{sc['scene']}.mp4"
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-t", f"{duration_per_scene:.2f}",
            "-vf", (
                f"scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,"
                f"zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1080x1920:fps=30"
            ),
            "-c:v", config.VIDEO_ENCODER,
            "-pix_fmt", "yuv420p",
            str(clip_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            # CPU fallback
            cmd[cmd.index(config.VIDEO_ENCODER)] = "libx264"
            subprocess.run(cmd, capture_output=True, text=True)
        scene_clips.append(clip_path)

    # 3. Concatenate scene clips
    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for c in scene_clips:
            clean_p = str(c).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    concatenated_bg = temp_dir / "concatenated_bg.mp4"
    cmd_concat = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(concatenated_bg)
    ]
    subprocess.run(cmd_concat, capture_output=True, text=True)

    # 4. Mix voiceover and ambient music into final batch MP4
    bgm_path = config.ASSETS_DIR / "music" / "dark_ambient.mp3"
    inputs = ["-i", str(concatenated_bg), "-i", str(audio_path)]
    
    if bgm_path.exists():
        inputs.extend(["-i", str(bgm_path)])
        audio_filter = "[1:a]volume=1.30[voice];[2:a]volume=0.12[bgm];[voice][bgm]amix=inputs=2:duration=first[aout]"
    else:
        audio_filter = "[1:a]volume=1.30[aout]"

    cmd_final = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", audio_filter,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "4.5M",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_mp4)
    ]
    res_final = subprocess.run(cmd_final, capture_output=True, text=True)
    if res_final.returncode != 0:
        cmd_final[cmd_final.index(config.VIDEO_ENCODER)] = "libx264"
        subprocess.run(cmd_final, capture_output=True, text=True)

    print(f"   ✓ Batch rendered successfully: {output_mp4} ({actual_duration:.1f}s)")
    return {
        "batch_file": str(output_mp4),
        "duration": actual_duration
    }

def synthesize_episode_batches(story_folder: str = "Story_A_The_Haunted_Frequency", episode: int = 1) -> dict:
    """
    Master pipeline:
    1. Loads the 15-scene script.
    2. Renders all 4 batches into /To_Edit/ and /Generated_Batches/.
    3. Writes the CapCut Roman Urdu guide.
    """
    story_root = STORY_FACTORY_DIR / story_folder
    scripts_dir = story_root / "Scripts"
    gen_dir = story_root / "Generated_Batches"
    to_edit_dir = story_root / "To_Edit"
    
    script_file = scripts_dir / f"Ep{episode:02d}_Scenes.json"
    if not script_file.exists():
        from story_engine import generate_curated_episode_1, save_episode_script
        data = generate_curated_episode_1()
        save_episode_script(data)
    else:
        with open(script_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    batches_config = data.get("batches", [])
    scenes_by_num = {s["scene"]: s for s in data.get("scenes", [])}

    print(f"\n=======================================================")
    print(f"🎬 SYNTHESIZING EPISODE {episode} ({len(batches_config)} BATCHES)")
    print(f"📖 Story: {data.get('story_title', 'Sci-Fi Story')}")
    print(f"🎯 Destination: {to_edit_dir}")
    print(f"=======================================================")

    rendered_batches = []

    for b in batches_config:
        batch_num = b["batch"]
        batch_filename = b["filename"]
        batch_scenes = [scenes_by_num[s_num] for s_num in b["scenes"] if s_num in scenes_by_num]
        
        target_to_edit = to_edit_dir / batch_filename
        target_archive = gen_dir / batch_filename

        res = render_batch_video(
            batch_info=b,
            scenes_list=batch_scenes,
            output_mp4=target_to_edit,
            batch_idx=batch_num
        )
        
        # Also copy to Generated_Batches archive
        import shutil
        shutil.copyfile(target_to_edit, target_archive)

        rendered_batches.append(res)

    # 4. Generate CapCut Roman Urdu Guide
    guide_path = to_edit_dir / f"StoryA_Ep{episode:02d}_CapCut_Guide.txt"
    guide_lines = [
        "========================================================",
        f"🎬 CAPCUT ASSEMBLY GUIDE — EPISODE {episode}: {data.get('episode_title', 'Episode')}",
        "========================================================",
        "HOW TO ASSEMBLE IN CAPCUT IN 3 MINUTES:",
        "1. Open CapCut, drag and drop the 4 batch videos in order:",
        "   - StoryA_Ep01_Batch1.mp4 (Scenes 1 to 4)",
        "   - StoryA_Ep01_Batch2.mp4 (Scenes 5 to 8)",
        "   - StoryA_Ep01_Batch3.mp4 (Scenes 9 to 12)",
        "   - StoryA_Ep01_Batch4.mp4 (Scenes 13 to 15)",
        "2. Add smooth Cut / Glitch / Dissolve transitions between batches.",
        "3. Copy-paste the Roman Urdu subtitles below onto the video timeline.",
        "4. Export as ONE single video named: StoryA_Ep01_FINAL.mp4",
        "5. Drop StoryA_Ep01_FINAL.mp4 into the '/Ready/' folder!",
        "========================================================",
        "📜 LINE-BY-LINE ROMAN URDU SUBTITLES:",
        "========================================================"
    ]

    for s in data.get("scenes", []):
        guide_lines.append(f"Scene {s['scene']:02d} [{s['spoken_english']}]:")
        guide_lines.append(f"   ➤ SUBTITLE: {s['roman_urdu']}")
        guide_lines.append("")

    guide_lines.append("========================================================")
    guide_lines.append("📌 END-CARD CTA (ADD AT 2:20 - 2:30):")
    guide_lines.append("   'Watch Full Story — Subscribe & Follow For Episode 2!'")
    guide_lines.append("========================================================")

    with open(guide_path, "w", encoding="utf-8") as f:
        f.write("\n".join(guide_lines))

    print(f"\n📄 Saved CapCut Editing Guide to: {guide_path}")
    print(f"🎉 All 4 Batches Ready in: {to_edit_dir}\n")

    return {
        "status": "success",
        "story": story_folder,
        "episode": episode,
        "batches": rendered_batches,
        "guide_path": str(guide_path)
    }

def main():
    parser = argparse.ArgumentParser(description="4-Batch Video Synthesizer for Kids Sci-Fi Story Factory")
    parser.add_argument("--story", type=str, default="Story_A_The_Haunted_Frequency")
    parser.add_argument("--episode", type=int, default=1)
    args = parser.parse_args()

    synthesize_episode_batches(story_folder=args.story, episode=args.episode)

if __name__ == "__main__":
    main()

import os
import random
import subprocess
from pathlib import Path
import imageio_ffmpeg
import config

import time
import urllib.request
import urllib.parse
from PIL import Image

ULTRA_VISUALS_DIR = config.ASSETS_DIR / "ultra_visuals"

# Comprehensive local fallback pool with all 19 ultra-HD visuals
FALLBACK_VISUALS = [
    "dark_statue.jpg", "chess_king.jpg", "eye_macro.jpg", "fog_silhouette.jpg",
    "brain_synapse.jpg", "dark_tunnel.jpg", "shattered_mirror.jpg", "chess_strategy.jpg",
    "dark_smoke.jpg", "eye_shadow.jpg", "mysterious_man.jpg", "neon_geometry.jpg",
    "theme_brain.jpg", "theme_chess.jpg", "theme_crowd.jpg", "theme_eye.jpg",
    "theme_feet.jpg", "theme_silhouette.jpg", "theme_whisper.jpg"
]

def get_ffmpeg_exe():
    return imageio_ffmpeg.get_ffmpeg_exe()

def generate_3d_prompt_for_text(text: str, index: int) -> str:
    """
    Synthesizes a rich 3D cinematic Unreal Engine 5 / Octane prompt matching the spoken text.
    """
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["disrespect", "insult", "anger", "angry", "shout", "react", "attack", "fight"]):
        scene = "stoic marble man standing perfectly calm and unmoved in a dark raging tempest, lightning rim lighting"
    elif any(w in text_lower for w in ["currency", "steal", "puppet", "string", "control", "manipulat", "trap", "trap"]):
        scene = "glowing crimson marionette puppet strings dissolving into dark mist, psychological silhouette"
    elif any(w in text_lower for w in ["silent", "silence", "eye", "stare", "gaze", "look", "watch", "contact"]):
        scene = "extreme macro close-up of intense stoic golden eye staring in pitch darkness, cinematic volumetric mist"
    elif any(w in text_lower for w in ["shatter", "ego", "destroy", "chess", "king", "collapse", "defeat", "fall"]):
        scene = "towering obsidian chess king piece shattering into glowing crystal fragments on black reflective glass"
    elif any(w in text_lower for w in ["mirror", "reflect", "insecurity", "weak", "hide", "expose"]):
        scene = "dark antique cracked mirror reflecting a mysterious shadowy figure, volumetric atmospheric fog"
    elif any(w in text_lower for w in ["untouchable", "armor", "statue", "calm", "shield", "power", "win", "high-value"]):
        scene = "monolithic stoic warrior statue surrounded by dark fog, glowing amber rim lighting, cinematic depth of field"
    elif any(w in text_lower for w in ["feet", "foot", "shoe", "floor", "walk", "door", "exit", "step", "leave"]):
        scene = "cinematic low angle of leather boots walking down a dark moody corridor with neon reflections"
    elif any(w in text_lower for w in ["brain", "mind", "subconscious", "memory", "thought", "psycholog"]):
        scene = "translucent crystalline human brain glowing with electric blue neural synapses in deep void"
    elif any(w in text_lower for w in ["whisper", "liar", "deceit", "fake", "mask", "secret", "betray"]):
        scene = "cracked porcelain smiling theater mask floating in dark moody smoke, dramatic side rim light"
    elif any(w in text_lower for w in ["crowd", "people", "room", "party", "meeting", "society"]):
        scene = "calm stoic figure standing motionless amidst blurred ghostly silhouettes in dark moody hall"
    else:
        scene = "mysterious cloaked stoic figure standing in dark atmospheric rain, dramatic golden rim light"

    return f"3D cinematic render, {scene}, dark psychology aesthetic, octane render, unreal engine 5, dramatic rim lighting, photorealistic, 8k vertical portrait"

def download_3d_image(prompt: str, out_path: Path, max_retries: int = 2) -> bool:
    """
    Downloads an AI-generated 3D image from Pollinations AI, crops watermarks, and saves locally.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&nologo=true&seed={seed}"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    img_data = response.read()
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    
                    # Clean any watermark from bottom 45px using PIL
                    try:
                        im = Image.open(out_path)
                        w, h = im.size
                        im.crop((0, 0, w, h - 45)).save(out_path)
                    except Exception:
                        pass
                    return True
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))
            continue
            
    return False

def get_scene_image(text: str, index: int, scenes_dir: Path) -> Path:
    """
    Generates a unique 3D visual matching the spoken text, or falls back to diverse local library.
    """
    img_filename = f"scene_{index}_3d.jpg"
    img_path = scenes_dir / img_filename
    
    # Generate 3D image prompt
    prompt = generate_3d_prompt_for_text(text, index)
    print(f"   🎨 [3D Scene {index+1}] Generating custom visual matching: '{text[:45]}...'")
    
    success = download_3d_image(prompt, img_path)
    if success and img_path.exists() and img_path.stat().st_size > 5000:
        print(f"      ✓ 3D render generated successfully ({img_path.stat().st_size // 1024} KB)")
        time.sleep(1.5)  # Safe spacing for next scene
        return img_path

    # Fallback to local ultra-HD library if network fails
    fallback_name = FALLBACK_VISUALS[index % len(FALLBACK_VISUALS)]
    fallback_path = ULTRA_VISUALS_DIR / fallback_name
    if fallback_path.exists():
        print(f"      ↳ Used HD backup asset: {fallback_name}")
        return fallback_path
    
    all_imgs = list(ULTRA_VISUALS_DIR.glob("*.jpg"))
    return all_imgs[0] if all_imgs else config.ASSETS_DIR / "default.jpg"


def render_ken_burns_clip(image_path: Path, duration: float, output_path: Path, zoom_in: bool = True):
    """
    Renders an image into a smooth Ken Burns motion clip of specified duration.
    """
    ffmpeg_exe = get_ffmpeg_exe()
    fps = config.VIDEO_FPS
    total_frames = int(max(duration * fps, 30))
    
    if zoom_in:
        zoom_expr = "min(zoom+0.0015,1.22)"
    else:
        zoom_expr = "max(1.22-0.0015*on,1.0)"
        
    filter_graph = (
        f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}:fps={fps}"
    )
    
    cmd = [
        ffmpeg_exe, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", filter_graph,
        "-t", f"{duration:.2f}",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "5M",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(output_path)

def prepare_contextual_background(sentences: list, total_duration: float, target_video_path: Path, scenes_dir: Path = None) -> str:
    """
    Creates a dynamic multi-scene background where visuals change according to what
    is being spoken in each sentence, using Ken Burns zoom transitions!
    """
    scenes = []
    current_chunk = []
    current_start = 0.0
    
    for s in sentences:
        if not current_chunk:
            current_start = s["start"]
        current_chunk.append(s["text"])
        chunk_duration = s["end"] - current_start
        
        # Pacing: 4.5s to 7.0s per visual scene
        if chunk_duration >= 4.5 or s == sentences[-1]:
            scenes.append({
                "text": " ".join(current_chunk),
                "duration": chunk_duration
            })
            current_chunk = []
            
    if not scenes:
        scenes = [{"text": "dark psychology", "duration": total_duration}]
        
    sum_dur = sum(sc["duration"] for sc in scenes)
    if sum_dur < total_duration:
        scenes[-1]["duration"] += (total_duration - sum_dur)

    if scenes_dir is None:
        scenes_dir = config.TEMP_DIR / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    print(f"🎬 Assembling {len(scenes)} dynamic 3D visual scenes...")
    for idx, sc in enumerate(scenes):
        img_path = get_scene_image(sc["text"], idx, scenes_dir)
        clip_path = scenes_dir / f"scene_{idx}.mp4"
        zoom_in = (idx % 2 == 0)
        render_ken_burns_clip(img_path, sc["duration"], clip_path, zoom_in=zoom_in)
        clip_paths.append(clip_path)

    # Concatenate all scene clips into one final background
    concat_list_file = scenes_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            safe_p = str(cp).replace("\\", "/")
            f.write(f"file '{safe_p}'\n")

    ffmpeg_exe = get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-t", f"{total_duration:.2f}",
        "-c", "copy",
        str(target_video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(target_video_path)

def prepare_music(duration: float, target_music_path: Path) -> str:
    """
    Prepares subtle dark suspense ambient drone.
    """
    ffmpeg_exe = get_ffmpeg_exe()
    filter_expr = "0.06*sin(2*PI*55*t)+0.03*sin(2*PI*82.4*t)+0.02*sin(2*PI*110*t)"
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", f"aevalsrc={filter_expr}:s=44100",
        "-t", f"{duration + 0.5:.2f}",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(target_music_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(target_music_path)

import os
import sys
import asyncio
import subprocess
from pathlib import Path
import imageio_ffmpeg
import edge_tts
import config

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

SCENES = [
    {
        "id": "scene1",
        "speaker": "Khalid",
        "voice": "ur-IN-SalmanNeural",
        "rate": "+2%",
        "pitch": "+0Hz",
        "audio_text": "سہیل بھائی... وہ ہر طرف سے آگے بڑھ رہے ہیں۔ شاید ہم نہیں نکل پائیں گے۔",
        "subtitles": [
            ("Suhail bhai... woh har taraf se agay barh rahe hain.", 0.0, 0.52),
            ("Shayad hum yahan se nahi nikal payenge.", 0.52, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene1_khalid.jpg",
        "zoom_in": True
    },
    {
        "id": "scene2",
        "speaker": "Suhail",
        "voice": "ur-PK-AsadNeural",
        "rate": "-5%",
        "pitch": "-2Hz",
        "audio_text": "خالد! میری طرف دیکھو۔ میں نے وعدہ کیا تھا... ہم سب ایک ساتھ واپس جائیں گے!",
        "subtitles": [
            ("Khalid! Meri taraf dekho.", 0.0, 0.42),
            ("Maine wada kiya tha... hum sab sath wapis jayenge!", 0.42, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene2_suhail_khalid.jpg",
        "zoom_in": False
    },
    {
        "id": "scene3",
        "speaker": "Awais [Radio]",
        "voice": "ur-PK-AsadNeural",
        "rate": "+5%",
        "pitch": "+4Hz",
        "audio_text": "سہیل! اویس بول رہا ہوں۔ ایکسٹرکشن تین منٹ میں نارتھ رج پر پہنچ رہی ہے! بس تھوڑا وقت نکالو!",
        "subtitles": [
            ("Suhail! Awais bol raha hoon.", 0.0, 0.35),
            ("Extraction 3 minute mein pohnch rahi hai... bas thora waqt nikalo!", 0.35, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene3_awais.jpg",
        "zoom_in": True
    },
    {
        "id": "scene4",
        "speaker": "Suhail",
        "voice": "ur-PK-AsadNeural",
        "rate": "-4%",
        "pitch": "-2Hz",
        "audio_text": "سن لیا؟ کوئی بھائی پیچھے نہیں رہے گا۔ چلو خالد، راستہ ہم خود بنائیں گے!",
        "subtitles": [
            ("Sun liya? Koi bhai peechay nahi rahega.", 0.0, 0.48),
            ("Chalo Khalid... rasta hum khud banayenge!", 0.48, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene4_suhail.jpg",
        "zoom_in": False
    },
    {
        "id": "scene5",
        "speaker": "Suhail",
        "voice": "ur-PK-AsadNeural",
        "rate": "-8%",
        "pitch": "-3Hz",
        "audio_text": "کیونکہ سچے بھائی حالات دیکھ کر ہاتھ نہیں چھوڑتے... وہ ساتھ نبھاتے ہیں۔",
        "subtitles": [
            ("Kyunke sachay bhai halaat dekh kar haath nahi chhorrte...", 0.0, 0.50),
            ("Woh aakhri saans tak saath nibhatay hain.", 0.50, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene5_finale.jpg",
        "zoom_in": True
    }
]

def get_audio_duration(file_path: Path) -> float:
    cmd = [
        FFMPEG_EXE, "-i", str(file_path),
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    import re
    m = re.findall(r"time=(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        h, mn, s = m[-1]
        return int(h) * 3600 + int(mn) * 60 + float(s)
    return 5.0

async def generate_speech_for_scene(scene: dict, output_path: Path) -> float:
    comm = edge_tts.Communicate(
        scene["audio_text"],
        scene["voice"],
        rate=scene["rate"],
        pitch=scene["pitch"]
    )
    await comm.save(str(output_path))
    return get_audio_duration(output_path)

def render_scene_clip(image_path: Path, audio_path: Path, duration: float, out_path: Path, zoom_in: bool):
    """
    Renders a single scene with Ken Burns motion and audio directly attached.
    """
    fps = config.VIDEO_FPS
    total_frames = int(max(duration * fps, 30))
    if zoom_in:
        zoom_expr = "min(zoom+0.0016,1.25)"
    else:
        zoom_expr = "max(1.25-0.0016*on,1.0)"
    
    video_filter = (
        f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}:fps={fps}"
    )
    
    # Pad audio with slight silence if audio is shorter than total clip duration
    audio_filter = f"apad=whole_dur={duration:.2f}"
    
    cmd = [
        FFMPEG_EXE, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-vf", video_filter,
        "-af", audio_filter,
        "-t", f"{duration:.2f}",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "6M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(out_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # Fallback to libx264
        cmd[cmd.index(config.VIDEO_ENCODER)] = "libx264"
        cmd.extend(["-preset", "ultrafast"])
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_ass_subtitles(scenes, scene_timings, ass_path: Path):
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {config.VIDEO_WIDTH}
PlayResY: {config.VIDEO_HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MovieSub,Arial,66,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5.0,2.0,2,40,40,320,1
Style: SpeakerTag,Arial,48,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,40,40,410,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    
    def format_ts(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        cs = int((s - int(s)) * 100)
        return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"

    for sc, timing in zip(scenes, scene_timings):
        sc_start = timing["start"]
        sc_dur = timing["duration"]
        speaker = sc["speaker"]
        
        t_start_str = format_ts(sc_start)
        t_end_str = format_ts(sc_start + sc_dur)
        events.append(f"Dialogue: 1,{t_start_str},{t_end_str},SpeakerTag,,0,0,0,,{{\\fad(120,120)}}[ {speaker.upper()} ]")
        
        for sub_text, frac_start, frac_end in sc["subtitles"]:
            p_start = sc_start + (frac_start * sc_dur)
            p_end = sc_start + (frac_end * sc_dur)
            p_start_str = format_ts(p_start)
            p_end_str = format_ts(p_end)
            anim = "{\\t(0,100,\\fscx106\\fscy106)\\t(100,200,\\fscx100\\fscy100)}"
            events.append(f"Dialogue: 2,{p_start_str},{p_end_str},MovieSub,,0,0,0,,{anim}{sub_text}")
            
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))

def create_tension_music(total_duration: float, music_path: Path):
    filter_expr = "0.06*sin(2*PI*50*t)+0.03*sin(2*PI*75*t)+0.02*sin(2*PI*100*t)"
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi",
        "-i", f"aevalsrc={filter_expr}:s=44100",
        "-t", f"{total_duration + 1.0:.2f}",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(music_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_publish_pack(output_folder: Path):
    pack_text = """================================================================================
4-PLATFORM CINEMATIC REEL PUBLISHING PACK
STARRING: SUHAIL, KHALID & AWAIS
TITLE: THE BROTHERHOOD PROMISE (ہم سب ایک ساتھ واپس جائیں گے)
================================================================================

[1] INSTAGRAM REELS (TARGET: HIGH-ENGAGEMENT URDU / PAKISTANI AUDIENCE)
--------------------------------------------------------------------------------
AUDIO: Original Audio (Urdu Cinematic Dialogue)
CAPTION:
"Hum ne wada kiya tha... koi bhai peechay nahi rahega! 🤝🔥"
Tag that one brother who will stand by you no matter how tough the war gets.

Follow for more high-octane cinematic stories!
#Brotherhood #Loyalty #Dosti #UrduStory #CinematicReel #Suhail #BrothersForLife #ActionMovie #Pakistan #ViralReel #ShortFilm #TrendingReels

[2] YOUTUBE SHORTS (TARGET: GLOBAL HIGH-CPM & VIRAL ACTION)
--------------------------------------------------------------------------------
TITLE:
The Brotherhood Promise: No Soldier Left Behind 💥🎖️ #Shorts #Cinematic

DESCRIPTION:
Surrounded in enemy ruins, Khalid thinks it's the end. But Suhail made a promise: they all make it out together. An intense AI cinematic short film about loyalty, brotherhood, and survival.

Cast:
- Suhail (Squad Leader)
- Khalid (Vanguard)
- Awais (Radio Specialist)

Subscribe for daily 8K cinematic short films!

TAGS:
brotherhood, survival drama, cinematic shorts, ai short film, military action, loyalty, suhail, emotional story, youtube shorts viral, 8k cinematic, brotherhood status, action movie clip

PINNED COMMENT:
"Would you ever leave a brother behind? Drop a ❤️ if you believe in true loyalty!"

[3] TIKTOK (TARGET: VIRAL YOUTH & HIGH RETENTION)
--------------------------------------------------------------------------------
CAPTION:
Koi bhai peechay nahi rahega! Tag your realest friend 💯🔥 #brotherhood #loyalty #cinematic #fyp #viral #storytime #action #friends #foryou #foryoupage

[4] FACEBOOK REELS (TARGET: EMOTIONAL STORYTELLING & VIRAL SHARES)
--------------------------------------------------------------------------------
CAPTION:
"سچے دوست حالات دیکھ کر ساتھ نہیں چھوڑتے... وہ ساتھ نبھاتے ہیں۔"
A gripping short film about the power of friendship and never giving up on each other. Share this with your best friends who always have your back!
#Dosti #BhaiChara #UrduStories #EmotionalDrama #FacebookReels #FriendshipGoals
================================================================================
"""
    pack_path = output_folder / "publish_pack.txt"
    with open(pack_path, "w", encoding="utf-8") as f:
        f.write(pack_text)
    print(f"-> Created 4-Platform Publish Pack at: {pack_path}")

async def main():
    print("="*60)
    print("  BUILDING AI CINEMATIC SHORT REEL: THE BROTHERHOOD PROMISE")
    print("="*60)
    
    temp_dir = config.TEMP_DIR / "story_build"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    out_dir = config.OUTPUT_DIR / "story_brotherhood_promise"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate Voice Audios and build Scene Clips
    scene_clips = []
    scene_timings = []
    current_time = 0.0
    
    print("-> Processing scenes (TTS + Ken Burns Motion)...")
    for idx, sc in enumerate(SCENES):
        audio_p = temp_dir / f"{sc['id']}.mp3"
        print(f"   [{idx+1}/5] Generating dialogue for {sc['speaker']}...")
        dur = await generate_speech_for_scene(sc, audio_p)
        
        # Add 0.35s conversational pause after line
        clip_dur = dur + 0.35
        scene_timings.append({
            "start": current_time,
            "duration": clip_dur
        })
        current_time += clip_dur
        
        clip_p = temp_dir / f"clip_{sc['id']}.mp4"
        print(f"   Rendering Ken Burns video: {sc['image'].name} ({clip_dur:.2f}s)...")
        render_scene_clip(sc["image"], audio_p, clip_dur, clip_p, sc["zoom_in"])
        scene_clips.append(clip_p)
        
    total_duration = current_time
    print(f"-> Total Story Runtime: {total_duration:.2f} seconds")
    
    # 2. Concatenate scene clips
    concat_list = temp_dir / "clips_concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for cp in scene_clips:
            safe_cp = str(cp).replace("\\", "/")
            f.write(f"file '{safe_cp}'\n")
            
    raw_story = temp_dir / "raw_story.mp4"
    cmd_cat = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(raw_story)
    ]
    subprocess.run(cmd_cat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("-> Concatenated all scenes into unified video stream")
    
    # 3. Generate Subtitles
    ass_path = temp_dir / "story_subtitles.ass"
    generate_ass_subtitles(SCENES, scene_timings, ass_path)
    print("-> Generated cinematic Roman Urdu ASS subtitles")
    
    # 4. Generate Tension Score
    tension_music = temp_dir / "tension_music.mp3"
    create_tension_music(total_duration, tension_music)
    
    # 5. Final Master Render (Burn subs, progress bar, audio mix)
    final_output = out_dir / "final_story_reel.mp4"
    print(f"-> Rendering final master reel to {final_output.name}...")
    
    try:
        rel_sub = os.path.relpath(ass_path, start=config.BASE_DIR).replace("\\", "/")
    except Exception:
        rel_sub = str(ass_path).replace("\\", "/").replace(":", "\\:")
        
    video_filter = f"ass={rel_sub},drawbox=x=0:y=1912:w='1080*(t/{total_duration:.2f})':h=8:color=0x00FFFF@0.95:t=fill"
    
    bass_drop_path = config.ASSETS_DIR / "sfx" / "bass_drop.mp3"
    inputs = [
        "-i", str(raw_story),
        "-i", str(tension_music)
    ]
    
    if bass_drop_path.exists():
        inputs.extend(["-i", str(bass_drop_path)])
        audio_filter = (
            f"[0:a]volume=1.35[voice];"
            f"[1:a]volume=0.10[bgm];"
            f"[2:a]volume=0.35[bass];"
            f"[voice][bgm][bass]amix=inputs=3:duration=first:dropout_transition=2[aout]"
        )
    else:
        audio_filter = (
            f"[0:a]volume=1.35[voice];"
            f"[1:a]volume=0.10[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        
    filter_complex = f"[0:v]{video_filter}[vout];{audio_filter}"
    
    cmd_render = [
        FFMPEG_EXE, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "6M",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_output)
    ]
    
    res = subprocess.run(cmd_render, cwd=str(config.BASE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        cmd_render[cmd_render.index(config.VIDEO_ENCODER)] = "libx264"
        cmd_render.extend(["-preset", "ultrafast", "-crf", "22"])
        subprocess.run(cmd_render, cwd=str(config.BASE_DIR), check=True)
        
    # 6. Generate 4-Platform Publish Pack
    generate_publish_pack(out_dir)
    
    print("\n" + "="*60)
    print(f"  SUCCESS! MASTER VIDEO GENERATED:")
    print(f"  {final_output}")
    print("="*60)
    
    # Open folder and video
    subprocess.run(["explorer.exe", str(out_dir)])
    try:
        os.startfile(str(final_output))
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())

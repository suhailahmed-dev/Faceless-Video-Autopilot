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
        "pitch": "+1Hz",
        "audio_text": "سہیل بھائی!... گولیاں ختم ہو رہی ہیں... وہ چاروں طرف سے آ چکے ہیں! ہم... ہم کیسے بچیں گے بھائی؟!",
        "subtitles": [
            ("Suhail bhai!... Goliyan khatam ho rahi hain!", 0.0, 0.48),
            ("Woh charon taraf se aa chuke hain... Hum kaisay bachenge?!", 0.48, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene1_khalid.jpg",
        "zoom_in": True,
        "sfx_overlay": "heartbeat"
    },
    {
        "id": "scene2",
        "speaker": "Suhail",
        "voice": "ur-PK-AsadNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
        "audio_text": "خالد! میری آنکھوں میں دیکھو۔ گھبرانا نہیں ہے۔ جب تک میں زندہ ہوں، تمہیں کچھ نہیں ہونے دوں گا!",
        "subtitles": [
            ("Khalid! Meri aankhon mein dekho... ghabrana nahi hai.", 0.0, 0.48),
            ("JAB TAK MAIN ZINDA HOON... tumhe kuch nahi hone doonga!", 0.48, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene2_suhail_khalid.jpg",
        "zoom_in": False,
        "sfx_overlay": "bass_drop"
    },
    {
        "id": "scene3",
        "speaker": "Awais [Radio]",
        "voice": "ur-PK-AsadNeural",
        "rate": "+4%",
        "pitch": "+3Hz",
        "audio_text": "سہیل! میں اویس بول رہا ہوں۔ ہیلی کاپٹر نارتھ رج پر پہنچ چکا ہے! صرف دو منٹ سنبھالو بھائی، بس دو منٹ!",
        "subtitles": [
            ("Suhail! Main Awais bol raha hoon.", 0.0, 0.35),
            ("Helicopter pohnch chuka hai! Sirf 2 minute sambhalo bhai!", 0.35, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene3_awais.jpg",
        "zoom_in": True,
        "sfx_overlay": "radio"
    },
    {
        "id": "scene4",
        "speaker": "Suhail",
        "voice": "ur-PK-AsadNeural",
        "rate": "-5%",
        "pitch": "-2Hz",
        "audio_text": "سن لیا خالد؟ راستہ بن چکا ہے۔ اب ہم لڑ کر نکلیں گے... اور ایک ساتھ واپس جائیں گے!",
        "subtitles": [
            ("Sun liya Khalid? Rasta ban chuka hai!", 0.0, 0.45),
            ("Ab hum larr kar nikalenge... aur ek sath wapis jayenge!", 0.45, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene4_suhail.jpg",
        "zoom_in": False,
        "sfx_overlay": "none"
    },
    {
        "id": "scene5",
        "speaker": "Suhail",
        "voice": "ur-PK-AsadNeural",
        "rate": "-10%",
        "pitch": "-3Hz",
        "audio_text": "یاد رکھنا... سچے دوست جیت میں تالیاں نہیں بجاتے، وہ ہارے ہوئے وقت میں کندھا بنتے ہیں۔",
        "subtitles": [
            ("Yaad rakhna... sachay dost jeet mein taaliyan nahi bajatay,", 0.0, 0.50),
            ("Woh haartay huay waqt mein KANDHA bantay hain!", 0.50, 1.0)
        ],
        "image": config.ASSETS_DIR / "story_scenes" / "scene5_finale.jpg",
        "zoom_in": True,
        "sfx_overlay": "bass_drop"
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

async def process_character_audio(scene: dict, raw_path: Path, mastered_path: Path) -> float:
    comm = edge_tts.Communicate(
        scene["audio_text"],
        scene["voice"],
        rate=scene["rate"],
        pitch=scene["pitch"]
    )
    await comm.save(str(raw_path))
    
    if scene["sfx_overlay"] == "radio":
        squelch_p = config.ASSETS_DIR / "sfx" / "radio_squelch.wav"
        if squelch_p.exists():
            cmd = [
                FFMPEG_EXE, "-y",
                "-i", str(squelch_p),
                "-i", str(raw_path),
                "-i", str(squelch_p),
                "-filter_complex",
                "[1:a]highpass=f=450,lowpass=f=2600,volume=1.45,acompressor=threshold=0.1:ratio=5[voice];"
                "[0:a]volume=0.6[s1];[2:a]volume=0.5[s2];"
                "[s1][voice][s2]concat=n=3:v=0:a=1[aout]",
                "-map", "[aout]",
                "-ar", "44100",
                "-ac", "2",
                str(mastered_path)
            ]
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-i", str(raw_path),
                "-af", "highpass=f=450,lowpass=f=2600,volume=1.4",
                "-ar", "44100",
                "-ac", "2",
                str(mastered_path)
            ]
    elif scene["speaker"] == "Suhail":
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(raw_path),
            "-af", "equalizer=f=160:t=q:w=1:g=3.5,equalizer=f=3300:t=q:w=1:g=4,acompressor=threshold=0.15:ratio=4:attack=6:release=70,volume=1.45",
            "-ar", "44100",
            "-ac", "2",
            str(mastered_path)
        ]
    else:
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(raw_path),
            "-af", "equalizer=f=2800:t=q:w=1:g=3.5,equalizer=f=300:t=q:w=1:g=2,acompressor=threshold=0.15:ratio=3.5:attack=8:release=80,volume=1.35",
            "-ar", "44100",
            "-ac", "2",
            str(mastered_path)
        ]
        
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return get_audio_duration(mastered_path)

def render_shocking_scene_clip(
    image_path: Path,
    audio_path: Path,
    duration: float,
    out_path: Path,
    zoom_in: bool,
    sfx_type: str
):
    fps = config.VIDEO_FPS
    total_frames = int(max(duration * fps, 30))
    
    if zoom_in:
        zoom_expr = "min(zoom+0.0020,1.26)"
    else:
        zoom_expr = "max(1.26-0.0020*on,1.0)"
        
    pan_x = "iw/2-(iw/zoom/2) + 12*sin(in/16)"
    pan_y = "ih/2-(ih/zoom/2) + 9*cos(in/14)"
    
    color_grade = "colorbalance=rs=0.07:gs=-0.03:bs=-0.06:rh=0.10:gh=0.04:bh=-0.06,vignette=PI/4.2,noise=alls=7:allf=t+u"
    
    video_filter = (
        f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:x='{pan_x}':y='{pan_y}':s={config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}:fps={fps},"
        f"{color_grade}"
    )
    
    inputs = [
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path)
    ]
    
    if sfx_type == "heartbeat":
        hb_path = config.ASSETS_DIR / "sfx" / "heartbeat.wav"
        if hb_path.exists():
            inputs.extend(["-stream_loop", "-1", "-i", str(hb_path)])
            audio_filter = "[1:a]volume=1.35[v];[2:a]volume=0.35[hb];[v][hb]amix=inputs=2:duration=first:dropout_transition=1[aout]"
        else:
            audio_filter = f"[1:a]apad=whole_dur={duration:.2f}[aout]"
    elif sfx_type == "bass_drop":
        bass_path = config.ASSETS_DIR / "sfx" / "bass_drop.mp3"
        if bass_path.exists():
            inputs.extend(["-i", str(bass_path)])
            audio_filter = "[1:a]volume=1.40[v];[2:a]volume=0.40[bd];[v][bd]amix=inputs=2:duration=first:dropout_transition=1[aout]"
        else:
            audio_filter = f"[1:a]apad=whole_dur={duration:.2f}[aout]"
    else:
        audio_filter = f"[1:a]apad=whole_dur={duration:.2f}[aout]"
        
    filter_complex = f"[0:v]{video_filter}[vout];{audio_filter}"
    
    cmd = [
        FFMPEG_EXE, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", f"{duration:.2f}",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "6M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        str(out_path)
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        cmd[cmd.index(config.VIDEO_ENCODER)] = "libx264"
        cmd.extend(["-preset", "ultrafast"])
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_shocking_ass_subtitles(scenes, scene_timings, ass_path: Path):
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {config.VIDEO_WIDTH}
PlayResY: {config.VIDEO_HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MovieSub,Arial,68,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5.5,2.5,2,40,40,320,1
Style: SuhailTag,Arial,48,&H0000FFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,40,40,415,1
Style: KhalidTag,Arial,48,&H0000D7FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,40,40,415,1
Style: RadioTag,Arial,48,&H0000FF00,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,40,40,415,1

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
        
        if "Radio" in speaker:
            style_tag = "RadioTag"
        elif "Suhail" in speaker:
            style_tag = "SuhailTag"
        else:
            style_tag = "KhalidTag"
            
        events.append(f"Dialogue: 1,{t_start_str},{t_end_str},{style_tag},,0,0,0,,{{\\fad(150,150)}}[ {speaker.upper()} ]")
        
        for sub_text, frac_start, frac_end in sc["subtitles"]:
            p_start = sc_start + (frac_start * sc_dur)
            p_end = sc_start + (frac_end * sc_dur)
            p_start_str = format_ts(p_start)
            p_end_str = format_ts(p_end)
            
            styled_text = sub_text
            for kw in ["JAB TAK MAIN ZINDA HOON", "KANDHA", "Suhail bhai!...", "Extraction", "wapis jayenge"]:
                if kw in styled_text:
                    styled_text = styled_text.replace(kw, f"{{\\c&H0000FFFF&}}{kw}{{\\c&H00FFFFFF&}}")
                    
            anim = "{\\t(0,120,\\fscx108\\fscy108)\\t(120,220,\\fscx100\\fscy100)}"
            events.append(f"Dialogue: 2,{p_start_str},{p_end_str},MovieSub,,0,0,0,,{anim}{styled_text}")
            
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))

def generate_publish_pack(output_folder: Path):
    pack_text = """================================================================================
4-PLATFORM MASTER SHORT FILM PUBLISHING PACK
TITLE: THE BROTHERHOOD STAND (ہم سب ایک ساتھ واپس جائیں گے)
CAST: SUHAIL (HERO LEAD), KHALID (COMPANION), AWAIS (RADIO)
================================================================================

[1] INSTAGRAM REELS (URDU AUDIO + ROMAN URDU HOOK)
--------------------------------------------------------------------------------
AUDIO: Original Audio (Suhail & Khalid Brotherhood Dialogue)
CAPTION:
"جب تک میں زندہ ہوں... تمہیں کچھ نہیں ہونے دوں گا!" 🔥🤝
A brother who stands with you when the whole world walks away.

Tag that one friend who is your permanent armor in life. 💯

#Brotherhood #Loyalty #Dosti #CinematicReel #Suhail #UrduStory #BrothersForLife #ActionFilm #PakistanReels #ViralReel #TrendingUrdu #FriendshipForever

[2] YOUTUBE SHORTS (GLOBAL HIGH-CPM ACTION REACH)
--------------------------------------------------------------------------------
TITLE:
"Until My Last Breath": The Brotherhood Promise 💥🎖️ #Shorts #Cinematic

DESCRIPTION:
Trapped under heavy enemy fire with ammunition running out, Khalid fears the worst. But Squad Leader Suhail made an unbreakable promise: they all make it home together. Experience an emotional, high-octane AI cinematic story about brotherhood, sacrifice, and loyalty.

Starring:
- Suhail (Squad Leader)
- Khalid (Vanguard Scout)
- Awais (Tactical Radio Comms)

Drop a LIKE and SUBSCRIBE for daily 8K cinematic short films!

TAGS:
brotherhood, cinematic shorts, military action, suhail, loyalty story, emotional film, army brotherhood, youtube shorts viral, 8k cinematic, action short film, true friendship status

PINNED COMMENT:
"True friends don't celebrate your wins... they carry you through your darkest wars. Drop a ❤️ if you agree!"

[3] TIKTOK (VIRAL RETENTION & SOUND TREND)
--------------------------------------------------------------------------------
CAPTION:
Sachay dost jeet mein taaliyan nahi bajatay... woh mushkil mein kandha bantay hain 🤝🔥 Tag your best brother! #brotherhood #loyalty #cinematic #fyp #viral #storytime #action #foryou #foryoupage

[4] FACEBOOK REELS (DEEP EMOTIONAL REACH & SHARES)
--------------------------------------------------------------------------------
CAPTION:
"سچے دوست حالات دیکھ کر ہاتھ نہیں چھوڑتے... وہ ساتھ نبھاتے ہیں۔"
A gripping short film about the power of brotherhood and never leaving anyone behind. Share this with the friends who always have your back!
#Dosti #BhaiChara #UrduStories #EmotionalDrama #FacebookReels #FriendshipGoals
================================================================================
"""
    pack_path = output_folder / "publish_pack.txt"
    with open(pack_path, "w", encoding="utf-8") as f:
        f.write(pack_text)

async def main():
    print("="*60)
    print("  BUILDING SHOCKING CINEMATIC MASTERPIECE: THE BROTHERHOOD STAND")
    print("="*60)
    
    temp_dir = config.TEMP_DIR / "shocking_build"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    out_dir = config.OUTPUT_DIR / "story_brotherhood_shocking"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    scene_clips = []
    scene_timings = []
    current_time = 0.0
    
    print("-> Processing character voices with Studio Vocal Mastering & SFX...")
    for idx, sc in enumerate(SCENES):
        raw_audio = temp_dir / f"raw_{sc['id']}.mp3"
        mastered_audio = temp_dir / f"mastered_{sc['id']}.wav"
        
        print(f"   [{idx+1}/5] Mastering voice for {sc['speaker']} ({sc['sfx_overlay']})...")
        dur = await process_character_audio(sc, raw_audio, mastered_audio)
        
        clip_dur = dur + 0.40
        scene_timings.append({
            "start": current_time,
            "duration": clip_dur
        })
        current_time += clip_dur
        
        clip_p = temp_dir / f"clip_{sc['id']}.mp4"
        print(f"   Rendering Cinema Motion: {sc['image'].name} ({clip_dur:.2f}s, shake+color-grade)...")
        render_shocking_scene_clip(sc["image"], mastered_audio, clip_dur, clip_p, sc["zoom_in"], sc["sfx_overlay"])
        scene_clips.append(clip_p)
        
    total_duration = current_time
    print(f"-> Total Short Film Runtime: {total_duration:.2f} seconds")
    
    # 2. Extract separate master video and master audio from clips using filter_complex concat
    # (Avoids AAC bitstream corruption from -c copy)
    print("-> Merging scenes into master timeline...")
    concat_inputs = []
    filter_parts_v = []
    filter_parts_a = []
    for idx, cp in enumerate(scene_clips):
        concat_inputs.extend(["-i", str(cp)])
        filter_parts_v.append(f"[{idx}:v]")
        filter_parts_a.append(f"[{idx}:a]")
        
    n_clips = len(scene_clips)
    v_cat = "".join(filter_parts_v) + f"concat=n={n_clips}:v=1:a=0[vcat]"
    a_cat = "".join(filter_parts_a) + f"concat=n={n_clips}:v=0:a=1[acat]"
    
    raw_story = temp_dir / "raw_story.mp4"
    cmd_cat = [
        FFMPEG_EXE, "-y",
        *concat_inputs,
        "-filter_complex", f"{v_cat};{a_cat}",
        "-map", "[vcat]",
        "-map", "[acat]",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "6M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        str(raw_story)
    ]
    res_cat = subprocess.run(cmd_cat, capture_output=True, text=True)
    if res_cat.returncode != 0:
        # Fallback to ultrafast libx264
        cmd_cat[cmd_cat.index(config.VIDEO_ENCODER)] = "libx264"
        cmd_cat.extend(["-preset", "ultrafast"])
        subprocess.run(cmd_cat, check=True)
    print("-> Successfully merged all scenes with frame-perfect audio sync")
    
    # 3. Subtitles
    ass_path = temp_dir / "shocking_subtitles.ass"
    generate_shocking_ass_subtitles(SCENES, scene_timings, ass_path)
    print("-> Generated dynamic Roman Urdu styled movie subtitles")
    
    # 4. Orchestral Tension Score
    orchestral_drone = config.ASSETS_DIR / "music" / "cinematic_orchestral_drone.wav"
    
    # 5. Final Master Render with hardware acceleration
    final_output = out_dir / "final_story_shocking.mp4"
    print(f"-> Rendering Master 1080x1920 Film to {final_output.name}...")
    
    try:
        rel_sub = os.path.relpath(ass_path, start=config.BASE_DIR).replace("\\", "/")
    except Exception:
        rel_sub = str(ass_path).replace("\\", "/").replace(":", "\\:")
        
    video_filter = f"ass={rel_sub},drawbox=x=0:y=1912:w='1080*(t/{total_duration:.2f})':h=8:color=0x00FFFF@0.95:t=fill"
    
    inputs = [
        "-i", str(raw_story),
        "-i", str(orchestral_drone)
    ]
    
    audio_filter = (
        f"[0:a]volume=1.35[voice_and_sfx];"
        f"[1:a]volume=0.18[score];"
        f"[voice_and_sfx][score]amix=inputs=2:duration=first:dropout_transition=2[aout]"
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
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        "-shortest",
        str(final_output)
    ]
    
    res = subprocess.run(cmd_render, cwd=str(config.BASE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        cmd_render[cmd_render.index(config.VIDEO_ENCODER)] = "libx264"
        cmd_render.extend(["-preset", "ultrafast", "-crf", "20"])
        subprocess.run(cmd_render, cwd=str(config.BASE_DIR), check=True)
        
    # 6. Publishing Pack
    generate_publish_pack(out_dir)
    print(f"-> Generated 4-Platform Publish Pack in {out_dir}")
    
    print("\n" + "="*60)
    print(f"  MASTERPIECE GENERATED SUCCESSFULLY!")
    print(f"  File: {final_output}")
    print("="*60)
    
    subprocess.run(["explorer.exe", str(out_dir)])
    try:
        os.startfile(str(final_output))
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())

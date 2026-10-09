import os
import subprocess
from pathlib import Path
import imageio_ffmpeg
import config

SFX_DIR = config.ASSETS_DIR / "sfx"

def get_ffmpeg_exe():
    return imageio_ffmpeg.get_ffmpeg_exe()

def assemble_final_video(
    background_path: Path,
    voice_audio_path: Path,
    music_audio_path: Path,
    ass_subtitle_path: Path,
    output_video_path: Path,
    duration: float = 35.0
) -> str:
    """
    Blends background video, voiceover, background music, sub-bass SFX,
    animated subtitles, and glowing progress bar into an ultra-high retention 1080x1920 MP4.
    """
    ffmpeg_exe = get_ffmpeg_exe()
    
    try:
        rel_sub_path = os.path.relpath(ass_subtitle_path, start=config.BASE_DIR).replace("\\", "/")
    except Exception:
        rel_sub_path = str(ass_subtitle_path).replace("\\", "/").replace(":", "\\:")

    # Animated progress bar at bottom (glowing electric yellow line)
    safe_duration = max(duration, 5.0)
    video_filter = f"ass={rel_sub_path},drawbox=x=0:y=1912:w='1080*(t/{safe_duration:.2f})':h=8:color=0x00FFFF@0.95:t=fill"

    bass_drop_path = SFX_DIR / "bass_drop.mp3"
    inputs = [
        "-i", str(background_path),
        "-i", str(voice_audio_path),
        "-i", str(music_audio_path)
    ]

    if bass_drop_path.exists():
        inputs.extend(["-i", str(bass_drop_path)])
        audio_filter = (
            f"[1:a]volume=1.35[voice];"
            f"[2:a]volume=0.10[bgm];"
            f"[3:a]volume=0.45[bass];"
            f"[voice][bgm][bass]amix=inputs=3:duration=first:dropout_transition=2[aout]"
        )
    else:
        audio_filter = (
            f"[1:a]volume=1.35[voice];"
            f"[2:a]volume=0.10[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

    filter_complex = f"[0:v]{video_filter}[vout];{audio_filter}"

    cmd = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", config.VIDEO_ENCODER,
        "-b:v", "5M",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_video_path)
    ]

    result = subprocess.run(
        cmd,
        cwd=str(config.BASE_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # Fallback to software encoding if hardware encoder complains
        cmd_fallback = [
            ffmpeg_exe, "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video_path)
        ]
        result_fallback = subprocess.run(cmd_fallback, cwd=str(config.BASE_DIR), capture_output=True, text=True)
        if result_fallback.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed:\n{result_fallback.stderr[-800:]}")

    return str(output_video_path)

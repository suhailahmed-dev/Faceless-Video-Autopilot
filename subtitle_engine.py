from pathlib import Path
import config

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS time format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def create_ass_subtitles(subtitle_chunks: list, output_ass_path: Path) -> str:
    """
    Creates dynamic ASS subtitles that stay comfortably readable on screen,
    with an elegant entry pop animation and high-contrast yellow focus highlight.
    """
    header = """[Script Info]
Title: TikTok/Reels Readable Dynamic Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralStyle,Arial,76,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,1,0,1,8,4,2,60,60,840,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for idx, item in enumerate(subtitle_chunks):
        start_str = format_ass_time(item["start"])
        end_str = format_ass_time(item["end"])
        text = item["text"].strip()
        
        words = text.split()
        if not words:
            continue
            
        # Subtle gentle pop-in on entry so it catches the eye without flickering
        anim_tag = "\\t(0,100,\\fscx110\\fscy110)\\t(100,200,\\fscx100\\fscy100)"
        
        if len(words) >= 2:
            # Highlight first 1-2 key words in electric yellow, rest in crisp white
            highlight_len = min(2, len(words) // 2 or 1)
            first_part = " ".join(words[:highlight_len])
            second_part = " ".join(words[highlight_len:])
            line_text = f"{{{anim_tag}}}{{\\c&H0000FFFF&}}{first_part} {{\\c&H00FFFFFF&}}{second_part}"
        else:
            line_text = f"{{{anim_tag}}}{{\\c&H0000FFFF&}}{text}"
            
        line = f"Dialogue: 0,{start_str},{end_str},ViralStyle,,0,0,0,,{line_text}"
        events.append(line)

    content = header + "\n".join(events) + "\n"
    
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(output_ass_path)

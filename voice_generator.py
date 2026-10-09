import asyncio
import re
from pathlib import Path
import edge_tts
import config

def break_into_word_chunks(text: str, start_time: float, end_time: float, max_words: int = 3):
    """
    Splits a sentence into small punchy chunks of max_words (e.g. 2-3 words)
    and distributes time proportionally by word character length.
    """
    words = text.strip().split()
    if not words:
        return []

    chunks = []
    for i in range(0, len(words), max_words):
        chunk_words = words[i:i + max_words]
        chunks.append(" ".join(chunk_words).upper())

    total_chars = sum(len(c) for c in chunks)
    duration = end_time - start_time
    
    timed_chunks = []
    current_time = start_time
    for chunk in chunks:
        # Allocate time relative to length of chunk
        chunk_duration = (len(chunk) / total_chars) * duration
        chunk_end = current_time + chunk_duration
        timed_chunks.append({
            "text": chunk,
            "start": current_time,
            "end": chunk_end
        })
        current_time = chunk_end

    return timed_chunks

VOICE_MAP = {
    "english": "en-US-ChristopherNeural",
    "urdu": "ur-PK-AsadNeural",
    "urdu_male": "ur-PK-AsadNeural",
    "urdu_female": "ur-PK-UzmaNeural",
    "hindi": "hi-IN-MadhurNeural"
}

async def _synthesize_async(text: str, output_audio_path: Path, voice: str = "english"):
    selected_voice = VOICE_MAP.get(voice, voice) if voice in VOICE_MAP else (voice or config.VOICE_NAME)
    communicate = edge_tts.Communicate(
        text=text,
        voice=selected_voice,
        rate=config.VOICE_RATE,
        pitch=config.VOICE_PITCH
    )
    
    sentences = []
    with open(output_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start_sec = chunk["offset"] / 10_000_000
                duration_sec = chunk["duration"] / 10_000_000
                sentences.append({
                    "start": start_sec,
                    "end": start_sec + duration_sec,
                    "text": chunk["text"]
                })

    # Now create dynamic subtitle chunks
    all_subtitle_chunks = []
    for s in sentences:
        sub_chunks = break_into_word_chunks(
            s["text"], 
            s["start"], 
            s["end"], 
            max_words=config.WORDS_PER_SCREEN
        )
        all_subtitle_chunks.extend(sub_chunks)

    # Smooth bridge: hold subtitle on screen during brief breath pauses so it doesn't vanish
    for i in range(len(all_subtitle_chunks) - 1):
        gap = all_subtitle_chunks[i+1]["start"] - all_subtitle_chunks[i]["end"]
        if 0 < gap <= 1.0:
            all_subtitle_chunks[i]["end"] = all_subtitle_chunks[i+1]["start"]

    # Determine total duration
    total_duration = sentences[-1]["end"] if sentences else 0.0

    return {
        "audio_path": str(output_audio_path),
        "duration": total_duration,
        "subtitles": all_subtitle_chunks,
        "sentences": sentences
    }

def generate_voiceover(text: str, output_filename: str = "voiceover.mp3", voice: str = "english") -> dict:
    output_path = config.TEMP_DIR / output_filename
    return asyncio.run(_synthesize_async(text, output_path, voice=voice))

if __name__ == "__main__":
    test_text = "If someone looks at your lips during a conversation, they are either attracted to you, or they are judging your words."
    res = generate_voiceover(test_text, "test_voice.mp3")
    print("Audio saved to:", res["audio_path"])
    print("Duration:", res["duration"], "seconds")
    print("Subtitles generated:", len(res["subtitles"]))
    for sub in res["subtitles"][:5]:
        print(f"[{sub['start']:.2f}s -> {sub['end']:.2f}s] {sub['text']}")

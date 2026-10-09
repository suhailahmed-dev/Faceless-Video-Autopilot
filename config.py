import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
MUSIC_DIR = ASSETS_DIR / "music"
OUTPUT_DIR = BASE_DIR / "output_videos"
TEMP_DIR = BASE_DIR / "temp"

for directory in [ASSETS_DIR, BACKGROUNDS_DIR, MUSIC_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini Models
PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODELS = ["gemini-3-flash-preview", "gemini-flash-latest"]

# Video Settings (9:16 Vertical Video for Shorts/Reels/TikTok)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_ENCODER = "h264_mf"  # Fast Windows Media Foundation Hardware Acceleration

# Voiceover Settings (Microsoft Edge Neural Voices - Free)
# en-US-ChristopherNeural: Deep, cinematic, dramatic masculine voice (Perfect for Dark Psychology)
VOICE_NAME = "en-US-ChristopherNeural"
VOICE_RATE = "-8%"   # Slower, calm, natural human storyteller pacing
VOICE_PITCH = "-3Hz"  # Rich, deep, cinematic baritone

# Subtitle styling configuration
SUBTITLE_FONT = "Arial"
SUBTITLE_FONT_SIZE = 74
WORDS_PER_SCREEN = 4  # 4 words per screen gives ~1.8-2.2 seconds visibility so viewer can comfortably read

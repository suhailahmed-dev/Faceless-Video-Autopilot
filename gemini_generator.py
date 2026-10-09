import json
import re
from google import genai
from google.genai import types
import config

# ==============================================================================
# 1. YOUTUBE SPECIALIZED PROMPT (SHORTS & 3-5 MIN STORIES)
# ==============================================================================
YOUTUBE_PROMPT_TEMPLATE = """
You are an elite YouTube director specializing in viral psychology, human communication, and high-retention storytelling.

TOPIC: {topic_info}
MODE: {mode} (either 'short' for 35-45s Short, or 'long' for 3-5 min deep storytelling)

GUIDELINES FOR 'short':
- Length: 95 to 125 words (35 to 45 seconds of speech).
- Language: English (Clear, authoritative, universally monetizable).
- Rule 1: First sentence MUST be a shock curiosity hook. Never use intro filler.
- Rule 2: Infinite Loop: The final sentence MUST loop seamlessly into the very first sentence.
- Rule 3: Educational & Eye-Opening: The viewer must learn something they can apply immediately.

GUIDELINES FOR 'long' (3-5 minutes):
- Length: 450 to 600 words.
- Structure:
  1. The Hook (0:00 - 0:25): Shocking psychological truth or paradox.
  2. The Deep Story (0:25 - 2:00): Real-world scenario or historical stoic example.
  3. The 3 Rules (2:00 - 3:45): Three actionable laws of human behavior.
  4. The Climax & Loop (3:45 - 4:30): Powerful takeaway + subscribe call to action.

RESPOND IN VALID JSON ONLY:
{{
  "title": "Click-worthy YouTube Title with #Shorts #Psychology",
  "hook": "Shock opening sentence",
  "script": "Complete spoken text for voice synthesis",
  "description": "2-3 sentence SEO rich description with educational value",
  "tags": ["psychology facts", "shorts", "human behavior", "mindset", "stoicism", "life hacks"],
  "pinned_comment": "Provocative question to pin in comments to trigger viewer replies",
  "mode": "{mode}"
}}
"""

# ==============================================================================
# 2. TIKTOK SPECIALIZED PROMPT (ROMAN URDU / FAST FYP HOOKS)
# ==============================================================================
TIKTOK_PROMPT_TEMPLATE = """
You are a top-tier viral TikTok creator in Pakistan/South Asia who understands the FYP algorithm.

TOPIC: {topic_info}

GUIDELINES:
- Length: 65 to 90 words (25 to 35 seconds fast-paced speech).
- Language: Roman Urdu / Hinglish (e.g. 'Jab koi apko disrespect kare toh ye ek kaam karo...').
- Pacing: ULTRA FAST. Shock hook in the first 0.8 seconds.
- Structure: Hook -> Shock Twist -> 2 Rapid Life Hacks -> Curiosity ending loop.
- No filler, no formal Urdu, use authentic street-smart, confident cadence.

RESPOND IN VALID JSON ONLY:
{{
  "title": "Short Catchy Roman Urdu Title",
  "hook": "Opening 1-line shock hook in Roman Urdu",
  "script": "Complete spoken Roman Urdu text for voice synthesis",
  "caption": "Short curiosity-driven Roman Urdu caption with emojis",
  "hashtags": "#tiktokpakistan #fyp #psychologyfacts #urduquotes #viralvideo #mindsetshift #foryou",
  "sound_cue": "bass_drop"
}}
"""

# ==============================================================================
# 3. INSTAGRAM REELS PROMPT (URDU EMOTIONAL OR ENGLISH PSYCHOLOGY)
# ==============================================================================
INSTAGRAM_PROMPT_TEMPLATE = """
You are a viral Instagram Reels strategist targeting high saves, shares, and follower growth.

TOPIC: {topic_info}
STYLE: {style} (either 'urdu_emotional' for relatable emotional storytelling, or 'english_psychology' for dark psychology hacks)

GUIDELINES:
- Length: 85 to 110 words (35-40 seconds).
- If 'urdu_emotional':
  - Language: Deep, moving Roman Urdu focusing on real human pain, fake friends, self-worth, and silent strength.
  - Tone: Respected, mature, inspiring Pakistani storyteller.
- If 'english_psychology':
  - Language: English dark psychology and high-value communication laws.
- Engagement Trigger: Must include an irresistible Save & Share trigger in caption.

RESPOND IN VALID JSON ONLY:
{{
  "title": "Reel Title",
  "hook": "Opening curiosity hook",
  "script": "Complete spoken text for voice synthesis",
  "caption": "Aesthetic line-broken caption with relatable question ('Comment YES agar aapke sath hua')",
  "hashtags": "#PsychologyFacts #ReelsPakistan #UrduQuotes #MindsetShift #LifeLessons #TrendingReels",
  "style": "{style}"
}}
"""

# ==============================================================================
# 4. FACEBOOK REELS & STORIES PROMPT (DESI HUMOR OR MORAL LESSONS)
# ==============================================================================
FACEBOOK_PROMPT_TEMPLATE = """
You are an expert Facebook page creator who crafts viral reels and stories that Pakistani families and youth share.

TOPIC: {topic_info}
STYLE: {style} (either 'funny_desi' for relatable everyday humor, or 'moral_story' for deep wisdom & respect)

GUIDELINES:
- Length: 90 to 120 words (35-45 seconds).
- Language: Engaging Roman Urdu.
- If 'funny_desi':
  - Relatable Pakistani observations (dost, rishtaydar, office ke drame, shaadi season).
  - Witty, clean, relatable humor that people tag their friends in.
- If 'moral_story':
  - Deep moral values: Respect for parents, true character during adversity, real vs fake relations.
  - High shareability for family WhatsApp and Facebook groups.

RESPOND IN VALID JSON ONLY:
{{
  "title": "Facebook Story Title",
  "hook": "First sentence hook",
  "script": "Complete spoken Roman Urdu text for voice synthesis",
  "caption": "Thought-provoking storytelling caption designed for high shares",
  "style": "{style}"
}}
"""

# ==============================================================================
# MASTER GENERATOR FUNCTIONS
# ==============================================================================

def _call_gemini_json(prompt: str) -> dict:
    """Helper to query Gemini models with JSON output parsing and fallback."""
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    models_to_try = [config.PRIMARY_MODEL] + config.FALLBACK_MODELS
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85
                )
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            data = json.loads(raw_text.strip())
            if "script" in data:
                data["script"] = re.sub(r'\[.*?\]', '', data["script"]).replace("*", "").strip()
            return data
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Gemini generation failed across all models: {last_error}")

def generate_youtube_script(topic_info: str, mode: str = "short") -> dict:
    prompt = YOUTUBE_PROMPT_TEMPLATE.replace("{topic_info}", topic_info).replace("{mode}", mode)
    return _call_gemini_json(prompt)

def generate_tiktok_script(topic_info: str) -> dict:
    prompt = TIKTOK_PROMPT_TEMPLATE.replace("{topic_info}", topic_info)
    return _call_gemini_json(prompt)

def generate_instagram_script(topic_info: str, style: str = "urdu_emotional") -> dict:
    prompt = INSTAGRAM_PROMPT_TEMPLATE.replace("{topic_info}", topic_info).replace("{style}", style)
    return _call_gemini_json(prompt)

def generate_facebook_script(topic_info: str, style: str = "moral_story") -> dict:
    prompt = FACEBOOK_PROMPT_TEMPLATE.replace("{topic_info}", topic_info).replace("{style}", style)
    return _call_gemini_json(prompt)

def generate_trending_topic_script(trending_topic: str) -> dict:
    """
    Generates tailored 4-platform scripts centered on today's breaking trend,
    revealing the psychological angle or human curiosity behind it.
    """
    context_topic = f"The Psychology and Phenomenon Behind '{trending_topic}'"
    yt = generate_youtube_script(context_topic, mode="short")
    tt = generate_tiktok_script(f"{trending_topic} aur iske peechay ki psychological haqeeqat")
    ig = generate_instagram_script(context_topic, style="urdu_emotional")
    fb = generate_facebook_script(f"{trending_topic} aur hamara samaj", style="moral_story")

    return {
        "title": f"Trending Breakdown: {trending_topic[:35]}",
        "raw_trend": trending_topic,
        "script": yt.get("script", ""),
        "platforms": {
            "youtube": yt,
            "tiktok": tt,
            "instagram": ig,
            "facebook": fb
        }
    }

def generate_viral_script(topic_info: str = "Dark Psychology & Human Behavior Secrets", target_platform: str = "all") -> dict:
    """
    Unified master generator: creates an integrated multi-platform distribution pack.
    """
    yt = generate_youtube_script(topic_info, mode="short")
    tt = generate_tiktok_script(topic_info)
    ig = generate_instagram_script(topic_info, style="urdu_emotional")
    fb = generate_facebook_script(topic_info, style="moral_story")

    return {
        "title": yt.get("title", f"Rule: {topic_info[:35]}"),
        "hook": yt.get("hook", ""),
        "script": yt.get("script", ""),
        "platforms": {
            "youtube": yt,
            "tiktok": tt,
            "instagram": ig,
            "facebook": fb
        }
    }

if __name__ == "__main__":
    print("Testing Unified Specialized Multi-Platform Script Generation...")
    res = generate_viral_script("The Art of Staying Calm When Disrespected")
    print("\n✓ YouTube Title:", res["platforms"]["youtube"]["title"])
    print("✓ TikTok Hook (Roman Urdu):", res["platforms"]["tiktok"]["hook"])
    print("✓ Instagram Caption:", res["platforms"]["instagram"]["caption"][:80])
    print("✓ Facebook Moral:", res["platforms"]["facebook"]["title"])

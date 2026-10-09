import requests
import xml.etree.ElementTree as ET
import random
from pathlib import Path
from datetime import datetime

# ==============================================================================
# CATEGORIZED VIRAL TOPIC REPOSITORIES (Multi-Platform Optimized)
# ==============================================================================

PLATFORM_VIRAL_TOPICS = {
    "youtube": [
        {"topic": "The Predatory Stare Test: What prolonged smiling eye contact actually means", "category": "Eye Contact & Reading People", "hook": "If someone holds eye contact with you while smiling slightly, do not smile back."},
        {"topic": "Foot Angle Psychology: How feet betray subconscious desire to escape a conversation", "category": "Subconscious Body Language", "hook": "Want to know if someone secretly wants you to leave? Look at their shoes, not their eyes."},
        {"topic": "The Power of Tactical Silence: Why saying nothing in an argument makes them crumble", "category": "Social Dominance", "hook": "The most dangerous response in an argument is not anger. It is complete, unwavering silence."},
        {"topic": "3 Signs Someone Is Secretly Envious of Your Success and Pretending to Be Happy", "category": "Deception Detection", "hook": "Pay close attention to who doesn't clap when you win."},
        {"topic": "The 48 Laws of Power: Law 4 - Always Say Less Than Necessary", "category": "Strategic Power", "hook": "The more you speak, the more common you appear, and the less in control you are."},
        {"topic": "How High-Value People Speak: The 3 vocal rules that command immediate respect", "category": "Vocal Dominance", "hook": "Notice how powerful leaders never speak quickly or finish with an upward tone?"}
    ],
    "tiktok": [
        {"topic": "Jab koi apko disrespect kare toh ye ek psychological move chalao", "category": "Respect Hacks", "hook": "Agle 10 seconds mein seekho kisi ke disrespect ko unhi par kaise ultana hai."},
        {"topic": "Fake dost pehchanne ka 5 second rule jo 99% log miss kar dete hain", "category": "Friendship Truth", "hook": "Agar tumhara dost ye aik cheez karta hai toh wo tumhara dost nahi hai."},
        {"topic": "Larkiyon ki body language ke 3 signs jo woh kabhi zubaan se nahi batati", "category": "Psychological Signals", "hook": "Yeh 3 signs notice karo aur samjho unke dimaag mein kya chal raha hai."},
        {"topic": "Overthinking ko 1 minute mein khatam karne ka military brain hack", "category": "Mind Control", "hook": "Dimagh mein baatein chalna band nahi ho rahi? Yeh trick abhi try karo."},
        {"topic": "Kabhi bhi kisi ko ye 3 baatein mat batana agar izzat bachani hai", "category": "Social Secrets", "hook": "Jitna kam bologe, utni tumhari value aasman par jayegi."}
    ],
    "instagram": [
        {"topic": "Sabke hote huway bhi andar se akela mehsoos karna...", "category": "Emotional Resonance", "hook": "Kabhi notice kiya hai ke sabse zyada hansne wala shakhs sabse zyada khamosh kyun hota hai?"},
        {"topic": "Jab apka sabse qareebi shakhs achanak ajnabee ban jaye", "category": "Human Bonds", "hook": "Log badalte nahi hain, bas unke chehre se zaroorat ka naqaab utar jata hai."},
        {"topic": "Dark Psychology: How subtle micro-rejections hurt more than direct insults", "category": "Psychology & Self-Worth", "hook": "The quietest disrespect is the most toxic."},
        {"topic": "Khamooshi sabse bari taqat kab banti hai?", "category": "Inner Strength", "hook": "Jab aap har baat par safai dena band kar dete hain, tab aap jeet jaate hain."},
        {"topic": "The Art of Detachment: Why stopping care brings everything back to you", "category": "Emotional Freedom", "hook": "The moment you stop chasing validation, people start competing for your attention."}
    ],
    "facebook": [
        {"topic": "Desi Rishtaydaron ke taane aur unka classy psychological jawab", "category": "Pakistani Relatable Humor", "hook": "Shadi par har rishtaydar ka aik sawal: 'Beta aage ka kya socha hai?' Suno iska best jawab."},
        {"topic": "Maa baap ki qadr waqt nikalne ke baad kyun hoti hai? Aik sachi dastaan", "category": "Moral Lessons & Family", "hook": "Duniya mein sab badal sakte hain, magar maa baap jaisa khuloos dobara nahi milta."},
        {"topic": "Purane sachi dosti aur aaj kal ke social media relations ka farq", "category": "Social Reality", "hook": "Pehle dost mushkil mein saath kharay hotay thay, aaj kal bas WhatsApp status dekh kar guzar jaate hain."},
        {"topic": "Zindagi ka sabse bara sabaq: Har kisi ko apna dard mat sunao", "category": "Life Wisdom", "hook": "Dard sunne walon ke paas namak hamesha tayyar hota hai."}
    ]
}

def fetch_google_trends(geo: str = "US") -> list:
    """Fetches real-time search trends from Google Trends RSS."""
    trends = []
    try:
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title = item.find("title")
                if title is not None and title.text:
                    clean_t = title.text.strip()
                    if clean_t and clean_t not in trends:
                        trends.append(clean_t)
    except Exception:
        pass
    return trends[:15]

def get_live_radar_summary() -> dict:
    """Returns combined trends from multiple regions."""
    us_trends = fetch_google_trends("US")
    pk_trends = fetch_google_trends("PK")
    
    combined = list(dict.fromkeys(pk_trends + us_trends))
    if not combined:
        combined = ["AI Technology Breakthrough", "Psychology of Motivation", "Viral Life Hacks", "Communication Mastery"]
    return {
        "trends": combined[:10],
        "last_updated": datetime.now().strftime("%I:%M %p PKT")
    }

def get_daily_trending_topic(history: list = None) -> dict:
    """
    Extracts today's breaking trend and synthesizes a high-curiosity psychological hook
    for the dedicated Daily Trending Video.
    """
    radar = get_live_radar_summary()
    top_trend = radar["trends"][0] if radar["trends"] else "High-Status Psychological Signals"
    
    # Formulate a viral hook around the trending entity or concept
    trend_angles = [
        f"The Psychological Truth Behind {top_trend}: Why Everyone Is Talking About It",
        f"What the {top_trend} Phenomenon Reveals About Human Behavior",
        f"The Dark Psychology of {top_trend}: The Subconscious Trigger Explained",
        f"The Hidden Power Dynamic Behind {top_trend} You Never Noticed"
    ]
    chosen_topic = random.choice(trend_angles)
    
    return {
        "chosen_topic": chosen_topic,
        "raw_trend": top_trend,
        "category": "Breaking Daily Trend",
        "trending_context": radar["trends"][:5]
    }

def get_platform_topic(platform: str = "youtube", history: list = None) -> dict:
    """Retrieves an optimal platform-specific topic from curated viral archives."""
    pool = PLATFORM_VIRAL_TOPICS.get(platform.lower(), PLATFORM_VIRAL_TOPICS["youtube"])
    used = [h.get("topic", "").lower() for h in (history or [])]
    
    candidates = [p for p in pool if p["topic"].lower() not in used]
    if not candidates:
        candidates = pool
        
    chosen = random.choice(candidates)
    return {
        "chosen_topic": chosen["topic"],
        "category": chosen["category"],
        "hook": chosen.get("hook", ""),
        "platform": platform
    }

def get_todays_winning_topic(history: list = None) -> dict:
    """Backward-compatible fallback."""
    return get_platform_topic("youtube", history)

if __name__ == "__main__":
    print("Testing Trend Radar Engine...")
    trends = get_live_radar_summary()
    print("Live Radar:", trends)
    print("\nDaily Trending Topic:", get_daily_trending_topic())
    print("\nTikTok Curated:", get_platform_topic("tiktok"))
    print("\nInstagram Curated:", get_platform_topic("instagram"))
    print("\nFacebook Curated:", get_platform_topic("facebook"))

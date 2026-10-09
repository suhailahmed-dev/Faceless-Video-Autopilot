import json
from pathlib import Path
from datetime import datetime
import config

MEMORY_FILE = config.BASE_DIR / "memory.json"

def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "generated_videos": [],
        "winning_categories": ["Body Language", "Eye Contact", "Deception", "War & Survival Story"],
        "top_performing_topics": []
    }

def save_memory(data: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_generated_video(title: str, topic: str, category: str, folder_path: str, duration: float):
    mem = load_memory()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": title,
        "topic": topic,
        "category": category,
        "folder_path": str(folder_path),
        "duration": duration,
        "status": "pending_review"
    }
    mem["generated_videos"].append(entry)
    save_memory(mem)
    return entry

def get_recent_history(limit: int = 10) -> list:
    mem = load_memory()
    return mem.get("generated_videos", [])[-limit:]

def mark_video_winner(title_substring: str):
    mem = load_memory()
    for v in mem["generated_videos"]:
        if title_substring.lower() in v["title"].lower():
            v["status"] = "winner"
            if v["category"] not in mem["winning_categories"]:
                mem["winning_categories"].append(v["category"])
            mem["top_performing_topics"].append(v["topic"])
    save_memory(mem)
    print(f"Video matching '{title_substring}' marked as WINNER in memory!")

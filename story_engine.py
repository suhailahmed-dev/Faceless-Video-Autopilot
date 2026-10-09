import os
import sys
import json
from pathlib import Path
from google import genai
from google.genai import types
import config

# Fix Windows console encoding for UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = config.BASE_DIR
STORY_FACTORY_DIR = BASE_DIR / "story_factory"

# ==============================================================================
# LOCKED CHARACTER & WORLD BIBLE (IMMUTABLE FOR STORY A & B)
# ==============================================================================
CHARACTER_BIBLE = {
    "suhail": {
        "name": "Suhail",
        "role": "Main Hero (Boy)",
        "age": 14,
        "appearance": "14-year-old boy with messy dark brown hair, bright determined blue eyes, wearing a vintage brown pilot leather jacket over a grey t-shirt and blue jeans",
        "personality": "Adventurous, fearless, curious, protective of his sister Sophia",
        "item": "An antique modified copper shortwave radio with glowing amber vacuum tubes"
    },
    "sophia": {
        "name": "Sophia",
        "role": "Main Heroine (Girl)",
        "age": 13,
        "appearance": "13-year-old girl with dark hair tied in two neat braids, observant hazel eyes, wearing an emerald green oversized hoodie and black cargo pants",
        "personality": "Clever, tech-savvy, cautious, quick-thinking under pressure",
        "item": "A glowing silver compass necklace whose needle spins backwards near paranormal rift zones"
    },
    "supporting": {
        "hamza": {
            "name": "Hamza",
            "role": "Loyal Friend",
            "age": 14,
            "appearance": "14-year-old boy with curly black hair, glasses, wearing a bright yellow windbreaker, carrying a backpack full of tools",
            "personality": "Nervous but brave when friends are in trouble"
        }
    },
    "art_style": (
        "3D stylized Pixar and DreamWorks animation style, cinematic Octane render, "
        "Unreal Engine 5, volumetric fog, dramatic rim lighting, vibrant rich colors with dark atmospheric shadows, "
        "kid-friendly spooky sci-fi mystery aesthetic, photorealistic textures, 8k vertical portrait"
    ),
    "rules": {
        "episodes_per_story": 7,
        "scenes_per_episode": 15,
        "seconds_per_scene": 10,
        "total_seconds_episode": 150,  # 2.5 minutes
        "narration_language": "Simple English with clear kid-friendly pacing",
        "subtitles_language": "Roman Urdu translation burned in"
    }
}

# 7-Episode Master Arc for Story A: "The Haunted Frequency"
STORY_A_ARC = {
    "title": "The Haunted Frequency",
    "folder_name": "Story_A_The_Haunted_Frequency",
    "episodes": [
        {"ep": 1, "title": "The Static in the Woods", "summary": "Suhail and Sophia discover an ancient radio buried in the misty pine forest picking up a strange voice counting down."},
        {"ep": 2, "title": "Voices From the Radio", "summary": "The radio speaks Suhail and Sophia's names and warns them of the shadow clock tower before static screams."},
        {"ep": 3, "title": "The Clock Tower Anomaly", "summary": "They sneak into the forbidden rusted clock tower where clocks tick backwards and gravity starts floating small objects."},
        {"ep": 4, "title": "The Mirror of Shadows", "summary": "Sophia's silver compass glows blinding violet, unlocking an obsidian mirror that reveals another dark dimension."},
        {"ep": 5, "title": "Trapped in the Grey Zone", "summary": "The rift pulls Suhail inside; Sophia must use the radio frequency to navigate the silent frozen world."},
        {"ep": 6, "title": "The Secret of the Watcher", "summary": "They discover who sent the signal: a lost explorer trapped inside the radio frequency 40 years ago."},
        {"ep": 7, "title": "The Final Frequency (Finale)", "summary": "In an epic race against time, Suhail and Sophia broadcast the exit frequency and escape just as the portal collapses."}
    ]
}

def get_bible_prompt_block() -> str:
    """Returns the locked bible text to be injected verbatim into prompts."""
    return f"""
LOCKED CHARACTER & WORLD BIBLE:
- Main Boy Character: {CHARACTER_BIBLE['suhail']['name']} ({CHARACTER_BIBLE['suhail']['appearance']}). Item: {CHARACTER_BIBLE['suhail']['item']}.
- Main Girl Character: {CHARACTER_BIBLE['sophia']['name']} ({CHARACTER_BIBLE['sophia']['appearance']}). Item: {CHARACTER_BIBLE['sophia']['item']}.
- Art Style: {CHARACTER_BIBLE['art_style']}.
- Tone: Spooky sci-fi mystery for kids and teenagers. Safe, eerie, exciting, zero gore or graphic violence.
- Spoken Audio: Clear simple English narration.
- Subtitle: Roman Urdu translation for every scene.
"""

def generate_curated_episode_1() -> dict:
    """
    Returns the master 15-scene production script for Story A, Episode 1:
    'The Static in the Woods' (15 scenes x 10s = 150s = 2.5 min).
    """
    scenes = [
        # BATCH 1: Scenes 1 to 4 (0:00 - 0:40)
        {
            "scene": 1,
            "batch": 1,
            "duration": 10,
            "spoken_english": "Deep in the misty Whispering Woods, fourteen-year-old Suhail heard a sound that should not exist.",
            "roman_urdu": "Khamoosh jungle ke beech, choudah saala Suhail ko aik aisi aawaz sunayi di jo nahi honi chahiye thi.",
            "visual_prompt": f"3D animation, Suhail (14yo boy with messy dark hair, blue eyes, brown leather jacket) walking cautiously through misty pine forest with glowing fireflies, {CHARACTER_BIBLE['art_style']}",
            "mood": "Mysterious"
        },
        {
            "scene": 2,
            "batch": 1,
            "duration": 10,
            "spoken_english": "His thirteen-year-old sister Sophia pointed her flashlight at the damp ground beneath an ancient twisted oak tree.",
            "roman_urdu": "Uski behan Sophia ne puranay darakht ke neeche torch ki roshni daali.",
            "visual_prompt": f"3D animation, Sophia (13yo girl with dark braids, hazel eyes, green hoodie) shining a bright flashlight onto muddy ground, {CHARACTER_BIBLE['art_style']}",
            "mood": "Curiosity"
        },
        {
            "scene": 3,
            "batch": 1,
            "duration": 10,
            "spoken_english": "Half-buried in the wet soil was an antique copper radio, glowing with faint amber vacuum tubes.",
            "roman_urdu": "Mitti mein aadhi dabi hui purani taanbay ki radio thi, jo halki amber roshni se chamak rahi thi.",
            "visual_prompt": f"3D animation, close-up of antique copper shortwave radio with glowing vacuum tubes in misty dark soil, eerie purple particles, {CHARACTER_BIBLE['art_style']}",
            "mood": "Discovery"
        },
        {
            "scene": 4,
            "batch": 1,
            "duration": 10,
            "spoken_english": "Suhail reached down and brushed the cold dirt away. Suddenly, the dial spun by itself.",
            "roman_urdu": "Suhail ne mitti saaf ki, to achanak radio ka knob khud ba khud ghoomne laga.",
            "visual_prompt": f"3D animation, Suhail in leather jacket kneeling down touching glowing copper radio, sudden electric spark, {CHARACTER_BIBLE['art_style']}",
            "mood": "Shock"
        },

        # BATCH 2: Scenes 5 to 8 (0:40 - 1:20)
        {
            "scene": 5,
            "batch": 2,
            "duration": 10,
            "spoken_english": "Static hissed through the speaker, followed by a low, mechanical hum that made the pine needles vibrate.",
            "roman_urdu": "Speaker se static ki aawaz aayi, aur zameen par paray darakht ke patte kaanpne lagay.",
            "visual_prompt": f"3D animation, radio speaker vibrating with soundwaves, pine needles floating slightly off the ground in misty fog, {CHARACTER_BIBLE['art_style']}",
            "mood": "Tension"
        },
        {
            "scene": 6,
            "batch": 2,
            "duration": 10,
            "spoken_english": "Sophia checked her silver compass necklace. The needle was spinning furiously counterclockwise.",
            "roman_urdu": "Sophia ne apna silver compass dekha, uski sui tezi se ulti simt ghoom rahi thi.",
            "visual_prompt": f"3D animation, close-up of Sophia holding her glowing silver compass necklace as the needle spins frantically, terrified expression, {CHARACTER_BIBLE['art_style']}",
            "mood": "Alarm"
        },
        {
            "scene": 7,
            "batch": 2,
            "duration": 10,
            "spoken_english": "'Suhail, don't touch it,' she whispered. But the radio crackled and a distorted voice cut through.",
            "roman_urdu": "'Suhail, isko haath mat lagao,' Sophia boli. Magar radio se aik ajeeb aawaz aane lagi.",
            "visual_prompt": f"3D animation, Sophia grabbing Suhail's arm in dark foggy forest, warning him with wide eyes, {CHARACTER_BIBLE['art_style']}",
            "mood": "Suspense"
        },
        {
            "scene": 8,
            "batch": 2,
            "duration": 10,
            "spoken_english": "'Frequency ninety-four point seven,' the voice whispered. 'Do not look up at the sky.'",
            "roman_urdu": "'Frequency 94.7,' aawaz ne kaha. 'Aasman ki taraf mat dekhna.'",
            "visual_prompt": f"3D animation, eerie glowing violet radio dial illuminated on 94.7 MHz, shadowy trees looming overhead, {CHARACTER_BIBLE['art_style']}",
            "mood": "Chilling"
        },

        # BATCH 3: Scenes 9 to 12 (1:20 - 2:00)
        {
            "scene": 9,
            "batch": 3,
            "duration": 10,
            "spoken_english": "Both kids instantly looked up into the canopy of dark pines.",
            "roman_urdu": "Dono bachon ne foran ooper ghane darakhton ki taraf dekha.",
            "visual_prompt": f"3D animation, low angle shot of Suhail and Sophia looking up in horror through pine treetops at the night sky, {CHARACTER_BIBLE['art_style']}",
            "mood": "Climax Build"
        },
        {
            "scene": 10,
            "batch": 3,
            "duration": 10,
            "spoken_english": "The clouds were swirling in a glowing violet vortex, completely silent and impossible.",
            "roman_urdu": "Badalon ke darmiyan aik baingani roshni ka bhanwar tezi se ghoom raha tha.",
            "visual_prompt": f"3D animation, cosmic violet rift swirl in dark night sky over misty pine forest, sci-fi anomaly, {CHARACTER_BIBLE['art_style']}",
            "mood": "Sci-Fi Wonder"
        },
        {
            "scene": 11,
            "batch": 3,
            "duration": 10,
            "spoken_english": "The trees around them began to cast two shadows instead of one.",
            "roman_urdu": "Unke gird darakhton ke aik ke bajaye do do saaye banne lage.",
            "visual_prompt": f"3D animation, ground view showing double shadows stretching unnaturally from pine trees, mysterious purple light, {CHARACTER_BIBLE['art_style']}",
            "mood": "Uncanny"
        },
        {
            "scene": 12,
            "batch": 3,
            "duration": 10,
            "spoken_english": "'We need to run back to the town right now,' Sophia urged, gripping her compass tightly.",
            "roman_urdu": "'Humein abhi wapas sheher bhagna hoga,' Sophia ne ghabra kar kaha.",
            "visual_prompt": f"3D animation, Sophia in green hoodie pulling Suhail to run, glowing rift light reflecting on their faces, {CHARACTER_BIBLE['art_style']}",
            "mood": "Urgency"
        },

        # BATCH 4: Scenes 13 to 15 (2:00 - 2:30)
        {
            "scene": 13,
            "batch": 4,
            "duration": 10,
            "spoken_english": "Suhail grabbed the copper radio by its handle. It was burning cold like ice.",
            "roman_urdu": "Suhail ne radio uthaya, to wo baraf ki tarah thandi thi.",
            "visual_prompt": f"3D animation, Suhail picking up the glowing antique radio, frost creeping along his leather sleeve, {CHARACTER_BIBLE['art_style']}",
            "mood": "Action"
        },
        {
            "scene": 14,
            "batch": 14,
            "duration": 10,
            "spoken_english": "Suddenly, the radio speaker screamed: 'Suhail! Sophia! It has found your coordinates!'",
            "roman_urdu": "Achanak radio se cheekh aayi: 'Suhail! Sophia! Usne tumhara pata dhoondh liya hai!'",
            "visual_prompt": f"3D animation, extreme close-up of radio tubes flaring bright magenta light, illuminating Suhail and Sophia's shocked faces, {CHARACTER_BIBLE['art_style']}",
            "mood": "Peak Cliffhanger"
        },
        {
            "scene": 15,
            "batch": 4,
            "duration": 10,
            "spoken_english": "In the mist ahead, a towering shadowy silhouette stepped onto the forest path. Subscribe for Episode Two!",
            "roman_urdu": "Dhundh ke beech aik azeem saaya raste par aa khara hua... Agli qist ke liye subscribe karein!",
            "visual_prompt": f"3D animation, wide cinematic shot of Suhail and Sophia facing a colossal shadowy silhouette with glowing eyes in foggy forest path, {CHARACTER_BIBLE['art_style']}",
            "mood": "Ultimate Cliffhanger & CTA"
        }
    ]

    return {
        "story_id": "Story_A",
        "story_title": STORY_A_ARC["title"],
        "episode": 1,
        "episode_title": STORY_A_ARC["episodes"][0]["title"],
        "total_scenes": len(scenes),
        "total_duration_sec": 150,
        "batches": [
            {"batch": 1, "scenes": [1, 2, 3, 4], "duration": 40, "filename": "StoryA_Ep01_Batch1.mp4"},
            {"batch": 2, "scenes": [5, 6, 7, 8], "duration": 40, "filename": "StoryA_Ep01_Batch2.mp4"},
            {"batch": 3, "scenes": [9, 10, 11, 12], "duration": 40, "filename": "StoryA_Ep01_Batch3.mp4"},
            {"batch": 4, "scenes": [13, 14, 15], "duration": 30, "filename": "StoryA_Ep01_Batch4.mp4"}
        ],
        "scenes": scenes
    }

def save_episode_script(data: dict):
    """Saves the generated scene script to the Scripts folder."""
    story_dir = STORY_FACTORY_DIR / STORY_A_ARC["folder_name"] / "Scripts"
    story_dir.mkdir(parents=True, exist_ok=True)
    file_path = story_dir / f"Ep{data['episode']:02d}_Scenes.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📄 Saved Episode Script: {file_path}")
    return file_path

if __name__ == "__main__":
    print("Testing Story Engine & Character Bible...")
    ep1 = generate_curated_episode_1()
    p = save_episode_script(ep1)
    print(f"✓ Total scenes: {ep1['total_scenes']} ({ep1['total_duration_sec']} seconds)")
    print(f"✓ 4 Batches configured: {[b['filename'] for b in ep1['batches']]}")

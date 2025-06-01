import json
import os

FLASHCARDS_FILE = "flashcards.json"
PROGRESS_FILE = "user_progress.json"
MISTAKES_FILE = "mistakes.json"

def load_flashcards():
    """
    Reads flashcards.json, which is assumed to be an array of objects:
      {
        "question": "...",
        "instruction": "There are 3 correct answers to this question.",
        "options": { "A": "text", "B": "text", ... },
        "answers": ["A", "D", "E"]
      }
    This function attaches an "id" (1-based index) to each entry.
    Returns: [ { "id": 1, "question": ..., "instruction": ..., "options": {...}, "answers": [...] }, ... ]
    """
    with open(FLASHCARDS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    processed = []
    for idx, entry in enumerate(raw, start=1):
        # Sanity check
        if not all(k in entry for k in ("question", "instruction", "options", "answers")):
            raise ValueError(
                f"Entry #{idx} missing one of 'question','instruction','options','answers'.\n→ {entry!r}"
            )
        processed.append({
            "id": idx,
            "question": entry["question"],
            "instruction": entry["instruction"],
            "options": entry["options"],   # {"A": "...", "B": "...", ...}
            "answers": entry["answers"]    # e.g. ["A","D","E"]
        })
    return processed

def load_progress():
    """
    Reads user_progress.json, which stores:
      { "day": 1, "answered": { "5": "correct", "12": "wrong", ... } }
    If file does not exist, returns {"day": 1, "answered": {}}
    """
    if not os.path.exists(PROGRESS_FILE):
        return {"day": 1, "answered": {}}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_progress(progress_dict):
    """
    Writes progress_dict to user_progress.json.
    """
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress_dict, f, indent=2)

def load_mistakes():
    """
    Reads mistakes.json, which stores:
      { "qid_str": count, ... }
    If file does not exist, returns {}.
    """
    if not os.path.exists(MISTAKES_FILE):
        return {}
    with open(MISTAKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_mistakes(mistakes_dict):
    """
    Writes mistakes_dict to mistakes.json.
    """
    with open(MISTAKES_FILE, "w", encoding="utf-8") as f:
        json.dump(mistakes_dict, f, indent=2)

import json
import os

FLASHCARDS_FILE = "flashcards.json"
PROGRESS_FILE = "user_progress.json"

def load_flashcards():
    """
    - Reads flashcards.json (a list of objects without 'id').
    - Adds an 'id' key to each entry (1-based index).
    - Keeps 'question', 'instruction', 'options' (dict), and 'answers' (list of letters).
    Returns a list of dicts, each dict guaranteed to have:
      { "id": int,
        "question": str,
        "instruction": str,
        "options": { "A": "text", "B": "text", … },
        "answers": [ "A", "D", … ] }
    """
    with open(FLASHCARDS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    processed = []
    for idx, entry in enumerate(raw, start=1):
        # Sanity‐check that the required keys exist
        if not all(k in entry for k in ("question", "instruction", "options", "answers")):
            raise ValueError(f"Entry #{idx} is missing one of 'question', 'instruction', 'options', 'answers'.\n→ {entry!r}")

        processed.append({
            "id": idx,
            "question": entry["question"],
            "instruction": entry["instruction"],
            "options": entry["options"],   # keep as { "A": text, "B": text, … }
            "answers": entry["answers"]    # list of letters, e.g. ["A","D","E"]
        })
    return processed

def load_progress():
    """
    Opens user_progress.json if it exists; otherwise initialize:
      { "day": 1, "answered": {} }
    'answered' maps question‐id (as string) → "correct" or "wrong".
    """
    if not os.path.exists(PROGRESS_FILE):
        return {"day": 1, "answered": {}}

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_progress(progress_dict):
    """
    Overwrites user_progress.json with progress_dict.
    """
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress_dict, f, indent=2)

import json
import os

FLASHCARDS_FILE = "flashcards.json"
PROGRESS_FILE = "user_progress.json"

def load_flashcards():
    """
    Opens flashcards.json and returns a list of dicts.
    Each dict must have keys: "id", "question", "options", "answers".
    """
    with open(FLASHCARDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_progress():
    """
    Opens user_progress.json if it exists; otherwise returns
    the initial structure: day=1, no answered questions yet.
    """
    if not os.path.exists(PROGRESS_FILE):
        # First run: no file yet → initialize progress
        return {"day": 1, "answered": {}}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_progress(progress_dict):
    """
    Writes the entire progress_dict back to user_progress.json.
    """
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress_dict, f, indent=2)

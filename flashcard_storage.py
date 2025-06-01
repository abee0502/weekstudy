# ───────────────────────────────────────────────────────────────────────────────
# flashcard_storage.py
#
# Provides: load_answered_ids(), save_answered_ids(), load_wrong_answers(), save_wrong_answers()
# ───────────────────────────────────────────────────────────────────────────────

import json
import os

# Files (in the same folder as your app)
ANSWERED_FILE = "answered_questions.json"
MISTAKES_FILE = "mistakes.json"


def load_answered_ids():
    """
    Returns a set of question‐indices (ints) that have already been answered
    in this session (for the current day). If the file doesn't exist, returns an empty set.
    """
    if not os.path.exists(ANSWERED_FILE):
        return set()
    with open(ANSWERED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # We expect data = [0, 5, 12, …], so convert to set of ints
    return set(int(x) for x in data)


def save_answered_ids(answered_set):
    """
    Writes the Python set/list of answered question‐indices to JSON.
    """
    with open(ANSWERED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(answered_set)), f, indent=2)


def load_wrong_answers():
    """
    Returns a dict { "<qid>": count, … }. If file doesn’t exist, returns {}.
    """
    if not os.path.exists(MISTAKES_FILE):
        return {}
    with open(MISTAKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_wrong_answers(wrong_dict):
    """
    Writes the dictionary of mistakes back to JSON.
    """
    with open(MISTAKES_FILE, "w", encoding="utf-8") as f:
        json.dump(wrong_dict, f, indent=2)

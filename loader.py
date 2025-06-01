import json

def load_flashcards():
    with open("flashcards.json") as f:
        return json.load(f)

def load_progress():
    try:
        with open("user_progress.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"day": 1, "answered": {}}

def save_progress(data):
    with open("user_progress.json", "w") as f:
        json.dump(data, f, indent=2)

import json
import os

def load_questions(path="questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_day_questions(questions, day, questions_per_day=40):
    start = (day - 1) * questions_per_day
    end = start + questions_per_day
    return questions[start:end]

def save_json(path, data):
    if not os.path.exists(os.path.dirname(path)):
        raise FileNotFoundError(f"Directory does not exist: {os.path.dirname(path)}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

def clear_day_mistakes(filename, day):
    """Clears mistakes for a specific day."""
    try:
        mistakes = load_json(filename, {})
        day_prefix = f"day{day}_q"
        filtered_mistakes = {k: v for k, v in mistakes.items() if not k.startswith(day_prefix)}
        save_json(filename, filtered_mistakes)
        return True
    except Exception as e:
        print(f"Error clearing mistakes for Day {day}: {e}")
        return False

def clear_bulk_mistakes(filename):
    """Clears the bulk mistakes file. Creates an empty one if not found."""
    try:
        save_json(filename, {})
        return True
    except Exception as e:
        print(f"Error clearing bulk mistakes: {e}")
        return False
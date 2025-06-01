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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

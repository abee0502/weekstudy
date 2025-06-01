from loaders import load_progress, save_progress

QUESTIONS_PER_DAY = 40
MAX_DAYS = 7

def get_today_batch(all_flashcards, day):
    """
    Given the full list of flashcards (with 'id'), returns the slice for this day.
    If there are fewer than day*40 cards total, it simply returns whatever remains.
    """
    start_idx = (day - 1) * QUESTIONS_PER_DAY
    end_idx = day * QUESTIONS_PER_DAY
    return all_flashcards[start_idx:end_idx]

def increment_day():
    """
    Bumps day by +1 (capped at MAX_DAYS). Saves back to user_progress.json.
    """
    prog = load_progress()
    current = prog.get("day", 1)
    new_day = current + 1
    if new_day > MAX_DAYS:
        new_day = MAX_DAYS
    prog["day"] = new_day
    save_progress(prog)

def reset_day():
    """
    Resets progress to day 1 with no answered questions.
    """
    save_progress({"day": 1, "answered": {}})

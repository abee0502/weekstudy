from loaders import load_progress, save_progress

QUESTIONS_PER_DAY = 40
MAX_DAYS = 7

def get_today_batch(all_flashcards, day):
    """
    Returns the list slice of all_flashcards for the given day (1-based).
    E.g. day=1 → indices 0..39, day=2 → 40..79, etc. If fewer than day*40 exist,
    returns whatever is left.
    """
    start_idx = (day - 1) * QUESTIONS_PER_DAY
    end_idx = day * QUESTIONS_PER_DAY
    return all_flashcards[start_idx:end_idx]

def increment_day():
    """
    Increases prog["day"] by 1 (capped at MAX_DAYS), then saves to user_progress.json.
    """
    prog = load_progress()
    current = prog.get("day", 1)
    new_day = min(current + 1, MAX_DAYS)
    prog["day"] = new_day
    save_progress(prog)

def reset_day():
    """
    Resets day to 1 and clears "answered".
    """
    save_progress({"day": 1, "answered": {}})

from loaders import load_progress, save_progress

QUESTIONS_PER_DAY = 40
MAX_DAYS = 7

def get_today_batch(all_flashcards, day):
    """
    Given the full list of flashcards and the current day (1–7),
    returns the slice of questions for that day.
    If total flashcards < day*40, return whatever remains.
    """
    start_index = (day - 1) * QUESTIONS_PER_DAY
    end_index = day * QUESTIONS_PER_DAY
    return all_flashcards[start_index:end_index]

def increment_day():
    """
    Loads progress.json, bumps 'day' by 1 (capped at 7), saves back.
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
    Sets day back to 1 and clears all answered records.
    """
    prog = {"day": 1, "answered": {}}
    save_progress(prog)

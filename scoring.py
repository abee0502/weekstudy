from loaders import load_progress, save_progress

QUESTIONS_PER_DAY = 40

def save_answer(qid, is_correct):
    """
    Mark question with id = qid (an integer) as "correct" or "wrong".
    Progress file stores qid as string.
    """
    prog = load_progress()
    prog.setdefault("answered", {})
    prog["answered"][str(qid)] = "correct" if is_correct else "wrong"
    save_progress(prog)

def get_progress_counts():
    """
    Returns a dict:
      { "day": int,
        "answered_today": int,
        "total_answered": int }
    """
    prog = load_progress()
    day = prog.get("day", 1)
    answered = prog.get("answered", {})

    # Determine how many of today's IDs have been answered
    today_start = (day - 1) * QUESTIONS_PER_DAY + 1  # e.g. day=1 → 1..40
    today_end   = day * QUESTIONS_PER_DAY              # e.g. day=1 → 1..40

    answered_today = 0
    for qid_str in answered.keys():
        try:
            q = int(qid_str)
        except ValueError:
            continue
        if today_start <= q <= today_end:
            answered_today += 1

    total_answered = len(answered)
    return {
        "day": day,
        "answered_today": answered_today,
        "total_answered": total_answered
    }

def reset_all_answers():
    """
    Clears the 'answered' dict and resets day to 1.
    """
    save_progress({"day": 1, "answered": {}})

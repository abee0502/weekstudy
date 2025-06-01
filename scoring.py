from loaders import load_progress, save_progress

QUESTIONS_PER_DAY = 40  # must match session.py’s constant

def save_answer(qid, is_correct):
    """
    Marks question qid (integer) as "correct" or "wrong" in user_progress.json.
    """
    prog = load_progress()
    # Ensure qid is stored as string key
    prog["answered"][str(qid)] = "correct" if is_correct else "wrong"
    save_progress(prog)

def get_progress_counts():
    """
    Returns a dict with:
      - 'day': current day number
      - 'answered_today': how many in this day's batch have been answered (correct or wrong)
      - 'total_answered': total distinct questions answered so far
    """
    prog = load_progress()
    day = prog.get("day", 1)
    answered_dict = prog.get("answered", {})

    # Count how many answered IDs fall into today's range:
    today_start = (day - 1) * QUESTIONS_PER_DAY + 1  # e.g. day=1 → 1..40
    today_end = day * QUESTIONS_PER_DAY               # e.g. day=1 → 1..40

    answered_today = 0
    for qid_str in answered_dict.keys():
        try:
            qid = int(qid_str)
        except ValueError:
            continue
        if today_start <= qid <= today_end:
            answered_today += 1

    total_answered = len(answered_dict)
    return {
        "day": day,
        "answered_today": answered_today,
        "total_answered": total_answered
    }

def reset_all_answers():
    """
    Clears all answered records and resets day to 1.
    """
    from loaders import save_progress
    save_progress({"day": 1, "answered": {}})

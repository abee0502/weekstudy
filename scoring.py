from loaders import load_progress, save_progress, load_mistakes, save_mistakes

QUESTIONS_PER_DAY = 40

def record_attempt(qid, is_correct):
    """
    Called whenever a user submits an answer for question ID `qid` (integer).
    - Updates user_progress.json → prog["answered"][str(qid)] = "correct"/"wrong"
    - If is_correct == False, increments mistakes[str(qid)] by 1 in mistakes.json.
    """
    # 1) Update answered in user_progress.json
    prog = load_progress()
    prog.setdefault("answered", {})
    prog["answered"][str(qid)] = "correct" if is_correct else "wrong"
    save_progress(prog)

    # 2) If wrong, increment mistake count
    if not is_correct:
        mistakes = load_mistakes()
        mistakes[str(qid)] = mistakes.get(str(qid), 0) + 1
        save_mistakes(mistakes)

def get_progress_counts():
    """
    Returns: {
      "day": int,
      "answered_today": int,    # how many question-IDs from today’s slice are in prog["answered"]
      "total_answered": int     # total distinct qids ever answered
    }
    """
    prog = load_progress()
    day = prog.get("day", 1)
    answered = prog.get("answered", {})

    today_start = (day - 1) * QUESTIONS_PER_DAY + 1
    today_end = day * QUESTIONS_PER_DAY

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
    Clears user_progress.json entirely and resets day to 1.
    """
    save_progress({"day": 1, "answered": {}})

def get_mistakes():
    """
    Returns the mistakes dict { "qid_str": count, … }.
    """
    return load_mistakes()

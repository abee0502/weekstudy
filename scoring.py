from loaders import load_progress, save_progress

QUESTIONS_PER_DAY = 40

def save_answer(qid, result):
    """
    Mark question with id = qid (an integer) as:
      - "correct"   (if exactly all right options were chosen),
      - "partial"   (if at least one correct option was chosen but not exactly all),
      - "wrong"     (if none of the correct options was chosen).
    Stores that string under user_progress.json → "answered".
    """
    prog = load_progress()
    prog.setdefault("answered", {})
    prog["answered"][str(qid)] = result  # result in {"correct", "partial", "wrong"}
    save_progress(prog)

def get_progress_counts():
    """
    Returns a dict:
      {
        "day": int,
        "answered_today": int,
        "total_answered": int
      }
    Uses load_progress() to count how many question-IDs from today's slice
    appear in prog["answered"] (regardless of whether correct/partial/wrong).
    """
    prog = load_progress()
    day = prog.get("day", 1)
    answered = prog.get("answered", {})

    today_start = (day - 1) * QUESTIONS_PER_DAY + 1
    today_end   = day * QUESTIONS_PER_DAY

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
    Clears the entire answered dict and resets day to 1.
    Overwrites user_progress.json with { "day": 1, "answered": {} }.
    """
    save_progress({"day": 1, "answered": {}})

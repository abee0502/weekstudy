from loader import load_progress, save_progress

def save_answer(qid, correct):
    progress = load_progress()
    progress["answered"][str(qid)] = "correct" if correct else "wrong"
    save_progress(progress)

def get_progress():
    progress = load_progress()
    answered_today = sum(1 for qid in progress["answered"] if int(qid) <= progress["day"] * 40 and (int(qid) > (progress["day"] - 1) * 40))
    return {
        "answered_today": answered_today,
        "total_answered": len(progress["answered"]),
        "day": progress["day"]
    }

def reset_progress():
    save_progress({"day": 1, "answered": {}})

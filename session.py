from loader import load_progress, save_progress

def get_today_batch(flashcards, day):
    start = (day - 1) * 40
    end = day * 40
    return flashcards[start:end]

def increment_day():
    progress = load_progress()
    progress["day"] = min(progress["day"] + 1, 7)
    save_progress(progress)

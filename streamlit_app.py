import streamlit as st

from session import get_today_batch
from scoring import get_progress_counts, reset_all_answers
from quiz_mode import run_quiz_mode
from flashcard_mode import run_flashcard_mode
from mistake_review import run_mistake_review

# ───────────────────────────────────────────────────────────────────────────────
# Main Streamlit entry point
st.set_page_config(page_title="7-Day Flashcard App", layout="wide")

st.title("7-Day Flashcard App")

# Sidebar: Mode Selector + Navigation
with st.sidebar:
    st.header("Mode Selector")
    mode = st.radio("Choose mode:", ["Quiz", "Flashcard", "Mistake Review", "Review Only"])

    st.write("---")
    st.header("Progress Tracker")
    counts = get_progress_counts()
    st.write(f"Day: **{counts['day']}/7**")
    # We need to know how many questions in today's day. 
    # We can approximate by reading flashcards and slicing, but for simplicity, show answered_today only.
    st.write(f"Answered Today: **{counts['answered_today']}**")
    st.write(f"Total Answered: **{counts['total_answered']}/278**")
    st.write("---")

    if st.button("Next Day"):
        if counts["answered_today"] < 40:
            st.warning("You must answer all 40 questions for today before advancing.")
        else:
            from session import increment_day
            increment_day()
            st.experimental_rerun()

    if st.button("Reset All Progress"):
        reset_all_answers()
        st.experimental_rerun()

# ───────────────────────────────────────────────────────────────────────────────
# Depending on mode, call the appropriate function
if mode == "Quiz":
    run_quiz_mode()

elif mode == "Flashcard":
    run_flashcard_mode()

elif mode == "Mistake Review":
    run_mistake_review()

elif mode == "Review Only":
    # “Review Only” is same as showing all questions + correct answers for today.
    from loaders import load_flashcards, load_progress
    from session import get_today_batch

    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)
    daily_batch = get_today_batch(all_flashcards, day)

    st.header(f"Review: Day {day} Questions + Correct Answers")
    for card in daily_batch:
        qid = card["id"]
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.markdown(f"*{card['instruction']}*")
        for letter, text in card["options"].items():
            st.write(f"- {letter}. {text}")
        correct_letters = ", ".join(card["answers"])
        st.success(f"Correct answer(s): {correct_letters}")
        st.write("---")

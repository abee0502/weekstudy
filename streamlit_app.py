# ───────────────────────────────────────────────────────────────────────────────
# streamlit_app.py
# ───────────────────────────────────────────────────────────────────────────────

import streamlit as st
from loaders import load_flashcards, load_progress
from session import get_today_batch, increment_day, reset_day
from scoring import save_answer, get_progress_counts, reset_all_answers

st.set_page_config(
    page_title="7-Day Flashcard Memorization",
    layout="wide"
)

# ─── Load Data ─────────────────────────────────────────────────────────────────
all_flashcards = load_flashcards()
prog = load_progress()
day = prog.get("day", 1)

st.title(f"Flashcard Practice – Day {day} of 7")

# ─── Which Questions for Today? ────────────────────────────────────────────────
daily_batch = get_today_batch(all_flashcards, day)

# Check which questions have already been answered
answered_dict = prog.get("answered", {})  # keys are strings like "5", values "correct"/"wrong"

# ─── Show Each Question + Options ──────────────────────────────────────────────
st.write(f"Questions for Day {day}: {len(daily_batch)}")
progress_counts = get_progress_counts()

for card in daily_batch:
    qid = card["id"]
    st.markdown(f"**Q{qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # If this question is already in answered_dict, just show the result
    if str(qid) in answered_dict:
        status = answered_dict[str(qid)]
        if status == "correct":
            st.success("✅ You answered this correctly.")
        else:
            # show which letters were correct
            correct_letters = ", ".join(card["answers"])
            st.error(f"❌ You answered this incorrectly.  (Correct: {correct_letters})")
        st.write("---")
        continue

    # Otherwise, render buttons for each option letter
    cols = st.columns(len(card["options"]))
    for i, (letter, text) in enumerate(card["options"].items()):
        with cols[i]:
            btn_key = f"{qid}_{letter}"
            if st.button(f"{letter}. {text}", key=btn_key):
                # Record answer
                is_correct = letter in card["answers"]
                save_answer(qid, is_correct)
                # Streamlit will automatically rerun the script now; on the next run,
                # this question will appear under the "already answered" branch.
    st.write("---")

# ─── Sidebar: Progress + Navigation ────────────────────────────────────────────
with st.sidebar:
    st.header("Progress Tracker")
    st.write(f"Day: **{progress_counts['day']}/7**")
    st.write(f"Answered Today: **{progress_counts['answered_today']}/{len(daily_batch)}**")
    st.write(f"Total Answered: **{progress_counts['total_answered']}/278**")

    st.write("---")
    if st.button("Next Day"):
        if progress_counts["answered_today"] < len(daily_batch):
            st.warning("Please answer all questions for today before moving on.")
        else:
            increment_day()
            st.experimental_rerun()  # This is fine here because we want to move to the next day

    if st.button("Reset All Progress"):
        reset_all_answers()
        st.experimental_rerun()

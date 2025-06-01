import streamlit as st
from loaders import load_flashcards, load_progress
from session import get_today_batch, increment_day, reset_day
from scoring import save_answer, get_progress_counts, reset_all_answers

# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="7-Day Flashcard Memorization",
    layout="wide"
)

# Load everything
all_flashcards = load_flashcards()
prog = load_progress()
day = prog.get("day", 1)

st.title(f"Flashcard Practice – Day {day} of 7")

# Get only today's slice
daily_batch = get_today_batch(all_flashcards, day)

# ─── Main Flashcard Loop ──────────────────────────────────────────────────────
st.write(f"Total questions for Day {day}: {len(daily_batch)}")
progress_counts = get_progress_counts()

# Show each question with its options as buttons
for card in daily_batch:
    # card must be a dict with keys "id", "question", "options", "answers"
    qid = card["id"]
    st.markdown(f"**Q{qid}:** {card['question']}")

    # Render buttons for each possible option
    cols = st.columns(len(card["options"]))
    for i, option in enumerate(card["options"]):
        with cols[i]:
            if st.button(option, key=f"{qid}_{option}"):
                is_correct = option in card["answers"]
                save_answer(qid, is_correct)
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Wrong.")
                # After answering, prevent double‐click miscounts
                st.experimental_rerun()

    st.write("---")  # horizontal separator between cards

# ─── Sidebar: Progress + Navigation ───────────────────────────────────────────
with st.sidebar:
    st.header("Progress Tracker")
    st.write(f"Day: **{day}/7**")
    st.write(f"Answered Today: **{progress_counts['answered_today']}/{len(daily_batch)}**")
    st.write(f"Total Answered: **{progress_counts['total_answered']}/278**")

    st.write("---")
    if st.button("Next Day"):
        # Only allow advancing if they’ve answered all of today's batch
        if progress_counts["answered_today"] < len(daily_batch):
            st.warning("Please answer all questions for today before moving on.")
        else:
            increment_day()
            st.experimental_rerun()

    if st.button("Review Wrong Answers"):
        st.experimental_rerun()  # you can detect a "mode" and show only wrong ones, see note below

    if st.button("Reset All Progress"):
        reset_all_answers()
        st.experimental_rerun()

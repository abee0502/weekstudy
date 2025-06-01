import streamlit as st
from loaders import load_flashcards, load_progress
from session import get_today_batch, increment_day, reset_day
from scoring import save_answer, get_progress_counts, reset_all_answers

# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="7-Day Flashcard Memorization",
    layout="wide"
)

# ─── Load Data ─────────────────────────────────────────────────────────────────
all_flashcards = load_flashcards()
prog = load_progress()
day = prog.get("day", 1)

st.title(f"Flashcard Practice – Day {day} of 7")

# ─── Get Today’s 40-Question Slice ──────────────────────────────────────────────
daily_batch = get_today_batch(all_flashcards, day)

# Debug prints (optional – remove once things run correctly)
# st.write(">>> all_flashcards[:2]:", all_flashcards[:2])
# st.write(">>> daily_batch[:2]:", daily_batch[:2])

# ─── Main Loop: Show Each Question + Options ───────────────────────────────────
st.write(f"Questions for Day {day}: {len(daily_batch)}")
progress_counts = get_progress_counts()

for card in daily_batch:
    # card is a dict: { "id", "question", "instruction", "options", "answers" }
    qid = card["id"]
    st.markdown(f"**Q{qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # We have options as a dict, e.g. { "A": "Info records", "B": "Quota arrangements", … }
    cols = st.columns(len(card["options"]))
    for i, (letter, text) in enumerate(card["options"].items()):
        with cols[i]:
            btn_key = f"{qid}_{letter}"
            if st.button(f"{letter}. {text}", key=btn_key):
                is_correct = letter in card["answers"]
                save_answer(qid, is_correct)
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong. (Correct: {', '.join(card['answers'])})")
                # Immediately rerun so you can't double-click
                st.experimental_rerun()

    st.write("---")  # horizontal rule

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
            st.experimental_rerun()

    if st.button("Reset All Progress"):
        reset_all_answers()
        st.experimental_rerun()

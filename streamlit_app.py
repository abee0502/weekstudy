import streamlit as st
from utils.loader import load_flashcards
from utils.session import get_today_batch, increment_day
from utils.scoring import save_answer, get_progress, reset_progress

flashcards = load_flashcards()
day = st.session_state.get("day", 1)

st.title(f"Flashcard Practice - Day {day}/7")

# Show 40 questions for today
daily_batch = get_today_batch(flashcards, day)

for card in daily_batch:
    st.markdown(f"**Q{card['id']}:** {card['question']}")
    for option in card['options']:
        if st.button(option, key=f"{card['id']}_{option}"):
            correct = option in card['answers']
            save_answer(card['id'], correct)

# Progress
progress = get_progress()
st.sidebar.write(f"✅ Answered Today: {progress['answered_today']}/40")
st.sidebar.write(f"📊 Total Progress: {progress['total_answered']}/278")

# Navigation
if st.button("Next Day") and progress['answered_today'] >= 40:
    increment_day()
    st.experimental_rerun()

if st.sidebar.button("Review Wrongs"):
    st.session_state["mode"] = "review"
    st.experimental_rerun()

if st.sidebar.button("Reset All"):
    reset_progress()
    st.experimental_rerun()

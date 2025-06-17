import streamlit as st
import os
from utils.utils import load_questions, get_day_questions, save_json, clear_day_mistakes, clear_bulk_mistakes
from day_practice.day_flashcards import run_flashcard_mode
from quiz_mode import run_quiz_mode
from day_practice.day_review_mode import run_review_mode
from day_practice.day_mistakes import run_mistake_review_mode
from day_practice.day_mistake_practice import run_mistake_practice_mode
from bulk_practice.bulk_practice_mode import run_bulk_practice_mode
from bulk_practice.bulk_mistake_tools import (
    show_all_bulk_mistakes,
    practice_bulk_mistakes
)
from bulk_practice.bulk_review_mode import run_bulk_review_mode

DAY_MISTAKES_FILE = "day_practice/data/day_mistakes.json"
BULK_MISTAKES_FILE = "bulk_practice/data/bulk_mistakes.json"

st.set_page_config(page_title="MM Prep Flashcards", layout="wide")
st.title("📚 MM Prep - Study Tool")

all_questions = load_questions("questions.json")

# ─── Main Mode Selection ────────────────────────────────────────────────
main_mode = st.sidebar.radio("Main Mode", [
    "Day Practice Mode",
    "Bulk Practice Mode"
])

if main_mode == "Day Practice Mode":
    st.sidebar.markdown("### Day Practice Options")
    day = st.sidebar.selectbox("Choose study day (1–7)", list(range(1, 8)))
    day_questions = get_day_questions(all_questions, day)
    day_mode = st.sidebar.radio("Day Mode", [
        "Flashcard Mode",
        "Review Mode",
        "Mistake Review Mode",
        "Mistake Practice Mode",
        "🧹 Clear Mistakes"
    ])

    if day_mode == "Flashcard Mode":
        run_flashcard_mode(day_questions, day)
    elif day_mode == "Review Mode":
        run_review_mode(day_questions, day)
    elif day_mode == "Mistake Review Mode":
        run_mistake_review_mode(day)
    elif day_mode == "Mistake Practice Mode":
        run_mistake_practice_mode(day)
    elif day_mode == "🧹 Clear Mistakes":
        st.header("🧹 Clear Mistake Log")
        if st.button(f"Delete Mistakes for Day {day}"):
            from utils.utils import clear_day_mistakes
            if clear_day_mistakes(DAY_MISTAKES_FILE, day):
                st.success(f"✅ Mistakes for Day {day} have been cleared.")
        else:
            st.info(f"No mistakes found for Day {day}.")

elif main_mode == "Bulk Practice Mode":
    st.sidebar.markdown("### Bulk Practice Options")

    if "bulk_days" not in st.session_state:
        st.session_state.bulk_days = []
    if "confirmed" not in st.session_state:
        st.session_state.confirmed = False

    if not st.session_state.confirmed:
        selected_days = st.sidebar.multiselect("Select days to practice", list(range(1, 8)), default=st.session_state.bulk_days)
        if st.sidebar.button("Confirm Selection"):
            st.session_state.bulk_days = selected_days
            st.session_state.confirmed = True
            st.rerun()
    else:
        st.sidebar.write(f"Selected days: {st.session_state.bulk_days}")
        if st.sidebar.button("Reset Selection"):
             st.session_state.bulk_days = []
             st.session_state.confirmed = False
             st.rerun()

    bulk_mode = st.sidebar.radio("Bulk Mode", [
        "Bulk Flashcard Mode",
        "Bulk Review Mode",
        "Bulk Mistake Review",
        "Bulk Practice Mistakes",
        "🧹 Clear Bulk Mistakes"
    ])

    days =  st.session_state.bulk_days

    if bulk_mode == "Bulk Flashcard Mode":
        if st.session_state.confirmed:
            run_bulk_practice_mode(all_questions, days)
        else:
            st.info("Please select days and confirm to use this mode.")

    elif bulk_mode == "Bulk Review Mode":
        if st.session_state.confirmed:
            run_bulk_review_mode(all_questions, days)
        else:
            st.info("Please select days and confirm to use this mode.")

    elif bulk_mode == "Bulk Mistake Review":
        show_all_bulk_mistakes()
    elif bulk_mode == "Bulk Practice Mistakes":
        practice_bulk_mistakes()
    elif bulk_mode == "🧹 Clear Bulk Mistakes":
        st.header("🧹 Clear Bulk Mistake Log")
        if st.button("Delete All Bulk Practice Mistake History"):
            if clear_bulk_mistakes(BULK_MISTAKES_FILE):
                st.success("✅ All bulk mistakes have been cleared.")
            else:
                st.info("No bulk mistakes to clear yet.")
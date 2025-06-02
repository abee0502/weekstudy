import streamlit as st
import os
from utils import load_questions, get_day_questions, save_json
from flashcards import run_flashcard_mode
from quiz_mode import run_quiz_mode
from review_mode import run_review_mode
from mistakes import run_mistake_review_mode

MISTAKES_FILE = "mistakes.json"

# ─── App Config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="MM Prep Flashcards", layout="wide")
st.title("📚 MM Prep - Study Tool")

# ─── Load Questions ───────────────────────────────────────────────────────
all_questions = load_questions("questions.json")

# ─── Day Selection ────────────────────────────────────────────────────────
day = st.sidebar.selectbox("Choose study day (1–7)", list(range(1, 8)))
day_questions = get_day_questions(all_questions, day)

# ─── Mode Selection ───────────────────────────────────────────────────────
mode = st.sidebar.radio("Choose mode", [
    "Flashcard Mode",
    "Quiz Mode",
    "Review Mode",
    "Mistake Review Mode",
    "Mistake Practice Mode",    # ← newly added
    "🧹 Clear Mistakes"
])


# ─── Route Based on Mode ──────────────────────────────────────────────────
if mode == "Flashcard Mode":
    run_flashcard_mode(day_questions, day)

elif mode == "Quiz Mode":
    run_quiz_mode(day_questions, day)

elif mode == "Review Mode":
    run_review_mode(day_questions, day)

elif mode == "Mistake Review Mode":
    run_mistake_review_mode(day)

# ← Insert this new clause:
elif mode == "Mistake Practice Mode":
    run_mistake_practice_mode(day)

elif mode == "🧹 Clear Mistakes":
    st.header("🧹 Clear Mistake Log")
    if st.button("Delete All Mistake History"):
        if os.path.exists(MISTAKES_FILE):
            save_json(MISTAKES_FILE, {})
            st.success("✅ All mistakes have been cleared.")
        else:
            st.info("No mistakes to clear yet.")

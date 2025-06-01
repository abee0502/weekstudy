# ───────────────────────────────────────────────────────────────────────────────
# streamlit_app.py
# ───────────────────────────────────────────────────────────────────────────────

import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch, increment_day, reset_day
from scoring import save_answer, get_progress_counts, reset_all_answers

# ───────────────────────────────────────────────────────────────────────────────
# Page config
st.set_page_config(
    page_title="7-Day Flashcard Memorization",
    layout="wide"
)

# ───────────────────────────────────────────────────────────────────────────────
# Load data
all_flashcards = load_flashcards()
prog = load_progress()
day = prog.get("day", 1)

# Today's subset of 40 questions
daily_batch = get_today_batch(all_flashcards, day)
answered_dict = prog.get("answered", {})  # { "qid_str": "correct"/"partial"/"wrong", ... }

# ───────────────────────────────────────────────────────────────────────────────
# Sidebar: Mode Selector + Navigation
with st.sidebar:
    st.header("Mode Selector")
    mode = st.radio("Choose mode:", ["Quiz", "Flashcard", "Review"])

    st.write("---")
    st.header("Progress Tracker")
    counts = get_progress_counts()
    st.write(f"Day: **{counts['day']}/7**")
    st.write(f"Answered Today: **{counts['answered_today']}/{len(daily_batch)}**")
    st.write(f"Total Answered: **{counts['total_answered']}/278**")
    st.write("---")

    if st.button("Next Day"):
        if counts["answered_today"] < len(daily_batch):
            st.warning("Please answer all questions for today before moving on.")
        else:
            increment_day()
            st.experimental_rerun()

    if st.button("Reset All Progress"):
        reset_all_answers()
        st.experimental_rerun()

# ───────────────────────────────────────────────────────────────────────────────
# If mode changed, reset flashcard‐state variables
if "prev_mode" not in st.session_state:
    st.session_state.prev_mode = mode

if mode != st.session_state.prev_mode:
    # Clear any flashcard session state when switching away
    for key in ["flashcard_qid", "flashcard_submitted", "flashcard_result"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.prev_mode = mode

# ───────────────────────────────────────────────────────────────────────────────
# REVIEW MODE: Show all questions + correct answers
if mode == "Review":
    st.title(f"Review: Day {day} Questions + Correct Answers")
    for card in daily_batch:
        qid = card["id"]
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.markdown(f"*{card['instruction']}*")
        for letter, text in card["options"].items():
            st.write(f"- {letter}. {text}")
        correct_letters = ", ".join(card["answers"])
        st.success(f"Correct answer(s): {correct_letters}")
        st.write("---")
    st.stop()

# ───────────────────────────────────────────────────────────────────────────────
# QUIZ MODE: All questions on one page
if mode == "Quiz":
    st.title(f"Day {day} Quiz Mode – Select & Submit Answers")

    for card in daily_batch:
        qid = card["id"]
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.markdown(f"*{card['instruction']}*")

        # If already answered, display previous result
        if str(qid) in answered_dict:
            result = answered_dict[str(qid)]
            if result == "correct":
                st.success("✅ You answered this correctly.")
            elif result == "partial":
                corr = ", ".join(card["answers"])
                st.warning(f"⚠️ Partially correct. Correct answer(s): {corr}")
            else:  # "wrong"
                corr = ", ".join(card["answers"])
                st.error(f"❌ Wrong. Correct answer(s): {corr}")
            st.write("---")
            continue

        # Otherwise, show checkboxes + submit button
        with st.form(key=f"quiz_form_{qid}"):
            selected = []
            for letter, text in card["options"].items():
                if st.checkbox(f"{letter}. {text}", key=f"{qid}_{letter}"):
                    selected.append(letter)

            submitted = st.form_submit_button("Submit")
            if submitted:
                correct_set = set(card["answers"])
                selected_set = set(selected)

                if selected_set == correct_set:
                    outcome = "correct"
                    st.success("✅ Correct!")
                elif selected_set & correct_set:
                    outcome = "partial"
                    corr_letters = ", ".join(card["answers"])
                    st.warning(f"⚠️ Partially correct. Correct answer(s): {corr_letters}")
                else:
                    outcome = "wrong"
                    corr_letters = ", ".join(card["answers"])
                    st.error(f"❌ Wrong. Correct answer(s): {corr_letters}")

                save_answer(qid, outcome)
        st.write("---")

# ───────────────────────────────────────────────────────────────────────────────
# FLASHCARD MODE: One random unanswered question at a time with instant feedback
if mode == "Flashcard":
    st.title(f"Day {day} Flashcard Mode")

    # Build list of unanswered cards
    unanswered = [card for card in daily_batch if str(card["id"]) not in answered_dict]

    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
        st.stop()

    # Step 1: If no current flashcard in session_state, pick one at random
    if "flashcard_qid" not in st.session_state:
        chosen = random.choice(unanswered)
        st.session_state.flashcard_qid = chosen["id"]
        st.session_state.flashcard_submitted = False
        st.session_state.flashcard_result = None

    # Load the current card
    current_qid = st.session_state.flashcard_qid
    # Find its dict in daily_batch (could index by id map, but a simple loop suffices)
    card = next(c for c in daily_batch if c["id"] == current_qid)

    # Display question + instruction
    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # If user has not yet submitted for this flashcard:
    if not st.session_state.flashcard_submitted:
        with st.form(key=f"fc_form_{current_qid}"):
            selected = []
            for letter, text in card["options"].items():
                if st.checkbox(f"{letter}. {text}", key=f"fc_{current_qid}_{letter}"):
                    selected.append(letter)

            submitted = st.form_submit_button("Submit Answer")
            if submitted:
                correct_set = set(card["answers"])
                selected_set = set(selected)

                if selected_set == correct_set:
                    outcome = "correct"
                    st.success("✅ Correct!")
                elif selected_set & correct_set:
                    outcome = "partial"
                    corr_letters = ", ".join(card["answers"])
                    st.warning(f"⚠️ Partially correct. Correct answer(s): {corr_letters}")
                else:
                    outcome = "wrong"
                    corr_letters = ", ".join(card["answers"])
                    st.error(f"❌ Wrong. Correct answer(s): {corr_letters}")

                # Record in session state and in persistent storage
                st.session_state.flashcard_submitted = True
                st.session_state.flashcard_result = outcome
                save_answer(current_qid, outcome)

                # Don’t immediately pick a new card—wait for “Next” click
        st.write("---")

    else:
        # Step 2: Show instant feedback (again) and a Next button
        outcome = st.session_state.flashcard_result
        if outcome == "correct":
            st.success("✅ Correct!")
        elif outcome == "partial":
            corr_letters = ", ".join(card["answers"])
            st.warning(f"⚠️ Partially correct. Correct answer(s): {corr_letters}")
        else:
            corr_letters = ", ".join(card["answers"])
            st.error(f"❌ Wrong. Correct answer(s): {corr_letters}")

        st.write("---")
        if st.button("Next Flashcard"):
            # Clear flashcard-specific keys and rerun to pick a new one
            del st.session_state.flashcard_qid
            del st.session_state.flashcard_submitted
            del st.session_state.flashcard_result
            st.experimental_rerun()

    # Show how many remain (optional)
    updated_unanswered = [c for c in daily_batch if str(c["id"]) not in load_progress().get("answered", {})]
    st.write(f"Remaining: **{len(updated_unanswered)}/{len(daily_batch)}** unanswered questions today.")

import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch, increment_day, reset_day
from scoring import save_answer, get_progress_counts, reset_all_answers

st.set_page_config(
    page_title="7-Day Flashcard Memorization",
    layout="wide"
)

# ─── Load All Flashcards & Progress ─────────────────────────────────────────────
all_flashcards = load_flashcards()
prog = load_progress()
day = prog.get("day", 1)

st.title(f"Flashcard App – Day {day} of 7")

# ─── Get Today’s Slice ───────────────────────────────────────────────────────────
daily_batch = get_today_batch(all_flashcards, day)
answered_dict = prog.get("answered", {})  # {"qid_str": "correct"/"partial"/"wrong", ...}

# ─── Sidebar: Mode Selector + Navigation ────────────────────────────────────────
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

# ─── Review Mode: Show All Questions + Correct Answers ───────────────────────────
if mode == "Review":
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
    st.stop()

# ─── Quiz Mode: All Questions on One Page ────────────────────────────────────────
if mode == "Quiz":
    st.header(f"Day {day} Quiz Mode – Select & Submit Answers")

    for card in daily_batch:
        qid = card["id"]
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.markdown(f"*{card['instruction']}*")

        # If already answered, display result
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

# ─── Flashcard Mode: One Random Unanswered Question at a Time ───────────────────
if mode == "Flashcard":
    st.header(f"Day {day} Flashcard Mode")

    # Build list of unanswered cards
    unanswered = [card for card in daily_batch if str(card["id"]) not in answered_dict]

    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
    else:
        # Pick a random unanswered question
        card = random.choice(unanswered)
        qid = card["id"]
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.markdown(f"*{card['instruction']}*")

        with st.form(key=f"fc_form_{qid}"):
            selected = []
            for letter, text in card["options"].items():
                if st.checkbox(f"{letter}. {text}", key=f"fc_{qid}_{letter}"):
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
                save_answer(qid, outcome)
                st.experimental_rerun()

        st.write(f"Progress: **{len(daily_batch) - len(unanswered)}/{len(daily_batch)}** answered today")

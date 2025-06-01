import streamlit as st
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

st.title(f"Flashcard Practice – Day {day} of 7")

# ─── Determine Today's Slice ────────────────────────────────────────────────────
daily_batch = get_today_batch(all_flashcards, day)

# Determine which questions are already answered
answered_dict = prog.get("answered", {})  # keys are strings like "5", values = "correct"/"partial"/"wrong"

# Sidebar: mode toggles
st.sidebar.header("Mode Selector")
show_review = st.sidebar.checkbox("Review Today's Answers")
st.sidebar.write("---")

# ─── If Reviewing, Show All Questions + Correct Answers ────────────────────────
if show_review:
    st.header(f"Review: Day {day} Questions + Correct Answers")
    for card in daily_batch:
        qid = card["id"]
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.markdown(f"*{card['instruction']}*")
        # Show each option letter + text
        for letter, text in card["options"].items():
            st.write(f"- {letter}. {text}")
        # Show the correct answers
        correct_letters = ", ".join(card["answers"])
        st.success(f"Correct answer(s): {correct_letters}")
        st.write("---")
    st.write("🔄 Uncheck “Review Today's Answers” in the sidebar to return to practice mode.")
    st.stop()  # Don’t show the rest (practice mode) when in review mode

# ─── Practice Mode: Show Each Question + a Form ─────────────────────────────────
st.header(f"Day {day} Practice – Select & Submit Your Answer(s)")

progress_counts = get_progress_counts()

for card in daily_batch:
    qid = card["id"]
    st.markdown(f"**Q{qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # If this question is already answered, show the stored result
    if str(qid) in answered_dict:
        result = answered_dict[str(qid)]
        if result == "correct":
            st.success("✅ You answered this correctly.")
        elif result == "partial":
            # Show partial result plus correct letters
            corr = ", ".join(card["answers"])
            st.warning(f"⚠️ Partially correct. Correct answer(s): {corr}")
        else:  # "wrong"
            corr = ", ".join(card["answers"])
            st.error(f"❌ Wrong. Correct answer(s): {corr}")
        st.write("---")
        continue

    # Otherwise, create a form for this question (so user can pick multiple checkboxes)
    with st.form(key=f"form_{qid}"):
        # Create a checkbox for each option
        selected = []
        for letter, text in card["options"].items():
            # Each checkbox returns True/False
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
                # At least one correct letter chosen, but not a full match
                outcome = "partial"
                corr_letters = ", ".join(card["answers"])
                st.warning(f"⚠️ Partially correct. Correct answer(s): {corr_letters}")
            else:
                outcome = "wrong"
                corr_letters = ", ".join(card["answers"])
                st.error(f"❌ Wrong. Correct answer(s): {corr_letters}")

            # Save the result ("correct"/"partial"/"wrong")
            save_answer(qid, outcome)
            # Streamlit will automatically rerun after a form submission, so on the next
            # run this qid will show as "already answered" above.
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
            st.experimental_rerun()

    if st.button("Reset All Progress"):
        reset_all_answers()
        st.experimental_rerun()

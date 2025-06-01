import streamlit as st
import random

from loaders import load_flashcards
from session import get_today_batch
from scoring import record_attempt, load_progress

def run_flashcard_mode():
    """
    Renders one random unanswered question at a time.
    As soon as the user submits an answer, instant feedback appears,
    and the next random unanswered question is shown automatically.
    Also displays a “rounds” counter (how many flashcard attempts made this session).
    """

    # Load flashcards + progress to know which day we’re on + answered set
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Flashcard Mode")

    daily_batch = get_today_batch(all_flashcards, day)
    answered_dict = prog.get("answered", {})

    # Build list of unanswered cards
    unanswered = [card for card in daily_batch if str(card["id"]) not in answered_dict]

    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
        return

    # Initialize session_state counters
    if "rounds" not in st.session_state:
        st.session_state.rounds = 0

    # Initialize or pick a new current_qid if needed
    if "current_qid" not in st.session_state or str(st.session_state.current_qid) in answered_dict:
        chosen = random.choice(unanswered)
        st.session_state.current_qid = chosen["id"]
        st.session_state.feedback = None  # reset previous feedback

    # Display rounds indicator
    st.subheader(f"Flashcard Attempts This Session: {st.session_state.rounds}")

    # Fetch the current card
    current_qid = st.session_state.current_qid
    card = next(c for c in daily_batch if c["id"] == current_qid)

    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # If there is existing feedback from the last submission, show it above the form
    if st.session_state.feedback is not None:
        st.write(st.session_state.feedback)
        st.write("---")

    # Show the form for this flashcard
    with st.form(key=f"fc_single_form_{current_qid}", clear_on_submit=False):
        selected = []
        for letter, text in card["options"].items():
            if st.checkbox(f"{letter}. {text}", key=f"fc_{current_qid}_{letter}"):
                selected.append(letter)

        submitted = st.form_submit_button("Submit Answer")
        if submitted:
            correct_set = set(card["answers"])
            selected_set = set(selected)

            if selected_set == correct_set:
                is_correct = True
                feedback_msg = "✅ Correct!"
            else:
                is_correct = False
                corr_letters = ", ".join(card["answers"])
                feedback_msg = f"❌ Wrong. Correct answer(s): {corr_letters}"

            # Record attempt + update mistakes if wrong
            record_attempt(current_qid, is_correct)

            # Increment the rounds counter
            st.session_state.rounds += 1

            # Store feedback into session_state so it persists after rerun
            st.session_state.feedback = feedback_msg

            # Immediately pick a new unanswered question (so next rerun shows it)
            # BUT store feedback so user can see it above the next question
            del st.session_state.current_qid  # force picking a new one on next rerun
            st.experimental_rerun()

    # Show how many remain (live update)
    prog_after = load_progress()
    answered_after = prog_after.get("answered", {})
    updated_unanswered = [c for c in daily_batch if str(c["id"]) not in answered_after]
    st.write(f"Remaining unanswered today: **{len(updated_unanswered)}/{len(daily_batch)}**")

import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch
from scoring import record_attempt

def run_flashcard_mode():
    """
    Renders one random unanswered question at a time.
    - User must select at least one checkbox or else a warning appears.
    - After a valid submission, instant feedback appears (✅ or ❌ + correct answer).
    - On the next rerun, a new random unanswered question is chosen automatically.
    - Tracks how many “rounds” (submissions) have occurred in this session.
    """

    # Load all flashcards and current progress (to know day & answered set)
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Flashcard Mode")

    # Get today’s 40-question slice and answered dictionary
    daily_batch = get_today_batch(all_flashcards, day)
    answered_dict = prog.get("answered", {})  # { "qid_str": "correct"/"wrong", ... }

    # Build list of unanswered cards for today
    unanswered = [card for card in daily_batch if str(card["id"]) not in answered_dict]

    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
        return

    # Initialize or pick a new “current_qid” if none exists or if it was just answered
    if "current_qid" not in st.session_state or str(st.session_state.current_qid) in answered_dict:
        chosen = random.choice(unanswered)
        st.session_state.current_qid = chosen["id"]
        st.session_state.feedback = None  # Clear previous feedback

    # Initialize or maintain “rounds” count
    if "rounds" not in st.session_state:
        st.session_state.rounds = 0

    # Display how many rounds (submissions) so far this session
    st.subheader(f"Flashcard Attempts This Session: {st.session_state.rounds}")

    # Fetch the current card object
    current_qid = st.session_state.current_qid
    card = next(c for c in daily_batch if c["id"] == current_qid)

    # If there is feedback from the previous submission, show it first
    if st.session_state.feedback:
        st.write(st.session_state.feedback)
        st.write("---")

    # Display the question and instruction
    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # Render the form for this single flashcard
    with st.form(key=f"fc_single_form_{current_qid}", clear_on_submit=False):
        selected = []
        for letter, text in card["options"].items():
            if st.checkbox(f"{letter}. {text}", key=f"fc_{current_qid}_{letter}"):
                selected.append(letter)

        submitted = st.form_submit_button("Submit Answer")

        if submitted:
            # If no checkbox was selected, show a warning and do NOT proceed
            if not selected:
                st.warning("⚠️ Please select at least one option before submitting.")
            else:
                correct_set = set(card["answers"])
                selected_set = set(selected)

                # Determine correctness
                if selected_set == correct_set:
                    is_correct = True
                    feedback_msg = "✅ Correct!"
                else:
                    is_correct = False
                    corr_letters = ", ".join(card["answers"])
                    feedback_msg = f"❌ Wrong. Correct answer(s): {corr_letters}"

                # Record attempt (updates user_progress.json and mistakes.json)
                record_attempt(current_qid, is_correct)

                # Increment “rounds” counter
                st.session_state.rounds += 1

                # Store feedback so that on the next rerun it will appear above the next question
                st.session_state.feedback = feedback_msg

                # Remove the current_qid so that on the next rerun, a new unanswered question is picked
                del st.session_state.current_qid
                # Note: No explicit st.experimental_rerun() needed—Streamlit reruns automatically after form submission

    # After the form (and possibly a rerun), show how many remain:
    prog_after = load_progress()
    answered_after = prog_after.get("answered", {})
    updated_unanswered = [c for c in daily_batch if str(c["id"]) not in answered_after]
    st.write(f"Remaining unanswered today: **{len(updated_unanswered)}/{len(daily_batch)}**")

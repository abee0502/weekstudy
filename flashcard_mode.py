import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch
from scoring import record_attempt

def run_flashcard_mode():
    """
    Implements Flashcard Mode for Day N:
      - Picks one random unanswered question.
      - Forces the user to select at least one option before accepting submission.
      - After a valid submission, shows instant feedback and then automatically picks the next
        unanswered question on the next rerun.
      - Maintains a 'rounds' counter in session_state (number of submissions this session).
    """

    # ─── Load all flashcards and current progress (to know 'day' and 'answered' set)
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Flashcard Mode")

    # ─── Get today’s 40‐question slice and the 'answered' dictionary
    daily_batch = get_today_batch(all_flashcards, day)
    answered_dict = prog.get("answered", {})  # { "qid_str": "correct"/"wrong", ... }

    # ─── Build list of unanswered cards for today
    unanswered = [card for card in daily_batch if str(card["id"]) not in answered_dict]

    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
        return

    # ─── Initialize or pick a new 'current_qid' if needed
    # If there is no 'current_qid' in session_state, or if that question has just been answered,
    # pick a new random one from the unanswered list.
    if ("current_qid" not in st.session_state) or (str(st.session_state["current_qid"]) in answered_dict):
        chosen = random.choice(unanswered)
        st.session_state["current_qid"] = chosen["id"]
        st.session_state["feedback"] = None  # clear any old feedback

    # ─── Initialize or maintain 'rounds' counter in session_state
    if "rounds" not in st.session_state:
        st.session_state["rounds"] = 0

    # ─── Display the rounds counter at the top
    st.subheader(f"Flashcard Attempts This Session: {st.session_state['rounds']}")

    # ─── Fetch the card corresponding to 'current_qid'
    current_qid = st.session_state["current_qid"]
    card = next(c for c in daily_batch if c["id"] == current_qid)

    # ─── If there is feedback from the previous submission, show it first
    if st.session_state.get("feedback"):
        st.write(st.session_state["feedback"])
        st.write("---")

    # ─── Display the question and instruction
    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # ─── Render the form for this single flashcard
    with st.form(key=f"fc_single_form_{current_qid}", clear_on_submit=False):
        selected = []  # will collect selected letters
        for letter, text in card["options"].items():
            if st.checkbox(f"{letter}. {text}", key=f"fc_{current_qid}_{letter}"):
                selected.append(letter)

        submitted = st.form_submit_button("Submit Answer")

        if submitted:
            # If no option was selected, show a warning and do NOT proceed to next card
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

                # Record the attempt:
                #  - Marks question as 'correct' or 'wrong' in user_progress.json
                #  - If wrong, increments its count in mistakes.json
                record_attempt(current_qid, is_correct)

                # Increment the 'rounds' counter
                st.session_state["rounds"] += 1

                # Store feedback so that on the next rerun it appears above the next question
                st.session_state["feedback"] = feedback_msg

                # Remove current_qid so that on the next rerun, a new random unanswered question is chosen
                del st.session_state["current_qid"]
                # No explicit st.experimental_rerun() is needed here; Streamlit reruns automatically
                # after a form submission.

    # ─── After the form (and possible rerun), show how many remain unanswered
    prog_after = load_progress()
    answered_after = prog_after.get("answered", {})
    updated_unanswered = [c for c in daily_batch if str(c["id"]) not in answered_after]
    st.write(f"Remaining unanswered today: **{len(updated_unanswered)}/{len(daily_batch)}**")

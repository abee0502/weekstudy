import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch
from scoring import record_attempt

def run_flashcard_mode():
    """
    Implements Flashcard Mode for the chosen day:
      1. On first render (or after clicking “Next Question”), pick a random unanswered q.
      2. Display the rounds counter and, if present, last feedback above the question.
      3. Show the question + checkboxes + “Submit Answer” button.
      4. If submitted with no selection → warning, same question stays on screen.
         If submitted with ≥1 selection:
          • Display feedback including the correct answer(s).
          • Set session_state["awaiting_next"] = True so we show “Next Question” button.
          • Record attempt (updates user_progress.json and mistakes.json).
          • Increment session_state["rounds"].
      5. If session_state["awaiting_next"] is True, we lock the question in place until
         the user clicks “Next Question.” When they do:
          • Pick a fresh random unanswered question (if any remain).
          • Set session_state["awaiting_next"] = False.
          • Clear session_state["last_feedback"] (so next question starts clean).
      6. Repeat until no unanswered remain, then show “done” message.
    """

    # ─── Load all flashcards & progress to know current day and answered set ───────────
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Flashcard Mode")

    # ─── Get today’s 40-question slice and build an “unanswered” list ─────────────────
    daily_batch = get_today_batch(all_flashcards, day)
    answered_dict = prog.get("answered", {})  # { "qid_str": "correct"/"wrong", ... }

    unanswered = [
        card for card in daily_batch 
        if str(card["id"]) not in answered_dict
    ]

    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
        return

    # ─── Initialize or maintain “rounds” counter ──────────────────────────────────────
    if "rounds" not in st.session_state:
        st.session_state["rounds"] = 0

    # ─── Initialize or re‐pick “current_qid” if needed ────────────────────────────────
    # We pick a new random question only if:
    #  ● it’s the very first time this function is running, OR
    #  ● session_state["awaiting_next"] is True and user has clicked “Next Question”.
    if "current_qid" not in st.session_state:
        # First time rendering → pick one unanswered question
        chosen = random.choice(unanswered)
        st.session_state["current_qid"] = chosen["id"]
        st.session_state["last_feedback"] = None
        st.session_state["awaiting_next"] = False

    # ─── Display how many attempts have been made this session ─────────────────────────
    st.subheader(f"Flashcard Attempts This Session: {st.session_state['rounds']}")

    # ─── If there is “last_feedback” from the previous submission, show it ────────────
    if st.session_state.get("last_feedback"):
        st.write(st.session_state["last_feedback"])
        st.write("---")

    # ─── Fetch the current card object by ID ──────────────────────────────────────────
    current_qid = st.session_state["current_qid"]
    card = next(c for c in daily_batch if c["id"] == current_qid)

    # ─── Display question text + instruction ─────────────────────────────────────────
    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # ─── If we are NOT awaiting the user to click “Next Question,” show the form ───────
    if not st.session_state.get("awaiting_next", False):

        with st.form(key=f"fc_form_{current_qid}", clear_on_submit=False):
            selected = []
            for letter, text in card["options"].items():
                if st.checkbox(f"{letter}. {text}", key=f"fc_{current_qid}_{letter}"):
                    selected.append(letter)

            submitted = st.form_submit_button("Submit Answer")

            if submitted:
                # (1) If no box was checked → warning, do nothing else
                if not selected:
                    st.warning("⚠️ Please select at least one option before submitting.")
                else:
                    # (2) Determine correctness
                    correct_set = set(card["answers"])
                    selected_set = set(selected)

                    if selected_set == correct_set:
                        is_correct = True
                        corr_letters = ", ".join(sorted(correct_set))
                        feedback_msg = f"✅ Correct! (Answer: {corr_letters})"
                    else:
                        is_correct = False
                        corr_letters = ", ".join(sorted(correct_set))
                        feedback_msg = f"❌ Wrong. Correct answer(s): {corr_letters}"

                    # (3) Record the attempt (updates user_progress.json and mistakes.json)
                    record_attempt(current_qid, is_correct)

                    # (4) Increment the rounds counter
                    st.session_state["rounds"] += 1

                    # (5) Store feedback and put us in “awaiting_next” state
                    st.session_state["last_feedback"] = feedback_msg
                    st.session_state["awaiting_next"] = True

    else:
        # ─── We ARE awaiting the user to click “Next Question” ─────────────────────────
        # Show a “Next Question” button. When clicked:
        #   • Clear last_feedback
        #   • Set awaiting_next = False so next question can render
        #   • Pick a new random unanswered qid (if any remain)
        if st.button("Next Question"):
            # Clear feedback
            st.session_state["last_feedback"] = None
            st.session_state["awaiting_next"] = False

            # Build list of still-unanswered
            prog_after = load_progress()
            answered_after = prog_after.get("answered", {})
            still_unanswered = [
                c for c in daily_batch 
                if str(c["id"]) not in answered_after
            ]

            if still_unanswered:
                new_card = random.choice(still_unanswered)
                st.session_state["current_qid"] = new_card["id"]
            else:
                # No unanswered remain → remove current_qid to trigger “done”
                del st.session_state["current_qid"]

            # Let Streamlit rerun automatically after button click

    # ─── After form or “Next Question” logic, show how many remain unanswered ─────────
    prog_latest = load_progress()
    answered_latest = prog_latest.get("answered", {})
    still_unanswered = [
        c for c in daily_batch 
        if str(c["id"]) not in answered_latest
    ]
    st.write(f"Remaining unanswered today: **{len(still_unanswered)}/{len(daily_batch)}**")

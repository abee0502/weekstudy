import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch
from scoring import record_attempt

def run_flashcard_mode():
    """
    Implements Flashcard Mode for the chosen day:
      1. On first run (or when session_state["current_qid"] is missing), pick a random unanswered question.
      2. Display rounds counter and (if present) last feedback above the current question.
      3. Show the question + checkboxes + “Submit Answer” button.
      4. If the user clicks “Submit Answer” with no selection → show warning.
         If they select at least one:
          • Evaluate correctness, record attempt (which also increments mistakes if wrong),
          • Increment rounds,
          • Set session_state["last_feedback"] to a string that always includes the correct answer(s),
          • Immediately pick a new random unanswered question (if any) by updating session_state["current_qid"].
      5. Because Streamlit automatically reruns on form submission, the same Python script runs again:
          • The new session_state["current_qid"] is used to show the next question.
          • The session_state["last_feedback"] is displayed above it.
      6. Repeat until no unanswered remain, then show a “done” message.
    """

    # ─── Load all flashcards and current progress (to know day & which are answered) ─────────
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Flashcard Mode")

    # ─── Compute today’s slice of 40 questions and which ones remain unanswered ─────────────
    daily_batch = get_today_batch(all_flashcards, day)
    answered_dict = prog.get("answered", {})  # e.g. { "1": "correct", "2": "wrong", ... }

    unanswered = [
        card for card in daily_batch 
        if str(card["id"]) not in answered_dict
    ]

    # If none remain, show completion and return
    if not unanswered:
        st.success("🎉 All questions for today have been answered!")
        return

    # ─── Initialize session_state["rounds"] if needed ───────────────────────────────────
    if "rounds" not in st.session_state:
        st.session_state["rounds"] = 0

    # ─── If no "current_qid" in session_state, pick one at random from unanswered ────────
    if "current_qid" not in st.session_state:
        chosen = random.choice(unanswered)
        st.session_state["current_qid"] = chosen["id"]
        st.session_state["last_feedback"] = None

    # ─── Display how many attempts have been made this session ────────────────────────────
    st.subheader(f"Flashcard Attempts This Session: {st.session_state['rounds']}")

    # ─── If there is “last_feedback” from a previous submission, show it above ────────────
    if st.session_state.get("last_feedback"):
        st.write(st.session_state["last_feedback"])
        st.write("---")

    # ─── Fetch the current question’s dict by ID ─────────────────────────────────────────
    current_qid = st.session_state["current_qid"]
    card = next(c for c in daily_batch if c["id"] == current_qid)

    # ─── Display the question text and instruction ───────────────────────────────────────
    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # ─── Build a form for this single flashcard question ─────────────────────────────────
    with st.form(key=f"fc_form_{current_qid}", clear_on_submit=False):
        selected = []  # collect which letters are checked

        for letter, text in card["options"].items():
            if st.checkbox(f"{letter}. {text}", key=f"fc_{current_qid}_{letter}"):
                selected.append(letter)

        submitted = st.form_submit_button("Submit Answer")

        if submitted:
            # 1) If no option selected → show warning, stay on same question
            if not selected:
                st.warning("⚠️ Please select at least one option before submitting.")
            else:
                # 2) Evaluate correctness
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

                # 3) Record the attempt (updates user_progress and mistakes.json if wrong)
                record_attempt(current_qid, is_correct)

                # 4) Increment the rounds counter
                st.session_state["rounds"] += 1

                # 5) Save feedback in session_state for display
                st.session_state["last_feedback"] = feedback_msg

                # 6) Pick a new random unanswered question (if any remain)
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
                    # If none remain, clear current_qid so next run shows “done”
                    del st.session_state["current_qid"]

                # No need for st.experimental_rerun()—Streamlit will rerun automatically after form submission.

    # ─── After form (and possible automatic rerun), show how many are still unanswered ─────
    prog_latest = load_progress()
    answered_latest = prog_latest.get("answered", {})
    still_unanswered = [
        c for c in daily_batch 
        if str(c["id"]) not in answered_latest
    ]
    st.write(f"Remaining unanswered today: **{len(still_unanswered)}/{len(daily_batch)}**")

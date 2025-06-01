# ───────────────────────────────────────────────────────────────────────────────
# flashcard_mode.py
#
# Simplified Flashcard Mode (all on one page, explicit “Next Question”):
# - Uses today’s slice of 40 from flashcards.json (via session.get("day")).
# - Creates a random order once, stored in session_state["flash_order"].
# - Shows one question at a time:
#     • Checkboxes for options, “Submit Answer” button.
#     • Blocks submit if no option selected.
#     • After valid submit: shows feedback (✅/❌ + correct answers) and “Next Question” button.
#     • Only on “Next Question” click does it advance to the next question.
# - Tracks “rounds” in session_state["rounds"].
# - Marks each question as answered in user_progress.json (via record_attempt), and increments mistakes if wrong.
# - When all 40 are done, shows a “🎉 Done!” message.
# ───────────────────────────────────────────────────────────────────────────────

import streamlit as st
import random

from loaders import load_flashcards, load_progress
from session import get_today_batch
from scoring import record_attempt

def run_flashcard_mode():
    """
    Displays flashcards one at a time for today’s 40 questions. Requires:
      - session_state["flash_order"]: a list of question‐IDs in random order
      - session_state["flash_index"]: current index into flash_order
      - session_state["rounds"]: how many submissions have been made
      - session_state["feedback"]: feedback string to show above the question
      - session_state["waiting_next"]: True if we just submitted and now need “Next Question”
    """

    # ─── Load all flashcards & current day to get today’s 40-card slice ─────────────
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Flashcard Mode (40 questions)")

    today_cards = get_today_batch(all_flashcards, day)
    total = len(today_cards)  # typically 40, except possibly last day

    # ─── Initialize session_state values on first run ───────────────────────────────
    if "flash_order" not in st.session_state:
        # Build a list of question‐IDs (the “id” field from each card) for today
        ids_for_today = [card["id"] for card in today_cards]
        random.shuffle(ids_for_today)
        st.session_state["flash_order"] = ids_for_today
        st.session_state["flash_index"] = 0
        st.session_state["rounds"] = 0
        st.session_state["feedback"] = None
        st.session_state["waiting_next"] = False

    flash_order = st.session_state["flash_order"]
    flash_index = st.session_state["flash_index"]

    # ─── If we have shown all questions, display “Done” and return ────────────────────
    if flash_index >= total:
        st.success("🎉 All questions for today have been answered!")
        return

    # ─── Display rounds count ────────────────────────────────────────────────────────
    st.subheader(f"Flashcard Attempts This Session: {st.session_state['rounds']}")

    # ─── If there’s feedback from a previous submission, show it above ─────────────────
    if st.session_state.get("feedback"):
        st.write(st.session_state["feedback"])
        st.write("---")

    # ─── Fetch the current question’s dictionary by ID ───────────────────────────────
    current_qid = flash_order[flash_index]
    card = next(c for c in today_cards if c["id"] == current_qid)

    # ─── Display the question text and instruction ───────────────────────────────────
    st.markdown(f"**Q{current_qid}: {card['question']}**")
    st.markdown(f"*{card['instruction']}*")

    # ─── If we’re waiting for the user to click “Next Question,” show only that button ──
    if st.session_state["waiting_next"]:
        if st.button("Next Question"):
            # Advance to next question:
            st.session_state["flash_index"] += 1
            st.session_state["rounds"] += 1
            st.session_state["feedback"] = None
            st.session_state["waiting_next"] = False
        # Show progress of how many remain:
        remaining = total - st.session_state["flash_index"]
        st.write(f"Remaining unanswered today: **{remaining}/{total}**")
        return

    # ─── Otherwise, show checkboxes + “Submit Answer” button ─────────────────────────
    selected = []
    for letter, text in card["options"].items():
        if st.checkbox(f"{letter}. {text}", key=f"flash_{current_qid}_{letter}"):
            selected.append(letter)

    if st.button("Submit Answer"):
        if not selected:
            st.warning("⚠️ Please select at least one option before submitting.")
        else:
            correct_set = set(card["answers"])
            chosen_set = set(selected)

            if chosen_set == correct_set:
                feedback_msg = f"✅ Correct! (Answer: {', '.join(sorted(correct_set))})"
                is_correct = True
            else:
                feedback_msg = f"❌ Wrong. Correct answer(s): {', '.join(sorted(correct_set))}"
                is_correct = False

            # Record attempt (updates user_progress.json and mistakes if wrong)
            record_attempt(current_qid, is_correct)

            # Store that feedback and switch to waiting_next mode
            st.session_state["feedback"] = feedback_msg
            st.session_state["waiting_next"] = True

    # ─── Show how many remain (questions not yet answered in this session) ─────────────
    # Because record_attempt already marked as answered, we can re-calc:
    prog_after = load_progress()
    answered_after = prog_after.get("answered", {})
    unanswered_left = [
        q for q in flash_order[flash_index:]
        if str(q) not in answered_after
    ]
    st.write(f"Remaining unanswered today: **{len(unanswered_left)}/{total}**")

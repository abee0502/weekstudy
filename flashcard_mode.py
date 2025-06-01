import streamlit as st
import random
import os

from loaders import load_flashcards, load_progress
from session import get_today_batch
from flashcard_storage import (
    load_answered_ids,
    save_answered_ids,
    load_wrong_answers,
    save_wrong_answers
)

def run_flashcard_mode():
    """
    Flashcard Mode (history + progress) for today’s 40 questions:
      1. Load “day” from user_progress.json; slice out 40 from flashcards.json.
      2. Maintain:
         - st.session_state.answered_ids  (set of indices within today's slice already answered)
         - st.session_state.question_order (a shuffled list of indices 0..(len(today)-1))
         - st.session_state.history       (a list of indices in the order the user has moved)
         - st.session_state.history_pos   (the pointer into history)
         - st.session_state.has_submitted (whether the current question has just been submitted)
      3. On first run (or after a Reset), initialize all the session_state fields.
      4. Display the current question (based on history[history_pos]), show checkboxes,
         and a “Submit Answer” button. If the user hasn't submitted yet, Next/Previous are disabled.
      5. When Submit is clicked with at least one checkbox:
         - Compare selected vs. correct. Show ✅/🟡/❌ + correct answer(s).
         - Increment mistake count for that question if wrong.
         - Add that index to answered_ids, write to disk.
         - Set has_submitted = True so that Next/Previous buttons become enabled.
      6. Next ➡️ only works if has_submitted is True. When Next is clicked:
         - Build the list of still‐unanswered indices of today’s slice.
         - Pick the first one in question_order that’s not in answered_ids, or any from unanswered if history_pos is at the end.
         - Append that new index to history, increment history_pos, set has_submitted = False.
      7. Previous ⬅️ simply moves history_pos -= 1 (if > 0) and sets has_submitted = False.
      8. Progress bar shows (history_pos+1)/len(question_order).  Question “{history_pos+1} of {len(question_order)}”.
      9. A Reset button clears everything (answered_ids file + session_state).  
    """

    # ─── Load all flashcards + current day from user_progress.json ───────────────────
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    # ─── Get exactly 40 (or fewer if last day) cards for this day ────────────────────
    today_cards = get_today_batch(all_flashcards, day)
    total = len(today_cards)  # typically 40 except final day

    st.header(f"Day {day} Flashcard Mode ({total} questions)")

    # ─── Initialize session_state once ───────────────────────────────────────────────
    if "answered_ids" not in st.session_state:
        st.session_state.answered_ids = load_answered_ids()

    if "question_order" not in st.session_state:
        # Create a list of indices [0 .. total-1], then shuffle
        st.session_state.question_order = list(range(total))
        random.shuffle(st.session_state.question_order)

    if "history" not in st.session_state or not st.session_state.history:
        # Pick the first unanswered index in question_order
        unanswered = [i for i in st.session_state.question_order
                      if i not in st.session_state.answered_ids]
        if not unanswered:
            # If all answered, we’ll reset below
            st.session_state.history = []
            st.session_state.history_pos = 0
        else:
            first_idx = unanswered[0]
            st.session_state.history = [first_idx]
            st.session_state.history_pos = 0

    if "has_submitted" not in st.session_state:
        st.session_state.has_submitted = False

    # ─── If everything is answered, show a “done” message and reset ──────────────────
    unanswered_ids = [i for i in st.session_state.question_order
                      if i not in st.session_state.answered_ids]
    if not unanswered_ids and st.session_state.answered_ids:
        st.success("🎉 You've answered all questions for today! Resetting for a new session.")
        # Clear the local JSON file and session_state so they can start again
        st.session_state.answered_ids = set()
        save_answered_ids(st.session_state.answered_ids)
        st.session_state.history = []
        st.session_state.history_pos = 0
        st.session_state.has_submitted = False
        st.stop()

    # ─── Determine which question index we’re currently on ───────────────────────────
    if st.session_state.history:
        idx = st.session_state.history[st.session_state.history_pos]
    else:
        # In case history is empty, pick a new first unanswered
        if unanswered_ids:
            idx = unanswered_ids[0]
            st.session_state.history = [idx]
            st.session_state.history_pos = 0
        else:
            # Should never really get here, but just in case
            st.success("🎉 All questions are done for today.")
            st.stop()

    card = today_cards[idx]  # This is a dict with keys "question", "instruction", "options", "answers"

    # ─── DISPLAY QUESTION NUMBER & PROGRESS BAR ─────────────────────────────────────
    question_number = st.session_state.history_pos + 1
    st.subheader(f"Question {question_number} of {total}")
    st.progress(question_number / total)

    # ─── SHOW QUESTION TEXT & INSTRUCTION ────────────────────────────────────────────
    st.write(card["question"])
    st.markdown(f"**{card.get('instruction', '')}**")

    # ─── RENDER CHECKBOXES ──────────────────────────────────────────────────────────
    selected = []
    for key, val in card["options"].items():
        # If this checkbox was previously checked (session_state), it stays checked
        if st.session_state.get(f"flash_{idx}_{key}", False):
            selected.append(key)
        st.checkbox(f"{key}. {val}", key=f"flash_{idx}_{key}")

    # ─── SUBMIT LOGIC ────────────────────────────────────────────────────────────────
    # We disable Submit if already submitted (has_submitted==True), so only show Submit if False
    if not st.session_state.has_submitted:
        if st.button("Submit Answer"):

            if not selected:
                st.warning("⚠️ Please select at least one option before submitting.")
            else:
                # Evaluate correctness (strict equality only)
                correct_set = set(card["answers"])
                chosen_set = set(selected)

                if chosen_set == correct_set:
                    st.success("✅ Correct!")
                elif chosen_set & correct_set:
                    st.warning(f"🟡 Partially correct. Correct answer(s): {', '.join(correct_set)}")
                else:
                    st.error(f"❌ Incorrect. Correct answer(s): {', '.join(correct_set)}")

                # Track wrong counts
                wrong_counts = load_wrong_answers()
                if chosen_set != correct_set:
                    wrong_counts[str(idx)] = wrong_counts.get(str(idx), 0) + 1
                save_wrong_answers(wrong_counts)

                # Mark this question as answered and persist
                st.session_state.answered_ids.add(idx)
                save_answered_ids(st.session_state.answered_ids)

                # Lock this question so Submit disappears and Next becomes available
                st.session_state.has_submitted = True

    # ─── NAVIGATION BUTTONS ─────────────────────────────────────────────────────────
    col_prev, col_next = st.columns(2)

    with col_prev:
        if st.button("⬅️ Previous"):
            if st.session_state.history_pos > 0:
                st.session_state.history_pos -= 1
                st.session_state.has_submitted = False
                # Clear any previous feedback on UI (optional; handled automatically)

    with col_next:
        if st.button("Next ➡️"):
            if st.session_state.has_submitted:
                # User must have clicked Submit first
                # Find the next unanswered question in question_order
                unanswered_ids = [i for i in st.session_state.question_order
                                  if i not in st.session_state.answered_ids]
                remaining = [i for i in unanswered_ids if i != idx]

                if remaining:
                    next_idx = remaining[0]
                    # Trim forward history (if user had gone back)
                    st.session_state.history = st.session_state.history[:st.session_state.history_pos + 1]
                    # Append the next question
                    st.session_state.history.append(next_idx)
                    st.session_state.history_pos += 1
                    st.session_state.has_submitted = False
                else:
                    # No more unanswered remain (but should have been caught above)
                    st.success("🎉 All questions for today have been answered!")
            else:
                st.warning("⚠️ Please submit your answer before moving to the next question.")

    # ─── RESET PROGRESS BUTTON ──────────────────────────────────────────────────────
    st.write("")  # small spacer
    if st.button("🔁 Reset Practice Progress"):
        # Clear in‐memory state and delete the JSON file
        st.session_state.answered_ids = set()
        st.session_state.history = []
        st.session_state.history_pos = 0
        st.session_state.has_submitted = False
        if os.path.exists("answered_questions.json"):
            os.remove("answered_questions.json")
        st.success("✅ Practice progress has been reset for Flashcard Mode.")
        st.stop()

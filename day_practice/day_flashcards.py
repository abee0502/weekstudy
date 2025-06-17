import streamlit as st
import random
from utils.utils import save_json, load_json

DATA_DIR = "day_practice/data/"
PROGRESS_FILE = DATA_DIR + "day_progress.json"
ANSWERED_FILE = DATA_DIR + "day_answered_ids.json"
MISTAKES_FILE = DATA_DIR + "day_mistakes.json"
ORDER_FILE = DATA_DIR + "day_flashcard_state.json"

def run_flashcard_mode(questions, day):
    total = len(questions)
    today_key = f"day{day}"

    # ─── Load progress, answered questions, and mistakes ─────────────────
    answered_data = load_json(ANSWERED_FILE, {})
    answered_ids = answered_data.get(today_key, [])

    progress_data = load_json(PROGRESS_FILE, {})
    completed_rounds = progress_data.get(today_key, 0)

    flashcard_state = load_json(ORDER_FILE, {})
    saved_state = flashcard_state.get(today_key, {})
    if "flashcard_order" not in st.session_state or "flashcard_index" not in st.session_state:
        if saved_state:
            st.session_state.flashcard_order = saved_state["order"]
            st.session_state.flashcard_index = saved_state["index"]
        else:
            st.session_state.flashcard_order = list(range(total))
            random.shuffle(st.session_state.flashcard_order)
            st.session_state.flashcard_index = 0

        st.session_state.flashcard_submitted = False
        st.session_state.selected_options = set()
        st.session_state.round_completed = False
        st.session_state.round_correct_count = 0  # <-- Only for current round

    # ─── Current question setup ──────────────────────────────────────────
    if st.session_state.flashcard_index >= len(st.session_state.flashcard_order):
        # Update completed rounds and reset for next round
        if not st.session_state.get("round_completed", False):
            progress_data[today_key] = completed_rounds + 1
            save_json(PROGRESS_FILE, progress_data)
            st.session_state.round_completed = True

        # Show accuracy for this round only
        accuracy = 0
        if total > 0:
            accuracy = (st.session_state.round_correct_count / total) * 100
        st.success("🎉 You've completed all questions for this round.")
        st.info(f"Your accuracy: **{accuracy:.1f}%** ({st.session_state.round_correct_count} out of {total} correct)")

        # Reset correct count for next round
        if st.button("Start New Round"):
            st.session_state.flashcard_order = list(range(total))
            random.shuffle(st.session_state.flashcard_order)
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_submitted = False
            st.session_state.selected_options = set()
            st.session_state.round_correct_count = 0  # <-- Reset for new round
            st.session_state.round_completed = False

            # Reset answered_ids for progress bar
            answered_data[today_key] = []
            save_json(ANSWERED_FILE, answered_data)

            st.rerun()
        return

    idx = st.session_state.flashcard_order[st.session_state.flashcard_index]
    q = questions[idx]

    st.markdown(f"**Question {st.session_state.flashcard_index + 1} / {total}**")
    st.markdown(q["instruction"])
    st.markdown(q["question"])

    # ─── Render Checkboxes ───────────────────────────────────────────────
    selected_keys = []
    for key, text in q["options"].items():
        if st.checkbox(f"{key}: {text}", key=f"opt_{key}"):
            selected_keys.append(key)

    # ─── Submit Logic ────────────────────────────────────────────────────
    if st.button("Submit"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            correct = set(q["answers"])
            selected = set(selected_keys)

            if selected == correct:
                st.success("✅ Correct!")
                st.session_state.round_correct_count += 1
            else:
                st.error("❌ Incorrect.")
                sorted_answers = sorted(correct)  # Sort only for display
                st.markdown(f"**Correct answers are:** {', '.join(sorted_answers)}")

                # Log mistake
                mistakes = load_json(MISTAKES_FILE, {})
                question_key = f"{today_key}_q{idx}"
                mistakes[question_key] = mistakes.get(question_key, 0) + 1
                save_json(MISTAKES_FILE, mistakes)

            # Save progress
            if idx not in answered_ids:
                answered_ids.append(idx)
                answered_data[today_key] = answered_ids
                save_json(ANSWERED_FILE, answered_data)

            st.session_state.flashcard_submitted = True

    # ─── Next Logic ──────────────────────────────────────────────────────
    if st.button("Next"):
        if not st.session_state.flashcard_submitted:
            st.warning("⚠️ Please submit your answer before going to the next question.")
        else:
            # Clear checkboxes
            for k in q["options"].keys():
                st.session_state.pop(f"opt_{k}", None)

            st.session_state.flashcard_index += 1
            st.session_state.flashcard_submitted = False

            # Save progress to state file
            flashcard_state[today_key] = {
                "order": st.session_state.flashcard_order,
                "index": st.session_state.flashcard_index
            }
            save_json(ORDER_FILE, flashcard_state)

            st.rerun()

    # ─── Progress Bar and Info ───────────────────────────────────────────
    if total > 0:
        st.progress(min(len(answered_ids) / total, 1.0))
        st.caption(f"Progress: {len(answered_ids)} / {total}")
    else:
        st.warning("⚠️ No questions found for this day.")

    st.caption(f"Completed rounds today: {progress_data.get(today_key, 0)}")

    # ─── Reset Day Button ────────────────────────────────────────────────
    if st.button("🔄 Reset Today"):
        answered_data[today_key] = []
        save_json(ANSWERED_FILE, answered_data)

        progress_data[today_key] = 0
        save_json(PROGRESS_FILE, progress_data)

        flashcard_state.pop(today_key, None)
        save_json(ORDER_FILE, flashcard_state)

        # Clear session state
        for k in list(st.session_state.keys()):
            if k.startswith("opt_") or k in [
                "flashcard_index", "flashcard_order", "flashcard_submitted",
                "correct_count", "round_completed"
            ]:
                del st.session_state[k]

        st.success("✅ Progress for today has been reset.")
        st.rerun()
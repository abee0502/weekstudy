import streamlit as st
import random
from utils import save_json, load_json

PROGRESS_FILE = "progress.json"
ANSWERED_FILE = "answered_ids.json"
MISTAKES_FILE = "mistakes.json"

def run_flashcard_mode(questions, day):
    total = len(questions)
    today_key = f"day{day}"

    # ─── Load answered IDs and progress count ─────────────────────────────
    answered_data = load_json(ANSWERED_FILE, {})
    answered_ids = answered_data.get(today_key, [])

    progress_data = load_json(PROGRESS_FILE, {})
    completed_rounds = progress_data.get(today_key, 0)

    # ─── Session Initialization ───────────────────────────────────────────
    if "flashcard_index" not in st.session_state:
        unanswered = [i for i in range(total) if i not in answered_ids]
        if not unanswered:
            # Completed round
            completed_rounds += 1
            progress_data[today_key] = completed_rounds
            save_json(PROGRESS_FILE, progress_data)

            # Reset answers
            answered_ids = []
            answered_data[today_key] = []
            save_json(ANSWERED_FILE, answered_data)

            unanswered = list(range(total))  # restart question pool

            completed_rounds += 1
            progress_data[today_key] = completed_rounds
            save_json(PROGRESS_FILE, progress_data)

        random.shuffle(unanswered)
        st.session_state.flashcard_order = unanswered
        st.session_state.flashcard_index = len(answered_ids)
        st.session_state.flashcard_submitted = False
        st.session_state.selected_options = set()

    idx = st.session_state.flashcard_order[st.session_state.flashcard_index]
    q = questions[idx]

    st.markdown(f"**Question {st.session_state.flashcard_index + 1} / {total}**")
    st.info(q["instruction"])
    st.markdown(q["question"])

    # ─── Render Checkboxes for Options ────────────────────────────────────
    selected_keys = []
    for key, text in q["options"].items():
        checked = st.checkbox(f"{key}: {text}", key=f"opt_{key}")
        if checked:
            selected_keys.append(key)

    # ─── Submit Logic ─────────────────────────────────────────────────────
    if st.button("Submit"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            correct = set(q["answers"])
            selected = set(selected_keys)

            if selected == correct:
                st.success("✅ Correct!")
            else:
                st.error("❌ Incorrect.")
                correct_answers = ", ".join(correct)
                st.markdown(f"**Correct answers are:** {correct_answers}")

                # Log mistake
                mistakes = load_json(MISTAKES_FILE, {})
                question_key = f"{today_key}_q{idx}"
                mistakes[question_key] = mistakes.get(question_key, 0) + 1
                save_json(MISTAKES_FILE, mistakes)

            # Save answer
            answered_ids.append(idx)
            answered_data[today_key] = answered_ids
            save_json(ANSWERED_FILE, answered_data)

            # Mark as submitted
            st.session_state.flashcard_submitted = True

    # ─── Next Logic ───────────────────────────────────────────────────────
    if st.button("Next"):
        if not st.session_state.flashcard_submitted:
            st.warning("⚠️ Please submit your answer before going to the next question.")
        else:
            # Clear checkboxes
            for k in q["options"].keys():
                st.session_state.pop(f"opt_{k}", None)

            st.session_state.flashcard_index += 1
            st.session_state.flashcard_submitted = False

            if st.session_state.flashcard_index >= len(st.session_state.flashcard_order):
                st.success("🎉 You've completed all questions for this round.")
                del st.session_state.flashcard_index
                del st.session_state.flashcard_order
                return

            st.rerun()
    # ─── Progress + Rounds Info ───────────────────────────────────────────
    if total > 0:
        progress_ratio = min(len(answered_ids) / total, 1.0)
        st.progress(progress_ratio)
        st.caption(f"Progress: {len(answered_ids)} / {total}")
    else:
        st.warning("⚠️ No questions found for this day. Please check your questions.json file.")

    st.caption(f"Completed rounds today: {completed_rounds}")

    # ─── Reset Day Button ─────────────────────────────────────────────────────
    if st.button("🔄 Reset Today"):
        # Reset memory for the day
        answered_data[today_key] = []
        save_json(ANSWERED_FILE, answered_data)

        progress_data[today_key] = 0
        save_json(PROGRESS_FILE, progress_data)

        # Clear session state
        keys_to_clear = [k for k in st.session_state if k.startswith("opt_")]
        for k in keys_to_clear:
            del st.session_state[k]
        for k in ["flashcard_index", "flashcard_order", "flashcard_submitted"]:
            if k in st.session_state:
                del st.session_state[k]

        st.success("✅ Progress for today has been reset.")
        st.rerun()

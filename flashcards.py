import streamlit as st
import random
from utils import save_json, load_json

PROGRESS_FILE = "progress.json"
ANSWERED_FILE = "answered_ids.json"
MISTAKES_FILE = "mistakes.json"
ORDER_FILE = "flashcard_state.json"

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

    # ─── Initialize session state ────────────────────────────────────────
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

    # ─── Current question setup ──────────────────────────────────────────
    '''
    if st.session_state.flashcard_index >= len(st.session_state.flashcard_order):
        st.success("🎉 You've completed all questions for this round.")
        del st.session_state.flashcard_index
        del st.session_state.flashcard_order
        return
    '''
    if st.session_state.flashcard_index >= len(st.session_state.flashcard_order):
        total_questions = len(st.session_state.flashcard_order)
        correct_count = total_questions
    # Optional: read from answered_ids to validate score if partial allowed
        score_percentage = (correct_count / total_questions) * 100

        st.success(f"🎉 You've completed all questions for this round.")
        st.info(f"Your score: {score_percentage:.0f}%")

    # Clear session state but allow new round trigger
        if st.button("🔄 Start a New Round"):
            from utils import save_json, load_json

            today_key = f"day{day}"
            answered_data = load_json(ANSWERED_FILE, {})
            answered_data[today_key] = []
            save_json(ANSWERED_FILE, answered_data)
    
            # Remove round order to reshuffle
            flashcard_state = load_json("flashcard_state.json")
            flashcard_state.pop(today_key, None)
            save_json("flashcard_state.json", flashcard_state)
    
            # Clear session
            for k in ["flashcard_index", "flashcard_order", "flashcard_submitted"]:
                st.session_state.pop(k, None)

            st.rerun()
        

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
            else:
                st.error("❌ Incorrect.")
                st.markdown(f"**Correct answers are:** {', '.join(correct)}")

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

    st.caption(f"Completed rounds today: {completed_rounds}")

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
            if k.startswith("opt_") or k in ["flashcard_index", "flashcard_order", "flashcard_submitted"]:
                del st.session_state[k]

        st.success("✅ Progress for today has been reset.")
        st.rerun()

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
            # Restore correct_count if it was saved; otherwise start at 0
            st.session_state.correct_count = saved_state.get("correct_count", 0)
        else:
            st.session_state.flashcard_order = list(range(total))
            random.shuffle(st.session_state.flashcard_order)
            st.session_state.flashcard_index = 0
            st.session_state.correct_count = 0

        st.session_state.flashcard_submitted = False

    # ─── If all questions are done, show completion + percentage ───────────
    if st.session_state.flashcard_index >= len(st.session_state.flashcard_order):
        # Increment completed_rounds for today
        progress_data[today_key] = completed_rounds + 1
        save_json(PROGRESS_FILE, progress_data)

        correct_count = st.session_state.correct_count
        percent = round((correct_count / total) * 100, 1) if total > 0 else 0.0

        st.success(f"🎉 You've completed round #{completed_rounds + 1} today!")
        st.info(f"✅ Correct: {correct_count} / {total} → {percent}%")

        # Button to start another shuffled round
        if st.button("🔁 Start Next Round"):
            # Clear answered IDs for today
            answered_data[today_key] = []
            save_json(ANSWERED_FILE, answered_data)

            # Reset flashcard_state so next run shuffles afresh
            if today_key in flashcard_state:
                del flashcard_state[today_key]
            save_json(ORDER_FILE, flashcard_state)

            # Optionally, clear mistakes for today (comment out if you want to keep them)
            mistakes_data = load_json(MISTAKES_FILE, {})
            for qid in list(mistakes_data.keys()):
                if qid.startswith(today_key):
                    del mistakes_data[qid]
            save_json(MISTAKES_FILE, mistakes_data)

            # Clear session state related to flashcards
            for k in ["flashcard_index", "flashcard_order", "flashcard_submitted", "correct_count"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.experimental_rerun()

        return

    # ─── Current question setup ──────────────────────────────────────────
    idx = st.session_state.flashcard_order[st.session_state.flashcard_index]
    q = questions[idx]

    st.markdown(f"**Question {st.session_state.flashcard_index + 1} / {total}**")
    st.markdown(q["instruction"])
    st.markdown(q["question"])

    # ─── Render Checkboxes ───────────────────────────────────────────────
    selected_keys = []
    for key, text in q["options"].items():
        checkbox_key = f"{today_key}_q{idx}_opt_{key}"
        if st.checkbox(f"{key}: {text}", key=checkbox_key):
            selected_keys.append(key)

    # ─── Submit Logic ────────────────────────────────────────────────────
    if st.button("Submit"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            if not st.session_state.flashcard_submitted:
                correct = set(q["answers"])
                selected = set(selected_keys)

                if selected == correct:
                    st.success("✅ Correct!")
                    st.session_state.correct_count += 1
                else:
                    st.error("❌ Incorrect.")
                    st.markdown(f"**Correct answers are:** {', '.join(correct)}")

                    # Log mistake
                    mistakes = load_json(MISTAKES_FILE, {})
                    question_key = f"{today_key}_q{idx}"
                    mistakes[question_key] = mistakes.get(question_key, 0) + 1
                    save_json(MISTAKES_FILE, mistakes)

                # Save progress (only first-time for this question)
                if idx not in answered_ids:
                    answered_ids.append(idx)
                    answered_data[today_key] = answered_ids
                    save_json(ANSWERED_FILE, answered_data)

                # Save correct_count + order + index so we can resume if needed
                flashcard_state[today_key] = {
                    "order": st.session_state.flashcard_order,
                    "index": st.session_state.flashcard_index,
                    "correct_count": st.session_state.correct_count
                }
                save_json(ORDER_FILE, flashcard_state)

                st.session_state.flashcard_submitted = True
            else:
                st.info("⚠️ You've already submitted this question. Click Next to continue.")

    # ─── Next Logic ──────────────────────────────────────────────────────
    if st.button("Next"):
        if not st.session_state.flashcard_submitted:
            st.warning("⚠️ Please submit your answer before going to the next question.")
        else:
            # Clear checkboxes for this question
            for k in q["options"].keys():
                skey = f"{today_key}_q{idx}_opt_{k}"
                if skey in st.session_state:
                    del st.session_state[skey]

            st.session_state.flashcard_index += 1
            st.session_state.flashcard_submitted = False

            # Save updated state
            flashcard_state[today_key] = {
                "order": st.session_state.flashcard_order,
                "index": st.session_state.flashcard_index,
                "correct_count": st.session_state.correct_count
            }
            save_json(ORDER_FILE, flashcard_state)

            st.experimental_rerun()

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

        if today_key in flashcard_state:
            del flashcard_state[today_key]
        save_json(ORDER_FILE, flashcard_state)

        # Optionally clear mistakes for the day
        mistakes_data = load_json(MISTAKES_FILE, {})
        for qid in list(mistakes_data.keys()):
            if qid.startswith(today_key):
                del mistakes_data[qid]
        save_json(MISTAKES_FILE, mistakes_data)

        for k in list(st.session_state.keys()):
            if k.startswith(f"{today_key}_q") or k in ["flashcard_index", "flashcard_order", "flashcard_submitted", "correct_count"]:
                del st.session_state[k]

        st.success("✅ Progress for today has been reset.")
        st.experimental_rerun()

import streamlit as st
import random
from utils.utils import load_json, save_json

DATA_DIR = "bulk_practice/data/"
PROGRESS_FILE = DATA_DIR + "bulk_progress.json"
ANSWERED_FILE = DATA_DIR + "bulk_answered_ids.json"
ORDER_FILE = DATA_DIR + "bulk_flashcard_state.json"
MISTAKES_FILE = DATA_DIR + "bulk_mistakes.json" # Modified this line

def run_bulk_practice_mode(all_questions, days):
    st.header("Bulk Practice Mode")

    # Step 1: Select days and start
    if "bulk_started" not in st.session_state or not st.session_state.bulk_started:
        selected_days = st.multiselect("Select days to practice", list(range(1, 8)), default=days or [1])
        if st.button("Start"):
            if not selected_days:
                st.warning("Please select at least one day.")
                return
            st.session_state.bulk_days = selected_days
            st.session_state.bulk_started = True
            # Reset all session state for a new run
            for k in list(st.session_state.keys()):
                if k.startswith("bulk_"):
                    del st.session_state[k]
            st.session_state.bulk_days = selected_days
            st.session_state.bulk_started = True
            st.rerun()
        return

    # Step 2: Prepare questions for selected days
    days = st.session_state.get("bulk_days", [])
    selected_questions = []
    question_map = []
    for day in days:
        start = (day - 1) * 40
        end = day * 40
        day_questions = all_questions[start:end]
        for idx, q in enumerate(day_questions):
            selected_questions.append(q)
            question_map.append((day, idx))
    total = len(selected_questions)
    session_key = "_".join(map(str, sorted(days)))
    today_key = f"bulk_{session_key}"

    # Initialize or restore order/index
    if "bulk_order" not in st.session_state or "bulk_index" not in st.session_state:
        st.session_state.bulk_order = list(range(total))
        random.shuffle(st.session_state.bulk_order)
        st.session_state.bulk_index = 0
        st.session_state.bulk_submitted = False
        st.session_state.bulk_correct_count = 0
        st.session_state.bulk_completed = False

    # Shuffle button
    if st.button("Shuffle"):
        random.shuffle(st.session_state.bulk_order)
        st.session_state.bulk_index = 0
        st.session_state.bulk_submitted = False
        st.session_state.bulk_correct_count = 0
        st.session_state.bulk_completed = False
        for k in list(st.session_state.keys()):
            if k.startswith("bulk_opt_"):
                del st.session_state[k]
        st.rerun()

    # Start Again button
    if st.button("Start Again"):
        for k in list(st.session_state.keys()):
            if k.startswith("bulk_"):
                del st.session_state[k]
        st.session_state.bulk_started = False
        st.rerun()

    # End of round
    if st.session_state.bulk_index >= len(st.session_state.bulk_order):
        st.session_state.bulk_completed = True
        accuracy = (st.session_state.bulk_correct_count / total) * 100 if total > 0 else 0
        st.success("🎉 You've completed all questions for this round.")
        st.info(f"Your accuracy: **{accuracy:.1f}%** ({st.session_state.bulk_correct_count} out of {total} correct)")
        return

    idx = st.session_state.bulk_order[st.session_state.bulk_index]
    q = selected_questions[idx]
    day, orig_idx = question_map[idx]

    st.markdown(f"**Day {day} — Question {st.session_state.bulk_index + 1} / {total}**")
    st.markdown(q.get("instruction", ""))
    st.markdown(q.get("question", ""))

    selected_keys = []
    for key, text in q.get("options", {}).items():
        if st.checkbox(f"{key}: {text}", key=f"bulk_opt_{key}_{idx}"):
            selected_keys.append(key)

    if st.button("Submit", key=f"bulk_submit_{idx}"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            correct = set(q.get("answers", []))  # Remove sorting here
            selected = set(selected_keys)
            
            if selected == correct:
                st.success("✅ Correct!")
                st.session_state.bulk_correct_count += 1
            else:
                st.error("❌ Incorrect.")
                sorted_answers = sorted(correct)  # Sort only for display
                st.markdown(f"**Correct answers are:** {', '.join(sorted_answers)}")
                # Log mistake
                mistakes = load_json(MISTAKES_FILE, {})
                question_key = f"day{day}_q{orig_idx}"
                mistakes[question_key] = mistakes.get(question_key, 0) + 1
                save_json(MISTAKES_FILE, mistakes)
            st.session_state.bulk_submitted = True

    if st.button("Next", key=f"bulk_next_{idx}"):
        if not st.session_state.bulk_submitted:
            st.warning("⚠️ Please submit your answer before going to the next question.")
        else:
            for k in q.get("options", {}).keys():
                st.session_state.pop(f"bulk_opt_{k}_{idx}", None)
            st.session_state.bulk_index += 1
            st.session_state.bulk_submitted = False
            st.rerun()

    st.progress((st.session_state.bulk_index + 1) / total)
    st.caption(f"Progress: {st.session_state.bulk_index + 1} / {total}")
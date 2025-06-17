import streamlit as st
import random
from utils.utils import load_json, load_questions, get_day_questions

DATA_DIR = "day_practice/data/"
MISTAKES_FILE = DATA_DIR + "day_mistakes.json"

def run_mistake_practice_mode(day):
    st.title(f"🔁 Mistake Practice – Day {day}")

    # ─── 1) Load all mistakes and filter for today ────────────────────────
    mistake_data = load_json(MISTAKES_FILE, {})
    day_prefix = f"day{day}_q"
    filtered = {k: v for k, v in mistake_data.items() if k.startswith(day_prefix)}

    if not filtered:
        st.success("🎉 No mistakes logged for this day! Nothing to practice.")
        return

    # ─── 2) Build a list of unique question indices you got wrong ───────
    q_indices = sorted({int(key.split("_q")[1]) for key in filtered.keys()})

    # ─── 3) Load all questions, then select just “day” questions ────────
    all_questions = load_questions("questions.json")
    day_questions = get_day_questions(all_questions, day)
    # Only include indices that are valid for day_questions
    valid_q_indices = [i for i in q_indices if 0 <= i < len(day_questions)]
    if len(valid_q_indices) < len(q_indices):
        st.warning("Some mistake entries refer to questions that do not exist for this day. They will be skipped.")
    practice_questions = [day_questions[i] for i in valid_q_indices]
    total = len(practice_questions)

    # ─── 4) Initialize session_state for mistake practice ─────────────
    if ("mistake_order" not in st.session_state
        or "mistake_index" not in st.session_state):
        
        order = list(range(total))
        random.shuffle(order)

        st.session_state.mistake_order = order
        st.session_state.mistake_index = 0
        st.session_state.mistake_correct = 0
        st.session_state.mistake_submitted = False

    # ─── 5) If we've practiced all mistaken cards, show results + Restart ─
    if st.session_state.mistake_index >= total:
        correct_count = st.session_state.mistake_correct
        accuracy_pct = (correct_count / total) * 100 if total > 0 else 0.0

        st.success(f"🎉 You've practiced all {total} mistaken question{'s' if total > 1 else ''}!")
        st.markdown(f"**Your practice accuracy:** {accuracy_pct:.1f}%")

        if st.button("🔁 Restart Mistake Practice"):
            new_order = list(range(total))
            random.shuffle(new_order)

            st.session_state.mistake_order = new_order
            st.session_state.mistake_index = 0
            st.session_state.mistake_correct = 0
            st.session_state.mistake_submitted = False

            # Clear checkbox keys from session_state
            for q in practice_questions:
                for opt_key in q["options"].keys():
                    st.session_state.pop(f"mistake_opt_{opt_key}", None)

            st.rerun()

        return

    # ─── 6) Otherwise, show the current mistaken question ───────────────
    curr_pos = st.session_state.mistake_index
    card_idx = st.session_state.mistake_order[curr_pos]
    q = practice_questions[card_idx]

    st.markdown(f"**Mistake {curr_pos + 1} / {total}**")
    st.markdown(q["instruction"])
    st.markdown(q["question"])

    # ─── 7) Render checkboxes for options ──────────────────────────────
    selected_keys = []
    for opt_letter, opt_text in q["options"].items():
        if st.checkbox(f"{opt_letter}: {opt_text}", key=f"mistake_opt_{opt_letter}"):
            selected_keys.append(opt_letter)

    # ─── 8) Submit logic for this card ─────────────────────────────────
    if st.button("Submit Mistake"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            correct_set = set(q["answers"])  # Remove sorting here
            selected_set = set(selected_keys)

            if selected_set == correct_set:
                st.success("✅ Correct!")
                st.session_state.mistake_correct += 1
            else:
                st.error("❌ Incorrect.")
                sorted_answers = sorted(correct_set)  # Sort only for display
                st.markdown(f"**Correct answers are:** {', '.join(sorted_answers)}")

                # Increment mistake count in mistakes.json
                # Find the mistake key for this question
                mistake_keys = [k for k in mistake_data.keys() if k.endswith(f"_q{q_indices[card_idx]}")]
                if mistake_keys:
                    key = mistake_keys[0]
                    mistake_data[key] = mistake_data.get(key, 0) + 1
                    from utils.utils import save_json
                    save_json(MISTAKES_FILE, mistake_data)

            st.session_state.mistake_submitted = True

    # ─── 9) Next‐Mistake logic ─────────────────────────────────────────
    if st.button("Next Mistake"):
        if not st.session_state.mistake_submitted:
            st.warning("⚠️ Please submit your answer before moving on.")
        else:
            # Clear checkboxes for this question
            for opt_letter in q["options"].keys():
                st.session_state.pop(f"mistake_opt_{opt_letter}", None)

            st.session_state.mistake_index += 1
            st.session_state.mistake_submitted = False
            st.rerun()

    # ─── 10) Progress indicator ───────────────────────────────────────
    st.caption(f"Progress: {curr_pos} / {total}")
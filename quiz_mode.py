import streamlit as st
from utils.utils import save_json, load_json

MISTAKES_FILE = "mistakes.json"

def run_quiz_mode(questions, day):
    st.title("🧠 Quiz Mode")

    total = len(questions)
    responses = {}
    submitted = st.session_state.get("quiz_submitted", False)

    # ─── Render Each Question ─────────────────────────────────────────────
    for idx, q in enumerate(questions):
        st.markdown(f"**Q{idx + 1}.** {q['question']}")
        st.info(q["instruction"])

        options_list = list(q["options"].values())
        selected = st.multiselect(f"Select answer(s) for Q{idx + 1}:", options_list, key=f"quiz_q_{idx}")

        rev_map = {v: k for k, v in q["options"].items()}
        selected_keys = [rev_map.get(s) for s in selected if s in rev_map]
        responses[idx] = selected_keys

        st.markdown("---")

    # ─── Submit Button ────────────────────────────────────────────────────
    if not submitted and st.button("Submit Quiz"):
        score = 0
        wrong_questions = {}

        for idx, q in enumerate(questions):
            correct = set(q["answers"])
            selected = set(responses.get(idx, []))
            if selected == correct:
                score += 1
            else:
                # Record mistake
                q_id = f"day{day}_q{idx}"
                wrong_questions[q_id] = wrong_questions.get(q_id, 0) + 1

        # Show score
        st.session_state.quiz_submitted = True
        st.session_state.quiz_wrong = wrong_questions  # Save for feedback
        st.session_state.quiz_score = score
        st.session_state.quiz_total = total
        # Do NOT rerun here

        # Save mistakes
        all_mistakes = load_json(MISTAKES_FILE, {})
        for key, count in wrong_questions.items():
            all_mistakes[key] = all_mistakes.get(key, 0) + count
        save_json(MISTAKES_FILE, all_mistakes)

        st.experimental_rerun()  # Optionally, rerun to show feedback

    # ─── Show Results and Feedback ────────────────────────────────────────
    if submitted:
        score = st.session_state.get("quiz_score", 0)
        total = st.session_state.get("quiz_total", len(questions))
        st.success(f"✅ Your Score: {score} / {total}")

        wrong_questions = st.session_state.get("quiz_wrong", {})
        if wrong_questions:
            st.markdown("### ❌ Questions you got wrong:")
            for idx, q in enumerate(questions):
                q_id = f"day{day}_q{idx}"
                if q_id in wrong_questions:
                    st.markdown(f"**Q{idx + 1}.** {q['question']}")
                    correct_answers = [q["options"][k] for k in q["answers"]]
                    st.info(f"Correct answer(s): {', '.join(correct_answers)}")
                    st.markdown("---")

        if st.button("Reset Quiz"):
            for idx in range(total):
                st.session_state.pop(f"quiz_q_{idx}", None)
            st.session_state.quiz_submitted = False
            st.session_state.quiz_wrong = {}
            st.session_state.quiz_score = 0
            st.session_state.quiz_total = 0
            st.experimental_rerun()
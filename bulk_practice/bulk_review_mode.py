import streamlit as st
from utils.utils import load_questions

def run_bulk_review_mode(all_questions, days):
    st.title("📘 Bulk Review Mode")

    selected_questions = []
    for day in days:
        start = (day - 1) * 40
        end = day * 40
        day_questions = all_questions[start:end]
        selected_questions.extend(day_questions)

    if not selected_questions:
        st.info("No questions selected for review. Please select days in Bulk Practice Mode.")
        return

    for idx, q in enumerate(selected_questions):
        st.markdown(f"**Q{idx + 1}.** {q['question']}")
        st.info(q["instruction"])

        # Show all options
        for key, text in q["options"].items():
            st.markdown(f"- {key}: {text}")

        # Show correct answers
        correct_keys = ", ".join(q["answers"])
        st.success("✅ Correct Answer(s): " + correct_keys)

        st.markdown("---")
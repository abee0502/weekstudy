import streamlit as st

def run_review_mode(questions, day):
    st.title(f"📘 Review Mode – Day {day}")

    for idx, q in enumerate(questions):
        st.markdown(f"**Q{idx + 1}.** {q['question']}")
        st.info(q["instruction"])

        # Show all options
        for key, text in q["options"].items():
            st.markdown(f"- {key}: {text}")

        # Show correct answers
        correct_text = [f"{k}: {v}" for k, v in q["options"].items() if k in q["answers"]]
        st.success("✅ Correct Answer(s): " + ", ".join(correct_text))

        st.markdown("---")

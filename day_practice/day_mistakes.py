import streamlit as st
from utils.utils import load_json

DATA_DIR = "day_practice/data/"
MISTAKES_FILE = DATA_DIR + "day_mistakes.json"

def run_mistake_review_mode(day):
    st.title(f"❌ Mistake Review – Day {day}")

    # Load all mistakes
    mistake_data = load_json(MISTAKES_FILE, {})

    # Filter for current day
    day_prefix = f"day{day}_q"
    filtered = {k: v for k, v in mistake_data.items() if k.startswith(day_prefix)}

    if not filtered:
        st.success("🎉 No mistakes for this day! Great job!")
        return

    # Load questions for today (needed to map back from qID)
    from utils.utils import load_questions, get_day_questions
    all_questions = load_questions("questions.json")
    day_questions = get_day_questions(all_questions, day)

    for key, count in filtered.items():
        q_index = int(key.split("_q")[1])
        q = day_questions[q_index]

        st.markdown(f"**Q{q_index + 1}.** {q['question']}")
        st.info(q["instruction"])

        for k, v in q["options"].items():
            st.markdown(f"- {k}: {v}")

        correct_keys = [k for k in q["answers"]]
        st.success("✅ Correct Answer(s): " + ", ".join(correct_keys))
        st.warning(f"❌ You answered this wrong {count} time(s).")

        st.markdown("---")
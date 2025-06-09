import streamlit as st
import sys
sys.path.append(".")
from utils.utils import load_json

DATA_DIR = "bulk_practice/data/"
BULK_MISTAKES_FILE = DATA_DIR + "bulk_mistakes.json"
QUESTIONS_FILE = "questions.json"

def show_all_bulk_mistakes(mistakes_file=BULK_MISTAKES_FILE, questions_file=QUESTIONS_FILE):
    st.header("All Bulk Practice Mistakes")
    mistakes = load_json(mistakes_file, {})
    all_questions = load_json(questions_file, [])

    if not mistakes:
        st.info("No bulk practice mistakes recorded yet.")
        return

    for key, count in mistakes.items():
        try:
            day, qidx = key.replace("day", "").split("_q")
            day = int(day)
            qidx = int(qidx)
            question_idx = (day - 1) * 40 + qidx
            q = all_questions[question_idx]

            st.markdown(f"**Day {day} Q{qidx+1}.** {q['question']}")
            st.info(q["instruction"])

            for k, v in q["options"].items():
                st.markdown(f"- {k}: {v}")

            correct_keys = [k for k in q["answers"]]
            st.success("✅ Correct Answer(s): " + ", ".join(correct_keys))
            st.warning(f"❌ You answered this wrong {count} time(s).")

            st.markdown("---")
        except Exception as e:
            st.error(f"Error processing question {key}: {e}")
            continue

def practice_bulk_mistakes(mistakes_file=BULK_MISTAKES_FILE, questions_file=QUESTIONS_FILE):
    st.header("Practice Bulk Mistakes")
    mistakes = load_json(mistakes_file, {})
    all_questions = load_json(questions_file, [])
    mistake_keys = list(mistakes.keys())
    
    if not mistake_keys:
        st.info("No bulk mistakes to practice!")
        return

    if "bulk_mistake_idx" not in st.session_state:
        st.session_state.bulk_mistake_idx = 0
        st.session_state.bulk_mistake_correct = 0
        st.session_state.bulk_mistake_submitted = False

    idx = st.session_state.bulk_mistake_idx
    total = len(mistake_keys)

    # Show completion message when finished
    if idx >= total:
        accuracy = (st.session_state.bulk_mistake_correct / total) * 100 if total > 0 else 0
        st.success(f"🎉 You've practiced all {total} mistaken questions!")
        st.markdown(f"**Your practice accuracy:** {accuracy:.1f}%")
        if st.button("🔁 Restart Practice"):
            st.session_state.bulk_mistake_idx = 0
            st.session_state.bulk_mistake_correct = 0
            st.session_state.bulk_mistake_submitted = False
            st.rerun()
        return

    key = mistake_keys[idx]
    try:
        day, qidx = key.replace("day", "").split("_q")
        day = int(day)
        qidx = int(qidx)
        question_idx = (day - 1) * 40 + qidx
        q = all_questions[question_idx]
    except Exception:
        st.session_state.bulk_mistake_idx += 1
        st.rerun()
        return

    # Display question info
    st.markdown(f"**Mistake {idx + 1} / {total}**")
    st.markdown(f"**Day {day} Q{qidx+1}** — Times missed: {mistakes[key]}")
    st.markdown(q.get("instruction", ""))
    st.markdown(q.get("question", ""))

    selected_keys = []
    for opt, text in q.get("options", {}).items():
        if st.checkbox(f"{opt}: {text}", key=f"bulk_mistake_opt_{opt}_{idx}"):
            selected_keys.append(opt)

    if st.button("Submit", key=f"bulk_mistake_submit_{idx}"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            correct = set(q.get("answers", []))
            selected = set(selected_keys)
            if selected == correct:
                st.success("✅ Correct!")
                st.session_state.bulk_mistake_correct += 1
            else:
                st.error("❌ Incorrect.")
                correct_texts = [f"{k}: {v}" for k, v in q["options"].items() if k in correct]
                st.markdown("**Correct Answer(s):** " + ", ".join(correct_texts))
                # Update mistake count
                mistakes[key] = mistakes.get(key, 0) + 1
                from utils.utils import save_json
                save_json(mistakes_file, mistakes)
            st.session_state.bulk_mistake_submitted = True

    if st.button("Next", key=f"bulk_mistake_next_{idx}"):
        if not st.session_state.bulk_mistake_submitted:
            st.warning("⚠️ Please submit your answer before moving on.")
        else:
            for opt in q.get("options", {}).keys():
                st.session_state.pop(f"bulk_mistake_opt_{opt}_{idx}", None)
            st.session_state.bulk_mistake_idx += 1
            st.session_state.bulk_mistake_submitted = False
            st.rerun()

    st.progress((idx + 1) / total)
    st.caption(f"Progress: {idx + 1} / {total}")
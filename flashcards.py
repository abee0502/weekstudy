import streamlit as st
import random
from utils import save_json, load_json

PROGRESS_FILE   = "progress.json"
ANSWERED_FILE   = "answered_ids.json"
MISTAKES_FILE   = "mistakes.json"
ORDER_FILE      = "flashcard_state.json"

def run_flashcard_mode(questions, day):
    total        = len(questions)
    today_key    = f"day{day}"

    # ─── Load progress, answered questions, and mistakes ────────────────
    answered_data    = load_json(ANSWERED_FILE, {})
    answered_ids     = answered_data.get(today_key, [])

    progress_data    = load_json(PROGRESS_FILE, {})
    completed_rounds = progress_data.get(today_key, 0)

    flashcard_state  = load_json(ORDER_FILE, {})
    saved_state      = flashcard_state.get(today_key, {})

    # ─── Initialize session_state on first run ──────────────────────────
    if "flashcard_order" not in st.session_state or "flashcard_index" not in st.session_state:
        if saved_state:
            st.session_state.flashcard_order  = saved_state["order"]
            st.session_state.flashcard_index  = saved_state["index"]
            st.session_state.correct_count    = saved_state.get("correct_count", 0)
        else:
            st.session_state.flashcard_order  = list(range(total))
            random.shuffle(st.session_state.flashcard_order)
            st.session_state.flashcard_index  = 0
            st.session_state.correct_count    = 0

        st.session_state.flashcard_submitted = False

    # ─── If we've finished all questions for this round ────────────────
    if st.session_state.flashcard_index >= total:
        # Compute accuracy
        accuracy = (
            (st.session_state.correct_count / total) * 100
            if total > 0 else
            0.0
        )

        st.success("🎉 You've completed all questions for this round.")
        st.info(
            f"Your score: {st.session_state.correct_count} / {total}  ({accuracy:.1f}%)"
        )

        # Increment “rounds completed” counter
        progress_data[today_key] = completed_rounds + 1
        save_json(PROGRESS_FILE, progress_data)

        # Offer a button to start a brand-new round of the same 40 questions
        if st.button("🔄 Start Another Round"):
            # 1) Clear answered_ids for today
            answered_data[today_key] = []
            save_json(ANSWERED_FILE, answered_data)

            # 2) Reset session_state: new random order, reset index & correct_count
            st.session_state.flashcard_order    = list(range(total))
            random.shuffle(st.session_state.flashcard_order)
            st.session_state.flashcard_index    = 0
            st.session_state.flashcard_submitted = False
            st.session_state.correct_count      = 0

            # 3) Overwrite flashcard_state.json on disk with the new values
            flashcard_state[today_key] = {
                "order":         st.session_state.flashcard_order,
                "index":         st.session_state.flashcard_index,
                "correct_count": st.session_state.correct_count
            }
            save_json(ORDER_FILE, flashcard_state)

            # As soon as we update session_state, we return so Streamlit will rerun
            return

        return  # nothing else to render after “round completed”

    # ─── Otherwise, show the current question ────────────────────────────
    idx = st.session_state.flashcard_order[st.session_state.flashcard_index]
    q   = questions[idx]

    st.markdown(f"**Question {st.session_state.flashcard_index + 1} / {total}**")
    st.markdown(q["instruction"])
    st.markdown(q["question"])

    # ─── Render Checkboxes for options ──────────────────────────────────
    selected_keys = []
    for key, text in q["options"].items():
        if st.checkbox(f"{key}: {text}", key=f"opt_{key}"):
            selected_keys.append(key)

    # ─── “Submit” Button Logic ──────────────────────────────────────────
    if st.button("Submit"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            correct = set(q["answers"])
            chosen  = set(selected_keys)

            if chosen == correct:
                st.success("✅ Correct!")
                st.session_state.correct_count += 1
            else:
                st.error("❌ Incorrect.")
                st.markdown(
                    f"**Correct answer(s):** {', '.join(sorted(correct))}"
                )

                # Log mistake
                mistakes     = load_json(MISTAKES_FILE, {})
                question_key = f"{today_key}_q{idx}"
                mistakes[question_key] = mistakes.get(question_key, 0) + 1
                save_json(MISTAKES_FILE, mistakes)

            # Mark this question as answered (only once)
            if idx not in answered_ids:
                answered_ids.append(idx)
                answered_data[today_key] = answered_ids
                save_json(ANSWERED_FILE, answered_data)

            st.session_state.flashcard_submitted = True

            # Save the updated correct_count / index / order back to disk
            flashcard_state[today_key] = {
                "order":         st.session_state.flashcard_order,
                "index":         st.session_state.flashcard_index,
                "correct_count": st.session_state.correct_count
            }
            save_json(ORDER_FILE, flashcard_state)

    # ─── “Next” Button Logic ────────────────────────────────────────────
    if st.button("Next"):
        if not st.session_state.flashcard_submitted:
            st.warning("⚠️ Please submit your answer before going to the next question.")
        else:
            # 1) Clear out the checkboxes so they don’t stay checked
            for k in q["options"].keys():
                st.session_state.pop(f"opt_{k}", None)

            # 2) Advance the index and reset “submitted” flag
            st.session_state.flashcard_index += 1
            st.session_state.flashcard_submitted = False

            # 3) Save updated index & correct_count to disk
            flashcard_state[today_key] = {
                "order":         st.session_state.flashcard_order,
                "index":         st.session_state.flashcard_index,
                "correct_count": st.session_state.correct_count
            }
            save_json(ORDER_FILE, flashcard_state)

            # 4) **Return immediately**, so Streamlit re-runs the script with the new index
            return

    # ─── Progress Bar & Info at the bottom ──────────────────────────────
    if total > 0:
        st.progress(min(len(answered_ids) / total, 1.0))
        st.caption(f"Progress: {len(answered_ids)} / {total}")
    else:
        st.warning("⚠️ No questions found for this day.")

    st.caption(f"Completed rounds today: {completed_rounds}")

    # ─── “Reset Today” Button ────────────────────────────────────────────
    if st.button("🔄 Reset Today"):
        # 1) Clear answered IDs
        answered_data[today_key] = []
        save_json(ANSWERED_FILE, answered_data)

        # 2) Reset completed‐rounds counter
        progress_data[today_key] = 0
        save_json(PROGRESS_FILE, progress_data)

        # 3) Remove any saved order/index for today
        flashcard_state.pop(today_key, None)
        save_json(ORDER_FILE, flashcard_state)

        # 4) Clear out all related session_state keys
        for k in list(st.session_state.keys()):
            if k.startswith("opt_") or k in ["flashcard_index", "flashcard_order", "flashcard_submitted", "correct_count"]:
                del st.session_state[k]

        st.success("✅ Progress for today has been reset.")
        return

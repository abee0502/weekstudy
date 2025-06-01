import streamlit as st
import random
from utils import save_json, load_json

PROGRESS_FILE    = "progress.json"
ANSWERED_FILE    = "answered_ids.json"
MISTAKES_FILE    = "mistakes.json"
ORDER_FILE       = "flashcard_state.json"

def run_flashcard_mode(questions, day):
    total = len(questions)
    today_key = f"day{day}"

    # ─── Load all persisted data once ─────────────────────────────────────────
    answered_data   = load_json(ANSWERED_FILE, {})
    mistakes_data   = load_json(MISTAKES_FILE, {})
    flashcard_state = load_json(ORDER_FILE, {})
    progress_data   = load_json(PROGRESS_FILE, {})

    # IDs of questions answered in this round
    answered_ids = answered_data.get(today_key, [])

    # How many completed rounds have already happened for today
    completed_rounds = progress_data.get(today_key, 0)

    # If no questions at all, bail out early:
    if total == 0:
        st.warning("⚠️ No questions found for this day.")
        return

    # ─── Initialize session_state for a new run if needed ────────────────────
    if "flashcard_order" not in st.session_state or "flashcard_index" not in st.session_state:
        # If there's a saved shuffle+index from earlier today, use it:
        saved_state = flashcard_state.get(today_key, {})
        if saved_state:
            st.session_state.flashcard_order = saved_state["order"]
            st.session_state.flashcard_index = saved_state["index"]
            # Also restore how many correct so far (if we saved it—see below)
            st.session_state.correct_count = saved_state.get("correct_count", 0)
        else:
            # First time this round: shuffle all questions
            order = list(range(total))
            random.shuffle(order)
            st.session_state.flashcard_order = order
            st.session_state.flashcard_index = 0
            st.session_state.correct_count = 0  # start counting fresh

        # A flag to prevent grading twice if they click “Submit” repeatedly
        st.session_state.flashcard_submitted = False

    # If we've completed this round:
    if st.session_state.flashcard_index >= total:
        # 1) Increment “completed_rounds” in PROGRESS_FILE:
        progress_data[today_key] = completed_rounds + 1
        save_json(PROGRESS_FILE, progress_data)

        # 2) Compute correct percentage
        correct_count = st.session_state.correct_count
        percent = round((correct_count / total) * 100, 1)  # e.g. 72.5%

        st.success(f"🎉 You've completed round #{completed_rounds + 1} today!")
        st.info(f"✅ Correct: {correct_count} / {total} → {percent}%")

        # 3) Offer a “Start Next Round” button
        if st.button("🔁 Start Next Round"):
            # — Clear answered-IDs for today
            answered_data[today_key] = []
            save_json(ANSWERED_FILE, answered_data)

            # — We do NOT reset progress_data[today_key], because that tracks total rounds
            #   but we DO reset flashcard_state (so next run will shuffle fresh)
            if today_key in flashcard_state:
                del flashcard_state[today_key]
            save_json(ORDER_FILE, flashcard_state)

            # — Clear mistakes for today’s questions (optional—feel free to keep them if you like).
            #    If you want to keep cumulative mistake counts across rounds, comment out the next two lines.
            for qid in list(mistakes_data.keys()):
                if qid.startswith(today_key):
                    del mistakes_data[qid]
            save_json(MISTAKES_FILE, mistakes_data)

            # — Clear session_state so that Streamlit re-initializes on the next run
            for k in ["flashcard_index", "flashcard_order", "flashcard_submitted", "correct_count"]:
                st.session_state.pop(k, None)

            st.experimental_rerun()

        return  # don’t render any more checkboxes—just the summary + “Start Next Round”

    # ─── Otherwise, we’re in the middle of a round ──────────────────────────
    idx = st.session_state.flashcard_order[st.session_state.flashcard_index]
    q   = questions[idx]

    st.markdown(f"**Question {st.session_state.flashcard_index + 1} / {total}**")
    st.markdown(q["instruction"])
    st.markdown(q["question"])

    # Render checkboxes (option keys are namespaced by question index to avoid collisions)
    selected_keys = []
    for key, text in q["options"].items():
        checkbox_key = f"{today_key}_q{idx}_opt_{key}"
        if st.checkbox(f"{key}: {text}", key=checkbox_key):
            selected_keys.append(key)

    # ─── Submit Logic ───────────────────────────────────────────────────────
    if st.button("Submit"):
        if not selected_keys:
            st.warning("⚠️ Please select at least one answer before submitting.")
        else:
            # Only grade the first time they submit this card
            if not st.session_state.flashcard_submitted:
                correct_set = set(q["answers"])
                selected_set = set(selected_keys)

                if selected_set == correct_set:
                    st.success("✅ Correct!")
                    st.session_state.correct_count += 1
                else:
                    st.error("❌ Incorrect.")
                    st.markdown(f"**Correct answers are:** {', '.join(correct_set)}")

                    # Log this mistake in MISTAKES_FILE
                    question_key = f"{today_key}_q{idx}"
                    mistakes_data[question_key] = mistakes_data.get(question_key, 0) + 1
                    save_json(MISTAKES_FILE, mistakes_data)

                # Mark this question as answered (and save)
                if idx not in answered_ids:
                    answered_ids.append(idx)
                    answered_data[today_key] = answered_ids
                    save_json(ANSWERED_FILE, answered_data)

                # Save current correct_count + index + order back to disk so we can resume mid-round
                flashcard_state[today_key] = {
                    "order": st.session_state.flashcard_order,
                    "index": st.session_state.flashcard_index,
                    "correct_count": st.session_state.correct_count
                }
                save_json(ORDER_FILE, flashcard_state)

                st.session_state.flashcard_submitted = True
            else:
                st.info("⚠️ You've already submitted this question. Click Next to continue.")

    # ─── Next Logic ─────────────────────────────────────────────────────────
    if st.button("Next"):
        if not st.session_state.flashcard_submitted:
            st.warning("⚠️ Please submit your answer before going to the next question.")
        else:
            # Clear the checkboxes for this question from session_state
            for key in q["options"].keys():
                session_key = f"{today_key}_q{idx}_opt_{key}"
                st.session_state.pop(session_key, None)

            # Advance to next index
            st.session_state.flashcard_index += 1
            st.session_state.flashcard_submitted = False

            # Save the new index back to disk
            flashcard_state[today_key] = {
                "order": st.session_state.flashcard_order,
                "index": st.session_state.flashcard_index,
                "correct_count": st.session_state.correct_count
            }
            save_json(ORDER_FILE, flashcard_state)

            st.experimental_rerun()

    # ─── Progress Bar & Info ───────────────────────────────────────────────
    st.progress(len(answered_ids) / total)
    st.caption(f"Answered so far: {len(answered_ids)} / {total}")
    st.caption(f"Rounds completed today: {completed_rounds}")

    # ─── Reset Today (full reset) ──────────────────────────────────────────
    if st.button("🔄 Reset Today"):
        # Clear answered IDs
        answered_data[today_key] = []
        save_json(ANSWERED_FILE, answered_data)

        # Reset completed rounds
        progress_data[today_key] = 0
        save_json(PROGRESS_FILE, progress_data)

        # Wipe flashcard_state so next run shuffles afresh
        if today_key in flashcard_state:
            del flashcard_state[today_key]
        save_json(ORDER_FILE, flashcard_state)

        # Clear mistakes for today (optional)
        for qid in list(mistakes_data.keys()):
            if qid.startswith(today_key):
                del mistakes_data[qid]
        save_json(MISTAKES_FILE, mistakes_data)

        # Clear session_state
        for k in ["flashcard_index", "flashcard_order", "flashcard_submitted", "correct_count"]:
            st.session_state.pop(k, None)

        st.success("✅ Progress for today has been reset.")
        st.experimental_rerun()

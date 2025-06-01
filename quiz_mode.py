import streamlit as st
from loaders import load_flashcards
from session import get_today_batch
from scoring import record_attempt, load_progress  # record_attempt will handle both marking answered & mistakes

def run_quiz_mode():
    """
    Renders all of today's questions at once in a single form.
    The user checks boxes for each question’s options, then clicks “Submit All”.
    After submission, shows total score and marks each question as correct/wrong.
    """

    # Load flashcards + progress to know which day we’re on
    all_flashcards = load_flashcards()
    prog = load_progress()
    day = prog.get("day", 1)

    st.header(f"Day {day} Quiz Mode – Answer All Questions & Submit Together")

    daily_batch = get_today_batch(all_flashcards, day)
    n_questions = len(daily_batch)

    # Build a big form so “Submit All” only appears once
    form = st.form(key="quiz_all_form", clear_on_submit=False)

    # Within the form, for each question, render its checkboxes with unique keys
    selections = {}  # will hold { qid: [letters_selected], … }
    for card in daily_batch:
        qid = card["id"]
        form.markdown(f"**Q{qid}: {card['question']}**")
        form.markdown(f"*{card['instruction']}*")

        # Create an empty list in selections for this question
        selections[qid] = []

        # Render checkboxes for each option
        for letter, text in card["options"].items():
            checkbox_key = f"quiz_{qid}_{letter}"
            if form.checkbox(f"{letter}. {text}", key=checkbox_key):
                selections[qid].append(letter)
        form.write("---")

    submitted_all = form.form_submit_button("Submit All Answers")

    if submitted_all:
        # Evaluate each question, record attempts, and generate feedback
        correct_count = 0
        wrong_list = []  # will hold (qid, selected_set, correct_set) for feedback display

        for card in daily_batch:
            qid = card["id"]
            correct_set = set(card["answers"])
            selected_set = set(selections[qid])

            # In Quiz mode, ANY deviation (missing or extra letter) = wrong
            is_question_correct = (selected_set == correct_set)
            if is_question_correct:
                correct_count += 1
            else:
                wrong_list.append((qid, selected_set, correct_set))

            # Record attempt (this also increments mistakes if wrong)
            record_attempt(qid, is_question_correct)

        # Show total score
        st.success(f"🏆 You scored {correct_count} out of {n_questions} ({correct_count}/{n_questions})")

        # Show detailed feedback question by question
        if correct_count < n_questions:
            st.subheader("Review of Incorrect Questions")
            for (qid, sel_set, corr_set) in wrong_list:
                card = next(c for c in daily_batch if c["id"] == qid)
                st.markdown(f"**Q{qid}: {card['question']}**")
                st.write(f"- Your answer: {', '.join(sorted(sel_set)) or '(none)'}")
                st.write(f"- Correct answer: {', '.join(sorted(corr_set))}")
                st.error("❌ Wrong")
                st.write("---")
        else:
            st.balloons()
            st.info("All correct—great job!")

import streamlit as st
from loaders import load_flashcards
from scoring import get_mistakes

def run_mistake_review():
    """
    Displays all questions that were ever answered “wrong” (in any mode),
    along with the count of how many times each was answered wrong.
    Sorted by highest mistake count first.
    """
    mistakes = get_mistakes()  # { "qid_str": count, … }
    if not mistakes:
        st.info("No mistakes recorded yet.")
        return

    # Convert to list of (qid_int, count) and sort by count descending
    mistake_list = []
    for qid_str, count in mistakes.items():
        try:
            qid = int(qid_str)
        except ValueError:
            continue
        mistake_list.append((qid, count))
    mistake_list.sort(key=lambda x: x[1], reverse=True)

    # Load flashcards to get question text
    all_flashcards = load_flashcards()
    flashcard_map = {card["id"]: card for card in all_flashcards}

    st.header("Mistake Review – Questions You Got Wrong & Counts")

    for (qid, count) in mistake_list:
        card = flashcard_map.get(qid)
        if not card:
            continue
        st.markdown(f"**Q{qid}: {card['question']}**")
        st.write(f"- Mistakes: {count} time(s)")
        # Also show correct answer(s)
        correct_letters = ", ".join(card["answers"])
        st.success(f"Correct answer(s): {correct_letters}")
        st.write("---")

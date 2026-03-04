# utils/memory_runtime.py

def find_similar_past_problems(system_memory, current_text):
    """
    Simple similarity based on prefix matching.
    You can upgrade later to embedding similarity.
    """

    if not current_text:
        return []

    current_text = current_text.lower()

    similar = []

    for m in system_memory:
        past_input = m.get("original_input", "").lower()

        # simple containment logic
        if current_text[:15] in past_input or past_input[:15] in current_text:
            similar.append(m)

    return similar


def memory_success_boost(similar_memories):
    """
    Count successful past problems.
    """
    success_count = sum(
        1 for m in similar_memories
        if m.get("verifier_outcome") == "correct"
    )

    return success_count
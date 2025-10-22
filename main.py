from typing import Dict, Any

from agents.diagnostic import adaptive_diagnostic_node, MIN_DIAGNOSTIC_CONFIDENCE, MAX_DIAGNOSTIC_QUESTIONS


def main():
    print("TeachAgent: Adaptive Diagnostic")
    topic = input("Enter a topic to diagnose (e.g., 'binary search', 'Bayes theorem'): ").strip()
    if not topic:
        print("Topic is required. Exiting.")
        return

    # Minimal initial state required by the diagnostic node
    state: Dict[str, Any] = {
        "topic": topic,
        "diagnostic_confidence": 0.0,
        "diagnostic_questions": [],
        "diagnostic_answers": [],
        "estimated_level": 0.2,
        "decision_log": [],
    }

    while True:
        updates = adaptive_diagnostic_node(state)
        state.update(updates)

        confidence = state.get("diagnostic_confidence", 0.0)
        num_questions = len(state.get("diagnostic_questions", []))

        if confidence >= MIN_DIAGNOSTIC_CONFIDENCE or num_questions >= MAX_DIAGNOSTIC_QUESTIONS:
            print("\nDiagnostic completed.")
            print(f"Estimated level: {state.get('estimated_level', 0.0):.2f}")
            print(f"Confidence: {confidence:.2f}")
            print("\nDecision log:")
            for entry in state.get("decision_log", []):
                print(f"- {entry}")
            break


if __name__ == "__main__":
    main()

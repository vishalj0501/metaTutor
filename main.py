from agents.strategies import get_default_strategies
from core.state import create_initial_state
from core.graph import build_teaching_graph


def main():
    print("="*80)
    print("METATUTOR: Adaptive Learning System")
    print("="*80)
    
    topic = input("\nEnter a topic to learn (e.g., 'binary search', 'Bayes theorem'): ").strip()
    if not topic:
        print("Topic is required. Exiting.")
        return

    state = create_initial_state(topic)
    state["available_strategies"] = get_default_strategies()
    state["strategy_attempts"] = {s["name"]: 0 for s in state["available_strategies"]}
    
    print(f"\nLearning Goal: Master {topic}")
    print(f"Target Proficiency: {state['target_proficiency']:.1f}")
    print(f"Max Attempts: {state['max_attempts']}")
    
    print(f"\n" + "="*60)
    print(f"Starting LangGraph Workflow")
    print("="*60)
    
    graph = build_teaching_graph()
    
    print(f"\nExecuting workflow...")
    final_state = graph.invoke(state, config={"recursion_limit": 500})
    
    next_action = final_state.get("next_action", "unknown")
    goal_achieved = final_state.get("goal_achieved", False)
    
    print(f"\n" + "="*60)
    print(f"Workflow Completed")
    print("="*60)
    
    if goal_achieved or next_action == "end_success":
        print(f"\nLEARNING GOAL ACHIEVED!")
        print(f"   Student has reached target proficiency!")
    elif next_action == "end_max_attempts":
        print(f"\nMax attempts reached. Ending session.")
    elif next_action == "end_stuck":
        print(f"\nStudent appears stuck. Ending session.")
        print(f"   Consider reviewing prerequisite knowledge or trying a different approach.")
    elif next_action == "prerequisite":
        prerequisite_topic = final_state.get("prerequisite_topic", "")
        if prerequisite_topic:
            print(f"\nPrerequisite needed: {prerequisite_topic}")
            print(f"   Consider learning {prerequisite_topic} first before continuing with {topic}")
    else:
        print(f"\nWorkflow ended with action: {next_action}")
    
    state = final_state
    
    print(f"\n" + "="*80)
    print(f"LEARNING SESSION SUMMARY")
    print("="*80)
    
    print(f"\nTopic: {topic}")
    print(f"Final Proficiency: {state.get('current_proficiency', 0.0):.2f}")
    print(f"Target Proficiency: {state.get('target_proficiency', 0.8):.2f}")
    print(f"Sessions Completed: {len(state.get('sessions', []))}")
    print(f"Total Attempts: {state.get('current_attempt', 0)}")
    
    print(f"\nStrategy Performance:")
    sessions = state.get("sessions", [])
    if sessions:
        strategy_scores = {}
        for session in sessions:
            strategy = session["strategy"]
            score = session["score"]
            if strategy not in strategy_scores:
                strategy_scores[strategy] = []
            strategy_scores[strategy].append(score)
        
        for strategy, scores in strategy_scores.items():
            avg_score = sum(scores) / len(scores)
            print(f"   {strategy:20s}: {avg_score:.2f} (used {len(scores)} times)")

    print(f"\nAgent Decision Log:")
    for i, decision in enumerate(state.get("decision_log", []), 1):
        print(f"   {i:2d}. {decision}")
    
    from agents.strategies import effectiveness_tracker
    filename = effectiveness_tracker.export_data()
    print(f"\nEffectiveness data exported to: {filename}")


if __name__ == "__main__":
    main()

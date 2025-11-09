from typing import Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from agents.strategies import get_default_strategies, track_session_effectiveness
from core.state import create_initial_state
from core.graph import build_teaching_graph


def main():
    """Main application with integrated strategy selection."""
    
    print("="*80)
    print("🎓 TEACHAGENT: Adaptive Learning System")
    print("="*80)
    
    topic = input("\nEnter a topic to learn (e.g., 'binary search', 'Bayes theorem'): ").strip()
    if not topic:
        print("Topic is required. Exiting.")
        return

    # Create initial state
    state = create_initial_state(topic)
    state["available_strategies"] = get_default_strategies()
    state["strategy_attempts"] = {s["name"]: 0 for s in state["available_strategies"]}
    
    print(f"\n🎯 Learning Goal: Master {topic}")
    print(f"📊 Target Proficiency: {state['target_proficiency']:.1f}")
    print(f"🔄 Max Attempts: {state['max_attempts']}")
    
    # Build and run LangGraph workflow
    print(f"\n" + "="*60)
    print(f"🚀 Starting LangGraph Workflow")
    print("="*60)
    
    graph = build_teaching_graph()
    
    # Run the workflow
    print(f"\n▶️  Executing workflow...")
    final_state = graph.invoke(state)
    
    # Handle final state and display results
    next_action = final_state.get("next_action", "unknown")
    goal_achieved = final_state.get("goal_achieved", False)
    
    print(f"\n" + "="*60)
    print(f"🏁 Workflow Completed")
    print("="*60)
    
    if goal_achieved or next_action == "end_success":
        print(f"\n🎉 LEARNING GOAL ACHIEVED!")
        print(f"   Student has reached target proficiency!")
    elif next_action == "end_max_attempts":
        print(f"\n⏸️  Max attempts reached. Ending session.")
    elif next_action == "end_stuck":
        print(f"\n⚠️  Student appears stuck. Ending session.")
        print(f"   Consider reviewing prerequisite knowledge or trying a different approach.")
    elif next_action == "prerequisite":
        prerequisite_topic = final_state.get("prerequisite_topic", "")
        if prerequisite_topic:
            print(f"\n📚 Prerequisite needed: {prerequisite_topic}")
            print(f"   Consider learning {prerequisite_topic} first before continuing with {topic}")
    else:
        print(f"\n⏸️  Workflow ended with action: {next_action}")
    
    # Update state reference for summary
    state = final_state
    
    # Final Summary
    print(f"\n" + "="*80)
    print(f"📊 LEARNING SESSION SUMMARY")
    print("="*80)
    
    print(f"\n🎯 Topic: {topic}")
    print(f"📈 Final Proficiency: {state.get('current_proficiency', 0.0):.2f}")
    print(f"🎯 Target Proficiency: {state.get('target_proficiency', 0.8):.2f}")
    print(f"📚 Sessions Completed: {len(state.get('sessions', []))}")
    print(f"🔄 Total Attempts: {state.get('current_attempt', 0)}")
    
    # Strategy Performance Summary
    print(f"\n📊 Strategy Performance:")
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
    
    # Decision Log
    print(f"\n🤖 Agent Decision Log:")
    for i, decision in enumerate(state.get("decision_log", []), 1):
        print(f"   {i:2d}. {decision}")
    
    # Export tracking data
    from agents.strategies import effectiveness_tracker
    filename = effectiveness_tracker.export_data()
    print(f"\n💾 Effectiveness data exported to: {filename}")


if __name__ == "__main__":
    main()

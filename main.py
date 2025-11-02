from typing import Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from agents.diagnostic import adaptive_diagnostic_node, MIN_DIAGNOSTIC_CONFIDENCE, MAX_DIAGNOSTIC_QUESTIONS
from agents.strategy_selector import strategy_selector_node
from agents.teaching_session import teaching_session_node
from agents.strategies import get_default_strategies, track_session_effectiveness
from core.state import create_initial_state


def run_teaching_session(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a complete teaching session using the selected strategy.
    
    This simulates the teaching process and returns a session result.
    """
    
    print(f"\n" + "="*60)
    print(f"📚 TEACHING SESSION")
    print("="*60)
    
    strategy = state.get("current_strategy", "direct_explanation")
    topic = state.get("topic", "Unknown Topic")
    
    print(f"\n🎯 Teaching Strategy: {strategy}")
    print(f"📖 Topic: {topic}")
    print(f"👤 Student Level: {state.get('current_proficiency', 0.0):.2f}")
    
    # Simulate teaching process
    print(f"\n📝 Teaching Process:")
    print(f"   1. Generating explanation using {strategy} approach...")
    print(f"   2. Creating assessment question...")
    print(f"   3. Evaluating student response...")
    
    # Simulate session score (this would come from actual teaching)
    # For demo, we'll use a simple simulation
    base_score = 0.7
    strategy_bonus = {
        "direct_explanation": 0.0,
        "socratic": 0.1,
        "worked_example": 0.15,
        "analogy": 0.05,
        "visual": 0.1
    }.get(strategy, 0.0)
    
    level_factor = 1.0 - (state.get("current_proficiency", 0.5) * 0.3)
    simulated_score = min(1.0, base_score + strategy_bonus + level_factor)
    
    print(f"   4. Session Score: {simulated_score:.2f}")
    
    # Create session record
    session = {
        "session_id": len(state.get("sessions", [])) + 1,
        "strategy": strategy,
        "score": simulated_score,
        "topic": topic,
        "explanation": f"Explanation using {strategy} for {topic}",
        "question": f"What is the key concept of {topic}?",
        "user_answer": "Student provided answer",
        "correct_answer": "Correct answer",
        "feedback": f"Feedback based on {strategy} approach",
        "timestamp": "2024-01-01T10:00:00"
    }
    
    # Update state
    new_sessions = state.get("sessions", []) + [session]
    
    # Track effectiveness
    track_session_effectiveness(
        strategy, 
        simulated_score, 
        topic, 
        state.get("current_proficiency", 0.5)
    )
    
    # Update proficiency
    proficiency_gain = simulated_score * 0.1
    new_proficiency = min(1.0, state.get("current_proficiency", 0.0) + proficiency_gain)
    
    print(f"\n📈 Learning Progress:")
    print(f"   Proficiency Gain: +{proficiency_gain:.2f}")
    print(f"   New Proficiency: {new_proficiency:.2f}")
    
    return {
        "sessions": new_sessions,
        "current_proficiency": new_proficiency,
        "consecutive_failures": 0 if simulated_score >= 0.6 else state.get("consecutive_failures", 0) + 1,
        "stuck_counter": 0 if simulated_score >= 0.6 else state.get("stuck_counter", 0) + 1
    }


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
    
    # Phase 1: Diagnostic
    print(f"\n" + "="*60)
    print(f"🔍 PHASE 1: DIAGNOSTIC ASSESSMENT")
    print("="*60)
    
    diagnostic_complete = False
    while not diagnostic_complete:
        updates = adaptive_diagnostic_node(state)
        state.update(updates)

        confidence = state.get("diagnostic_confidence", 0.0)
        num_questions = len(state.get("diagnostic_questions", []))

        if confidence >= MIN_DIAGNOSTIC_CONFIDENCE or num_questions >= MAX_DIAGNOSTIC_QUESTIONS:
            diagnostic_complete = True
            print(f"\n✅ Diagnostic completed.")
            print(f"   Estimated Level: {state.get('estimated_level', 0.0):.2f}")
            print(f"   Confidence: {confidence:.2f}")
            
            # Set initial proficiency based on diagnostic
            state["current_proficiency"] = state.get("estimated_level", 0.2)
    
    # Phase 2: Adaptive Teaching
    print(f"\n" + "="*60)
    print(f"📚 PHASE 2: ADAPTIVE TEACHING")
    print("="*60)
    
    session_count = 0
    max_sessions = 8
    
    while (session_count < max_sessions and 
           state.get("current_proficiency", 0.0) < state.get("target_proficiency", 0.8) and
           state.get("current_attempt", 0) < state.get("max_attempts", 10)):
        
        session_count += 1
        state["current_attempt"] = state.get("current_attempt", 0) + 1
        
        print(f"\n--- Session {session_count} ---")
        
        # Step 1: Strategy Selection
        print(f"\n🤔 Agent selecting teaching strategy...")
        updates = strategy_selector_node(state)
        state.update(updates)
        
        selected_strategy = state["current_strategy"]
        print(f"✅ Selected: {selected_strategy}")
        
        # Step 2: Teaching Session
        session_updates = teaching_session_node(state)
        state.update(session_updates)
        
        # Step 3: Progress Check
        current_proficiency = state.get("current_proficiency", 0.0)
        target_proficiency = state.get("target_proficiency", 0.8)
        
        print(f"\n📊 Progress Update:")
        print(f"   Current Proficiency: {current_proficiency:.2f}")
        print(f"   Target Proficiency: {target_proficiency:.2f}")
        print(f"   Progress: {(current_proficiency/target_proficiency)*100:.1f}%")
        
        if current_proficiency >= target_proficiency:
            print(f"\n🎉 LEARNING GOAL ACHIEVED!")
            print(f"   Student has reached target proficiency!")
            break
        
        # Check if stuck
        consecutive_failures = state.get("consecutive_failures", 0)
        if consecutive_failures >= 3:
            print(f"\n⚠️  Student appears stuck ({consecutive_failures} consecutive failures)")
            print(f"   Agent will try different approaches...")
        
        # Pause for user input
        if session_count < max_sessions:
            input(f"\n⏸️  Press Enter to continue to next session...")
    
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

"""
Test script for meta_reasoner_node

Run this to test the meta-reasoner with different scenarios.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from core.state import create_initial_state
from agents.meta_reasoner_node import meta_reasoner_node
from agents.strategies import get_default_strategies


def test_scenario(name: str, state_updates: dict, description: str):
    """Test a specific scenario."""
    print("\n" + "="*80)
    print(f"🧪 TEST SCENARIO: {name}")
    print("="*80)
    print(f"Description: {description}")
    
    # Create base state
    topic = "binary search"
    state = create_initial_state(topic)
    state["available_strategies"] = get_default_strategies()
    state["strategy_attempts"] = {s["name"]: 0 for s in state["available_strategies"]}
    state["estimated_level"] = 0.2  # From diagnostic
    
    # Apply scenario updates
    state.update(state_updates)
    
    # Run meta-reasoner
    updates = meta_reasoner_node(state)
    state.update(updates)
    
    # Display results
    print(f"\n📊 Result:")
    print(f"   Next Action: {state.get('next_action', 'unknown')}")
    print(f"   Goal Achieved: {state.get('goal_achieved', False)}")
    print(f"   Needs Prerequisite: {state.get('needs_prerequisite', False)}")
    if state.get('prerequisite_topic'):
        print(f"   Prerequisite Topic: {state.get('prerequisite_topic')}")
    
    return state.get('next_action')


def test_all_scenarios():
    """Test all decision paths."""
    
    print("="*80)
    print("🧪 TESTING META-REASONER NODE - ALL DECISION PATHS")
    print("="*80)
    
    # Scenario 1: CONTINUE - Making progress
    test_scenario(
        "CONTINUE - Making Progress",
        {
            "current_proficiency": 0.5,
            "target_proficiency": 0.8,
            "current_attempt": 3,
            "max_attempts": 10,
            "consecutive_failures": 0,
            "stuck_counter": 0,
            "sessions": [
                {"session_id": 1, "strategy": "direct_explanation", "score": 0.7},
                {"session_id": 2, "strategy": "worked_example", "score": 0.75},
                {"session_id": 3, "strategy": "analogy", "score": 0.8}
            ]
        },
        "Student is making progress, proficiency below target, attempts remaining"
    )
    
    # Scenario 2: END_SUCCESS - Goal achieved
    test_scenario(
        "END_SUCCESS - Goal Achieved",
        {
            "current_proficiency": 0.85,
            "target_proficiency": 0.8,
            "current_attempt": 5,
            "max_attempts": 10,
            "consecutive_failures": 0,
            "stuck_counter": 0,
            "sessions": [
                {"session_id": i, "strategy": "direct_explanation", "score": 0.8 + i*0.02}
                for i in range(1, 6)
            ]
        },
        "Student has reached target proficiency"
    )
    
    # Scenario 3: END_MAX_ATTEMPTS
    test_scenario(
        "END_MAX_ATTEMPTS",
        {
            "current_proficiency": 0.6,
            "target_proficiency": 0.8,
            "current_attempt": 10,
            "max_attempts": 10,
            "consecutive_failures": 1,
            "stuck_counter": 2,
            "sessions": [
                {"session_id": i, "strategy": "direct_explanation", "score": 0.5 + (i % 3) * 0.1}
                for i in range(1, 11)
            ]
        },
        "Max attempts reached, proficiency below target"
    )
    
    # Scenario 4: END_STUCK
    test_scenario(
        "END_STUCK",
        {
            "current_proficiency": 0.3,
            "target_proficiency": 0.8,
            "current_attempt": 5,
            "max_attempts": 10,
            "consecutive_failures": 4,
            "stuck_counter": 5,
            "sessions": [
                {"session_id": i, "strategy": f"strategy_{i%5}", "score": 0.2 + (i % 2) * 0.1}
                for i in range(1, 6)
            ]
        },
        "Student stuck with many consecutive failures, no progress"
    )
    
    # Scenario 5: PREREQUISITE
    test_scenario(
        "PREREQUISITE",
        {
            "current_proficiency": 0.25,
            "target_proficiency": 0.8,
            "current_attempt": 4,
            "max_attempts": 10,
            "consecutive_failures": 3,
            "stuck_counter": 4,
            "sessions": [
                {"session_id": i, "strategy": f"strategy_{i%5}", "score": 0.2}
                for i in range(1, 5)
            ]
        },
        "Student consistently struggling, might need prerequisite knowledge"
    )
    
    print("\n" + "="*80)
    print("✅ All test scenarios completed!")
    print("="*80)


if __name__ == "__main__":
    test_all_scenarios()


"""
Test script for evaluate_node

Run this to test just the evaluation node without running the full system.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from core.state import create_initial_state
from agents.evaluate_node import evaluate_node
from agents.strategies import get_default_strategies


def test_evaluate_node():
    """Test the evaluate_node with sample data."""
    
    print("="*80)
    print("🧪 TESTING EVALUATION NODE")
    print("="*80)
    
    # Create a test state
    topic = "binary search"
    state = create_initial_state(topic)
    
    # Set up test data
    state["available_strategies"] = get_default_strategies()
    state["strategy_attempts"] = {s["name"]: 0 for s in state["available_strategies"]}
    state["current_strategy"] = "direct_explanation"
    state["current_proficiency"] = 0.5
    state["current_question"] = "What is the time complexity of binary search?"
    state["current_user_answer"] = input("\nEnter your answer to test evaluation: ").strip()
    state["current_correct_answer"] = "Binary search has O(log n) time complexity"
    state["current_question_difficulty"] = 0.6
    state["current_explanation"] = "Binary search is a divide and conquer algorithm"
    state["current_teaching_data"] = {
        "explanation": "Binary search works by repeatedly dividing the search space in half",
        "key_points": ["Divide and conquer", "O(log n) complexity", "Requires sorted array"]
    }
    
    print(f"\n📝 Test Setup:")
    print(f"   Topic: {topic}")
    print(f"   Question: {state['current_question']}")
    print(f"   Your Answer: {state['current_user_answer']}")
    print(f"   Difficulty: {state['current_question_difficulty']}")
    print(f"   Current Proficiency: {state['current_proficiency']:.2f}")
    
    # Run evaluation node
    print(f"\n{'='*80}")
    updates = evaluate_node(state)
    state.update(updates)
    
    # Display results
    print(f"\n{'='*80}")
    print("📊 TEST RESULTS")
    print("="*80)
    print(f"   Final Proficiency: {state.get('current_proficiency', 0.0):.2f}")
    print(f"   Sessions Created: {len(state.get('sessions', []))}")
    
    if state.get('sessions'):
        session = state['sessions'][-1]
        print(f"\n   Last Session:")
        print(f"     Score: {session['score']:.2f}")
        print(f"     Strategy: {session['strategy']}")
        print(f"     Feedback: {session['feedback'][:100]}...")
    
    print(f"\n✅ Evaluation node test complete!")


if __name__ == "__main__":
    test_evaluate_node()


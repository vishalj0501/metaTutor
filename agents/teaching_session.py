"""
Teaching Session Node

This module implements the teaching session node that uses the selected strategy
to generate structured teaching content in JSON format.
"""

from typing import Dict, Any
import random

from core.state import AgentState
from agents.strategies import get_strategy_prompt, update_strategy_effectiveness, track_session_effectiveness
from config.parsers import parse_teaching_response, safe_parse
from tools.llm import get_llm


def teaching_session_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute a teaching session using the selected strategy.
    
    This node:
    1. Gets the current strategy from state
    2. Generates teaching content using LLM
    3. Parses the JSON response
    4. Creates a session record
    5. Updates effectiveness tracking
    6. Returns session results
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with session updates
    """
    
    print("\n" + "="*60)
    print("📚 TEACHING SESSION NODE")
    print("="*60)
    
    # ===== STEP 1: Extract Context =====
    
    strategy = state.get("current_strategy", "direct_explanation")
    topic = state.get("topic", "Unknown Topic")
    student_level = state.get("current_proficiency", 0.5)
    
    print(f"\n🎯 Teaching Strategy: {strategy}")
    print(f"📖 Topic: {topic}")
    print(f"👤 Student Level: {student_level:.2f}")
    
    # ===== STEP 2: Generate Teaching Content =====
    
    print(f"\n🤖 Generating teaching content...")
    
    # Get strategy-specific prompt
    prompt = get_strategy_prompt(strategy, topic, student_level)
    
    # Call LLM
    llm = get_llm(use_mock=False)
    response = llm.invoke(prompt)
    
    # Handle response format
    if hasattr(response, 'content'):
        response_text = response.content
    else:
        response_text = str(response)
    
    print(f"✅ LLM response received")
    
    # ===== STEP 3: Parse Teaching Response =====
    
    print(f"\n🔍 Parsing teaching response...")
    
    try:
        teaching_data = parse_teaching_response(response_text, strategy)
        print(f"✅ Successfully parsed {strategy} response")
        
        # Display teaching content based on strategy
        _display_teaching_content(strategy, teaching_data)
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        print(f"   Using fallback teaching data")
        
        # Use safe parser with fallback
        teaching_data = safe_parse(response_text, parse_teaching_response, strategy)
    
    # ===== STEP 4: Simulate Student Interaction =====
    
    print(f"\n👤 Simulating student interaction...")
    
    # Simulate student answering the assessment question
    assessment_question = teaching_data.get("assessment_question", "What did you learn?")
    expected_answer = teaching_data.get("expected_answer", "Student should demonstrate understanding")
    
    print(f"   Question: {assessment_question}")
    print(f"   Expected: {expected_answer}")
    
    # Simulate student response and scoring
    session_score = _simulate_student_response(strategy, student_level, teaching_data)
    
    print(f"   Session Score: {session_score:.2f}")
    
    # ===== STEP 5: Create Session Record =====
    
    session_id = len(state.get("sessions", [])) + 1
    
    session_record = {
        "session_id": session_id,
        "strategy": strategy,
        "score": session_score,
        "topic": topic,
        "explanation": _extract_explanation(strategy, teaching_data),
        "question": assessment_question,
        "user_answer": "Simulated student response",
        "correct_answer": expected_answer,
        "feedback": f"Feedback based on {strategy} approach",
        "timestamp": "2024-01-01T10:00:00",
        "teaching_data": teaching_data  # Store full teaching data
    }
    
    # ===== STEP 6: Update State =====
    
    new_sessions = state.get("sessions", []) + [session_record]
    
    # Track effectiveness
    track_session_effectiveness(strategy, session_score, topic, student_level)
    
    # Update strategy effectiveness in state
    updated_strategies = update_strategy_effectiveness(
        state.get("available_strategies", []),
        strategy,
        session_score
    )
    
    # Update proficiency
    proficiency_gain = session_score * 0.1
    new_proficiency = min(1.0, student_level + proficiency_gain)
    
    print(f"\n📈 Learning Progress:")
    print(f"   Proficiency Gain: +{proficiency_gain:.2f}")
    print(f"   New Proficiency: {new_proficiency:.2f}")
    
    # ===== STEP 7: Return Updates =====
    
    return {
        "sessions": new_sessions,
        "available_strategies": updated_strategies,
        "current_proficiency": new_proficiency,
        "consecutive_failures": 0 if session_score >= 0.6 else state.get("consecutive_failures", 0) + 1,
        "stuck_counter": 0 if session_score >= 0.6 else state.get("stuck_counter", 0) + 1
    }


def _display_teaching_content(strategy: str, teaching_data: Dict[str, Any]):
    """Display teaching content based on strategy type."""
    
    print(f"\n📝 Teaching Content ({strategy}):")
    
    if strategy == "direct_explanation":
        print(f"   Explanation: {teaching_data.get('explanation', 'N/A')[:100]}...")
        print(f"   Key Points: {teaching_data.get('key_points', [])}")
        
    elif strategy == "socratic":
        questions = teaching_data.get("questions", [])
        print(f"   Questions ({len(questions)}):")
        for i, q in enumerate(questions, 1):
            print(f"     {i}. {q}")
        
    elif strategy == "worked_example":
        print(f"   Problem: {teaching_data.get('problem_statement', 'N/A')[:100]}...")
        steps = teaching_data.get("solution_steps", [])
        print(f"   Solution Steps ({len(steps)}):")
        for step in steps[:3]:  # Show first 3 steps
            print(f"     Step {step.get('step', '?')}: {step.get('action', 'N/A')[:50]}...")
        
    elif strategy == "analogy":
        print(f"   Analogy: {teaching_data.get('analogy_concept', 'N/A')}")
        mapping = teaching_data.get("analogy_mapping", {})
        print(f"   Mapping: {list(mapping.keys())[:3]}...")
        
    elif strategy == "visual":
        print(f"   Visual Type: {teaching_data.get('visual_type', 'N/A')}")
        print(f"   Description: {teaching_data.get('visual_description', 'N/A')[:100]}...")
        components = teaching_data.get("key_components", [])
        print(f"   Components ({len(components)}): {[c.get('component', '?') for c in components[:3]]}")


def _simulate_student_response(strategy: str, student_level: float, teaching_data: Dict[str, Any]) -> float:
    """
    Simulate student response and calculate session score.
    
    This is a simplified simulation - in a real system, this would involve
    actual student interaction and assessment.
    """
    
    # Base score based on student level
    base_score = student_level * 0.8 + 0.2
    
    # Strategy effectiveness bonuses
    strategy_bonuses = {
        "direct_explanation": 0.0,
        "socratic": 0.1,
        "worked_example": 0.15,
        "analogy": 0.05,
        "visual": 0.1
    }
    
    bonus = strategy_bonuses.get(strategy, 0.0)
    
    # Add some randomness to simulate variability
    random_factor = random.uniform(-0.1, 0.1)
    
    final_score = min(1.0, base_score + bonus + random_factor)
    return max(0.0, final_score)


def _extract_explanation(strategy: str, teaching_data: Dict[str, Any]) -> str:
    """Extract explanation text based on strategy type."""
    
    if strategy == "direct_explanation":
        return teaching_data.get("explanation", "Direct explanation provided")
    
    elif strategy == "socratic":
        questions = teaching_data.get("questions", [])
        return f"Socratic questions: {'; '.join(questions[:2])}..."
    
    elif strategy == "worked_example":
        problem = teaching_data.get("problem_statement", "Worked example provided")
        return f"Worked example: {problem[:100]}..."
    
    elif strategy == "analogy":
        analogy = teaching_data.get("analogy_concept", "Analogy provided")
        return f"Analogy: {analogy}"
    
    elif strategy == "visual":
        visual_type = teaching_data.get("visual_type", "Visual representation")
        return f"Visual: {visual_type}"
    
    else:
        return "Teaching content provided"


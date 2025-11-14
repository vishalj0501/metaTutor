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
    print("Teaching Session Node")
    print("="*60)
    
    strategy = state.get("current_strategy", "direct_explanation")
    topic = state.get("topic", "Unknown Topic")
    student_level = state.get("current_proficiency", 0.5)
    
    print(f"\nTeaching Strategy: {strategy}")
    print(f"Topic: {topic}")
    print(f"Student Level: {student_level:.2f}")
    
    print(f"\nGenerating teaching content...")
    
    prompt = get_strategy_prompt(strategy, topic, student_level)
    
    llm = get_llm(use_mock=False)
    response = llm.invoke(prompt)
    
    if hasattr(response, 'content'):
        response_text = response.content
    else:
        response_text = str(response)
    
    print(f"LLM response received")
    
    print(f"\nParsing teaching response...")
    
    try:
        teaching_data = parse_teaching_response(response_text, strategy)
        print(f"Successfully parsed {strategy} response")
        
        _display_teaching_content(strategy, teaching_data)
        
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"   Using fallback teaching data")
        
        teaching_data = safe_parse(response_text, parse_teaching_response, strategy)
    
    print(f"\nSimulating student interaction...")
    
    assessment_question = teaching_data.get("assessment_question", "What did you learn?")
    expected_answer = teaching_data.get("expected_answer", "Student should demonstrate understanding")
    
    print(f"   Question: {assessment_question}")
    print(f"   Expected: {expected_answer}")
    
    session_score = _simulate_student_response(strategy, student_level, teaching_data)
    
    print(f"   Session Score: {session_score:.2f}")

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
        "teaching_data": teaching_data
    }
    
    new_sessions = state.get("sessions", []) + [session_record]
    
    track_session_effectiveness(strategy, session_score, topic, student_level)
    
    updated_strategies = update_strategy_effectiveness(
        state.get("available_strategies", []),
        strategy,
        session_score
    )
    
    proficiency_gain = session_score * 0.1
    new_proficiency = min(1.0, student_level + proficiency_gain)
    
    print(f"\nLearning Progress:")
    print(f"   Proficiency Gain: +{proficiency_gain:.2f}")
    print(f"   New Proficiency: {new_proficiency:.2f}")
    
    return {
        "sessions": new_sessions,
        "available_strategies": updated_strategies,
        "current_proficiency": new_proficiency,
        "consecutive_failures": 0 if session_score >= 0.6 else state.get("consecutive_failures", 0) + 1,
        "stuck_counter": 0 if session_score >= 0.6 else state.get("stuck_counter", 0) + 1
    }


def _display_teaching_content(strategy: str, teaching_data: Dict[str, Any]):
    print(f"\nTeaching Content ({strategy}):")
    
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
        for step in steps[:3]:
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
    base_score = student_level * 0.8 + 0.2
    
    strategy_bonuses = {
        "direct_explanation": 0.0,
        "socratic": 0.1,
        "worked_example": 0.15,
        "analogy": 0.05,
        "visual": 0.1
    }
    
    bonus = strategy_bonuses.get(strategy, 0.0)
    
    random_factor = random.uniform(-0.1, 0.1)
    
    final_score = min(1.0, base_score + bonus + random_factor)
    return max(0.0, final_score)


def _extract_explanation(strategy: str, teaching_data: Dict[str, Any]) -> str:        
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


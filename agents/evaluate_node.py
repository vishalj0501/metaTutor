"""
Evaluation Node

This module implements the evaluation node that handles LLM-based grading,
proficiency tracking, and strategy effectiveness updates.
"""

from typing import Dict, Any
from datetime import datetime

from core.state import AgentState
from config.parsers import parse_answer_evaluation, safe_parse
from agents.strategies import update_strategy_effectiveness, track_session_effectiveness
from config.prompts import ANSWER_EVALUATION_PROMPT
from tools.llm import get_llm


def evaluate_node(state: AgentState) -> Dict[str, Any]:
    """
    Evaluate student answer using LLM-based grading.
    
    This node:
    1. Gets question, user_answer, and context from state
    2. Calls LLM for evaluation
    3. Calculates proficiency gain
    4. Creates session record
    5. Tracks effectiveness
    6. Updates strategy effectiveness
    7. Updates state
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with state updates
    """
    
    print("\n" + "="*60)
    print("📊 EVALUATION NODE")
    print("="*60)
    
    # ===== STEP 1: Extract Context =====
    
    strategy = state.get("current_strategy", "direct_explanation")
    topic = state.get("topic", "Unknown Topic")
    student_level = state.get("current_proficiency", 0.5)
    question = state.get("current_question", "")
    user_answer = state.get("current_user_answer", "")
    correct_answer = state.get("current_correct_answer", "")
    current_explanation = state.get("current_explanation", "")
    teaching_data = state.get("current_teaching_data", {})
    
    # Get difficulty from practice question data
    difficulty = state.get("current_question_difficulty", student_level)
    
    print(f"\n🎯 Strategy: {strategy}")
    print(f"📖 Topic: {topic}")
    print(f"👤 Student Level: {student_level:.2f}")
    print(f"📝 Question: {question[:80]}..." if len(question) > 80 else f"📝 Question: {question}")
    
    if not question:
        print("⚠️  No question found in state. Skipping evaluation.")
        return {}
    
    if not user_answer:
        print("⚠️  No user answer found in state. Using empty string.")
        user_answer = ""
    
    # ===== STEP 2: Evaluate Answer =====
    
    print(f"\n🔍 Evaluating answer using LLM...")
    
    # Format evaluation prompt
    prompt = ANSWER_EVALUATION_PROMPT.format(
        topic=topic,
        question=question,
        expected_level=difficulty,
        user_answer=user_answer
    )
    
    # Call LLM
    llm = get_llm(use_mock=False)
    response = llm.invoke(prompt)
    
    # Handle response format
    if hasattr(response, 'content'):
        response_text = response.content
    else:
        response_text = str(response)
    
    print(f"✅ LLM response received")
    
    # Parse evaluation response
    print(f"\n🔍 Parsing evaluation response...")
    
    try:
        evaluation = parse_answer_evaluation(response_text)
        print(f"✅ Successfully parsed evaluation response")
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        print(f"   Using fallback evaluation data")
        
        # Use safe parser with fallback
        evaluation = safe_parse(response_text, parse_answer_evaluation)
    
    session_score = evaluation["quality_score"]
    
    # ===== STEP 3: Display Evaluation Results =====
    
    print(f"\n📊 Evaluation Results:")
    print(f"   Score: {session_score:.2f}/1.0")
    print(f"   Reasoning: {evaluation['reasoning']}")
    
    if evaluation.get('strengths'):
        print(f"\n   ✅ Strengths:")
        for strength in evaluation['strengths']:
            print(f"      - {strength}")
    
    if evaluation.get('weaknesses'):
        print(f"\n   ⚠️  Areas to improve:")
        for weakness in evaluation['weaknesses']:
            print(f"      - {weakness}")
    
    print(f"\n   Level indication: {evaluation.get('level_indication', 'unknown')}")
    
    # ===== STEP 4: Calculate Proficiency Gain =====
    
    proficiency_gain = _calculate_proficiency_gain(
        score=session_score,
        current_level=student_level,
        difficulty=difficulty
    )
    
    new_proficiency = min(1.0, max(0.0, student_level + proficiency_gain))
    
    print(f"\n📈 Learning Progress:")
    print(f"   Proficiency Gain: {proficiency_gain:+.2f}")
    print(f"   New Proficiency: {new_proficiency:.2f} (from {student_level:.2f})")
    
    # ===== STEP 5: Create Session Record =====
    
    session_id = len(state.get("sessions", [])) + 1
    
    # Extract explanation text for session record
    explanation = _extract_explanation_for_session(strategy, teaching_data, current_explanation)
    
    session_record = {
        "session_id": session_id,
        "strategy": strategy,
        "score": session_score,
        "topic": topic,
        "explanation": explanation,
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "feedback": evaluation.get('reasoning', ''),
        "timestamp": datetime.now().isoformat()
    }
    
    # ===== STEP 6: Track Effectiveness =====
    
    # Track session effectiveness
    track_session_effectiveness(strategy, session_score, topic, student_level)
    
    # Update strategy effectiveness in state
    updated_strategies = update_strategy_effectiveness(
        state.get("available_strategies", []),
        strategy,
        session_score
    )
    
    # Display strategy effectiveness update
    strategy_obj = next((s for s in updated_strategies if s["name"] == strategy), None)
    if strategy_obj:
        print(f"\n📊 Strategy Effectiveness Update:")
        print(f"   {strategy}: {strategy_obj['effectiveness']:.2f}")
    
    # ===== STEP 7: Update State =====
    
    new_sessions = state.get("sessions", []) + [session_record]
    
    # Determine if this was a failure
    is_success = session_score >= 0.6
    consecutive_failures = 0 if is_success else state.get("consecutive_failures", 0) + 1
    stuck_counter = 0 if is_success else state.get("stuck_counter", 0) + 1
    
    # Increment attempt counter after each session
    current_attempt = state.get("current_attempt", 0) + 1
    
    decision = (
        f"📊 Evaluation: Score {session_score:.2f} | "
        f"{'Success' if is_success else 'Needs improvement'} | "
        f"Proficiency: {student_level:.2f} → {new_proficiency:.2f}"
    )
    
    return {
        "sessions": new_sessions,
        "available_strategies": updated_strategies,
        "current_proficiency": new_proficiency,
        "consecutive_failures": consecutive_failures,
        "stuck_counter": stuck_counter,
        "current_attempt": current_attempt,
        "decision_log": state.get("decision_log", []) + [decision]
    }


def _calculate_proficiency_gain(score: float, current_level: float, difficulty: float) -> float:
    """
    Calculate proficiency gain based on score, current level, and question difficulty.
    
    Args:
        score: Quality score from 0.0 to 1.0
        current_level: Current student proficiency level
        difficulty: Question difficulty level
        
    Returns:
        Proficiency adjustment (positive or negative)
    """
    
    # Base gain: score * 0.1 (linear scaling)
    base_gain = score * 0.1
    
    # Adjust based on difficulty vs current level
    level_difference = difficulty - current_level
    
    if level_difference > 0.2:
        # Question was harder than student level
        # Reward doing well on hard questions more
        if score >= 0.7:
            base_gain *= 1.3  # Bonus for handling hard questions
        elif score < 0.4:
            base_gain *= 0.7  # Less penalty for struggling with hard questions
    elif level_difference < -0.2:
        # Question was easier than student level
        # Penalize doing poorly on easy questions more
        if score < 0.6:
            base_gain *= 0.8  # More penalty for struggling with easy questions
    
    # Cap the gain to prevent wild swings
    gain = max(-0.15, min(0.15, base_gain))
    
    return gain


def _extract_explanation_for_session(strategy: str, teaching_data: Dict[str, Any], current_explanation: str) -> str:
    """Extract explanation text for session record."""
    
    if current_explanation:
        return current_explanation
    
    if not teaching_data:
        return "Teaching content provided"
    
    if strategy == "direct_explanation":
        return teaching_data.get("explanation", "Direct explanation provided")
    
    elif strategy == "socratic":
        questions = teaching_data.get("questions", [])
        if questions:
            return f"Socratic questions: {'; '.join(questions[:2])}..."
        return "Socratic questions provided"
    
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


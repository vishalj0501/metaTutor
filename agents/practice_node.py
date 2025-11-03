"""
Practice Node

This module implements the practice node that generates practice questions
based on what was taught and evaluates student responses.
"""

from typing import Dict, Any
from datetime import datetime

from core.state import AgentState
from agents.diagnostic import evaluate_answer_quality
from agents.strategies import update_strategy_effectiveness, track_session_effectiveness
from agents.parsers import parse_practice_question, safe_parse
from config.prompts import PRACTICE_QUESTION_PROMPT
from tools.llm import get_llm


def practice_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate practice question and evaluate student response.
    
    This node:
    1. Gets teaching content from state
    2. Generates practice question using LLM
    3. Parses the question
    4. Gets student input
    5. Evaluates answer using LLM
    6. Calculates proficiency gain
    7. Creates session record
    8. Updates state
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with state updates
    """
    
    print("\n" + "="*60)
    print("✏️  PRACTICE NODE")
    print("="*60)
    
    # ===== STEP 1: Extract Context =====
    
    strategy = state.get("current_strategy", "direct_explanation")
    topic = state.get("topic", "Unknown Topic")
    student_level = state.get("current_proficiency", 0.5)
    current_explanation = state.get("current_explanation", "")
    teaching_data = state.get("current_teaching_data", {})
    
    print(f"\n🎯 Strategy: {strategy}")
    print(f"📖 Topic: {topic}")
    print(f"👤 Student Level: {student_level:.2f}")
    
    # ===== STEP 2: Generate Practice Question =====
    
    print(f"\n🤖 Generating practice question...")
    
    # Create teaching summary from teaching_data
    teaching_summary = _create_teaching_summary(strategy, teaching_data, current_explanation)
    
    # Generate practice question prompt
    prompt = PRACTICE_QUESTION_PROMPT.format(
        topic=topic,
        student_level=student_level,
        strategy=strategy,
        teaching_summary=teaching_summary
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
    
    # ===== STEP 3: Parse Practice Question =====
    
    print(f"\n🔍 Parsing practice question...")
    
    try:
        practice_data = parse_practice_question(response_text)
        print(f"✅ Successfully parsed practice question")
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        print(f"   Using fallback practice question")
        
        # Use safe parser with fallback
        practice_data = safe_parse(response_text, parse_practice_question)
    
    question = practice_data.get("question", "What did you learn?")
    expected_answer = practice_data.get("expected_answer", "Student should demonstrate understanding")
    difficulty = practice_data.get("difficulty", 0.5)
    hints = practice_data.get("hints", [])
    reasoning = practice_data.get("reasoning", "")
    
    # ===== STEP 4: Display Question and Get Student Input =====
    
    print(f"\n📝 Practice Question:")
    print(f"   {question}")
    
    if hints:
        print(f"\n   💡 Hints available:")
        for i, hint in enumerate(hints, 1):
            print(f"      {i}. {hint}")
    
    if reasoning:
        print(f"\n   💭 Why this question: {reasoning}")
    
    # Get student answer
    print(f"\n👤 Your answer:")
    user_answer = input("   ").strip()
    
    if not user_answer:
        print("   ⚠️  No answer provided, using empty string")
        user_answer = ""
    
    # ===== STEP 5: Evaluate Answer =====
    
    print(f"\n🔍 Evaluating your answer...")
    
    evaluation = evaluate_answer_quality(
        question=question,
        user_answer=user_answer,
        expected_level=difficulty,
        topic=topic
    )
    
    session_score = evaluation["quality_score"]
    
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
    
    # ===== STEP 6: Create Session Record =====
    
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
        "correct_answer": expected_answer,
        "feedback": evaluation.get('reasoning', ''),
        "timestamp": datetime.now().isoformat()
    }
    
    # ===== STEP 7: Update State =====
    
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
    
    # ===== STEP 8: Return Updates =====
    
    decision = f"✏️  Practice session: Score {session_score:.2f} | {'Success' if session_score >= 0.6 else 'Needs improvement'}"
    
    return {
        "current_question": question,
        "current_correct_answer": expected_answer,
        "sessions": new_sessions,
        "available_strategies": updated_strategies,
        "current_proficiency": new_proficiency,
        "consecutive_failures": 0 if session_score >= 0.6 else state.get("consecutive_failures", 0) + 1,
        "stuck_counter": 0 if session_score >= 0.6 else state.get("stuck_counter", 0) + 1,
        "decision_log": state.get("decision_log", []) + [decision]
    }


def _create_teaching_summary(strategy: str, teaching_data: Dict[str, Any], current_explanation: str) -> str:
    """Create a summary of teaching content for practice question generation."""
    
    if not teaching_data:
        return current_explanation or "Teaching content provided"
    
    summary_parts = []
    
    if strategy == "direct_explanation":
        explanation = teaching_data.get("explanation", "")
        key_points = teaching_data.get("key_points", [])
        if explanation:
            summary_parts.append(f"Explanation: {explanation[:200]}")
        if key_points:
            summary_parts.append(f"Key points: {', '.join(key_points)}")
    
    elif strategy == "socratic":
        questions = teaching_data.get("questions", [])
        if questions:
            summary_parts.append(f"Socratic questions: {', '.join(questions[:3])}")
        sequence = teaching_data.get("question_sequence", "")
        if sequence:
            summary_parts.append(f"Sequence: {sequence[:100]}")
    
    elif strategy == "worked_example":
        problem = teaching_data.get("problem_statement", "")
        steps = teaching_data.get("solution_steps", [])
        if problem:
            summary_parts.append(f"Problem: {problem[:200]}")
        if steps:
            step_summary = "; ".join([f"Step {s.get('step', '?')}: {s.get('action', '')[:50]}" 
                                     for s in steps[:3]])
            summary_parts.append(f"Steps: {step_summary}")
    
    elif strategy == "analogy":
        analogy = teaching_data.get("analogy_concept", "")
        explanation = teaching_data.get("explanation", "")
        if analogy:
            summary_parts.append(f"Analogy: {analogy}")
        if explanation:
            summary_parts.append(f"Explanation: {explanation[:200]}")
    
    elif strategy == "visual":
        visual_type = teaching_data.get("visual_type", "")
        description = teaching_data.get("visual_description", "")
        if visual_type:
            summary_parts.append(f"Visual type: {visual_type}")
        if description:
            summary_parts.append(f"Description: {description[:200]}")
    
    if summary_parts:
        return " | ".join(summary_parts)
    
    return current_explanation or "Teaching content provided"


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


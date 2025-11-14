from typing import Dict, Any

from core.state import AgentState
from config.parsers import parse_practice_question, safe_parse
from config.prompts import PRACTICE_QUESTION_PROMPT
from tools.llm import get_llm


def practice_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate practice question and collect student response.
    
    This node:
    1. Gets teaching content from state
    2. Generates practice question using LLM
    3. Parses the question
    4. Displays question and gets student input
    5. Stores question and answer in state for evaluation
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with state updates (question, answer, difficulty)
    """
    
    print("\n" + "="*60)
    print("Practice Node")
    print("="*60)
    
    strategy = state.get("current_strategy", "direct_explanation")
    topic = state.get("topic", "Unknown Topic")
    student_level = state.get("current_proficiency", 0.5)
    current_explanation = state.get("current_explanation", "")
    teaching_data = state.get("current_teaching_data", {})
    
    print(f"\nStrategy: {strategy}")
    print(f"Topic: {topic}")
    print(f"Student Level: {student_level:.2f}")
    
    print(f"\nGenerating practice question...")
    
    teaching_summary = _create_teaching_summary(strategy, teaching_data, current_explanation)
    
    prompt = PRACTICE_QUESTION_PROMPT.format(
        topic=topic,
        student_level=student_level,
        strategy=strategy,
        teaching_summary=teaching_summary
    )
    
    llm = get_llm(use_mock=False)
    response = llm.invoke(prompt)
    
    if hasattr(response, 'content'):
        response_text = response.content
    else:
        response_text = str(response)
    
    print(f"LLM response received")
    
    print(f"\nParsing practice question...")
    
    try:
        practice_data = parse_practice_question(response_text)
        print(f"Successfully parsed practice question")
        
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"   Using fallback practice question")
        
        practice_data = safe_parse(response_text, parse_practice_question)
    
    question = practice_data.get("question", "What did you learn?")
    expected_answer = practice_data.get("expected_answer", "Student should demonstrate understanding")
    difficulty = practice_data.get("difficulty", 0.5)
    hints = practice_data.get("hints", [])
    reasoning = practice_data.get("reasoning", "")
    
    print(f"\nPractice Question:")
    print(f"   {question}")
    
    if hints:
        print(f"\nHints available:")
        for i, hint in enumerate(hints, 1):
            print(f"      {i}. {hint}")
    
    if reasoning:
        print(f"\nWhy this question: {reasoning}")
    
    print(f"\nYour answer:")
    user_answer = input("   ").strip()
    
    if not user_answer:
        print("No answer provided, using empty string")
        user_answer = ""
    
    print(f"\nAnswer collected. Ready for evaluation.")
    
    return {
        "current_question": question,
        "current_correct_answer": expected_answer,
        "current_user_answer": user_answer,
        "current_question_difficulty": difficulty
    }


def _create_teaching_summary(strategy: str, teaching_data: Dict[str, Any], current_explanation: str) -> str:        
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


from typing import Dict, Any

from core.state import AgentState
from agents.strategies import get_strategy_prompt
from config.parsers import parse_teaching_response, safe_parse
from tools.llm import get_llm


def teach_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate and display teaching content using the selected strategy.
    
    This node:
    1. Gets the current strategy from state
    2. Generates teaching content using LLM
    3. Parses the JSON response
    4. Displays teaching content
    5. Stores explanation and teaching_data in state
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with state updates
    """
    
    print("\n" + "="*60)
    print("Teach Node")
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
    
    explanation = _extract_explanation(strategy, teaching_data)
    
    decision = f"Taught {topic} using {strategy} strategy"
    
    return {
        "current_explanation": explanation,
        "current_teaching_data": teaching_data,
        "decision_log": state.get("decision_log", []) + [decision]
    }


def _display_teaching_content(strategy: str, teaching_data: Dict[str, Any]):
    print(f"\nTeaching Content ({strategy}):")
    
    if strategy == "direct_explanation":
        explanation = teaching_data.get('explanation', 'N/A')
        print(f"   Explanation: {explanation}")
        key_points = teaching_data.get('key_points', [])
        if key_points:
            print(f"\n   Key Points:")
            for i, point in enumerate(key_points, 1):
                print(f"     {i}. {point}")
        
    elif strategy == "socratic":
        questions = teaching_data.get("questions", [])
        print(f"   Questions ({len(questions)}):")
        for i, q in enumerate(questions, 1):
            print(f"     {i}. {q}")
        sequence = teaching_data.get("question_sequence", "")
        if sequence:
            print(f"\n   Sequence: {sequence}")
        
    elif strategy == "worked_example":
        problem = teaching_data.get('problem_statement', 'N/A')
        print(f"   Problem: {problem}")
        steps = teaching_data.get("solution_steps", [])
        print(f"\n   Solution Steps ({len(steps)}):")
        for step in steps:
            step_num = step.get('step', '?')
            action = step.get('action', 'N/A')
            explanation = step.get('explanation', '')
            print(f"     Step {step_num}: {action}")
            if explanation:
                print(f"       Why: {explanation}")
        final_answer = teaching_data.get("final_answer", "")
        if final_answer:
            print(f"\n   Final Answer: {final_answer}")
        
    elif strategy == "analogy":
        analogy_concept = teaching_data.get('analogy_concept', 'N/A')
        print(f"   Analogy Concept: {analogy_concept}")
        explanation = teaching_data.get('explanation', '')
        if explanation:
            print(f"\n   Explanation: {explanation}")
        mapping = teaching_data.get("analogy_mapping", {})
        if mapping:
            print(f"\n   Mapping:")
            for concept_feature, analogy_feature in mapping.items():
                print(f"     {concept_feature} → {analogy_feature}")
        limitations = teaching_data.get("limitations", "")
        if limitations:
            print(f"\n   Limitations: {limitations}")
        
    elif strategy == "visual":
        visual_type = teaching_data.get('visual_type', 'N/A')
        print(f"   Visual Type: {visual_type}")
        description = teaching_data.get('visual_description', 'N/A')
        print(f"\n   Description: {description}")
        ascii_art = teaching_data.get("ascii_art", "")
        if ascii_art:
            print(f"\n   ASCII Art:\n{ascii_art}")
        components = teaching_data.get("key_components", [])
        if components:
            print(f"\n   Key Components ({len(components)}):")
            for component in components:
                comp_name = component.get('component', '?')
                position = component.get('position', '?')
                purpose = component.get('purpose', '?')
                print(f"     - {comp_name}: {position} ({purpose})")
        connections = teaching_data.get("connections", "")
        if connections:
            print(f"\n   Connections: {connections}")


def _extract_explanation(strategy: str, teaching_data: Dict[str, Any]) -> str:        
    if strategy == "direct_explanation":
        return teaching_data.get("explanation", "Direct explanation provided")
    
    elif strategy == "socratic":
        questions = teaching_data.get("questions", [])
        if questions:
            return f"Socratic questions: {'; '.join(questions)}"
        return "Socratic questions provided"
    
    elif strategy == "worked_example":
        problem = teaching_data.get("problem_statement", "Worked example provided")
        steps = teaching_data.get("solution_steps", [])
        if steps:
            step_summary = "; ".join([f"Step {s.get('step', '?')}: {s.get('action', '')}" 
                                     for s in steps[:3]])
            return f"Worked example: {problem[:100]}... Steps: {step_summary}"
        return f"Worked example: {problem[:100]}..."
    
    elif strategy == "analogy":
        analogy = teaching_data.get("analogy_concept", "Analogy provided")
        explanation = teaching_data.get("explanation", "")
        if explanation:
            return f"Analogy: {analogy}. {explanation[:100]}..."
        return f"Analogy: {analogy}"
    
    elif strategy == "visual":
        visual_type = teaching_data.get("visual_type", "Visual representation")
        description = teaching_data.get("visual_description", "")
        if description:
            return f"Visual ({visual_type}): {description[:100]}..."
        return f"Visual: {visual_type}"
    
    else:
        return "Teaching content provided"

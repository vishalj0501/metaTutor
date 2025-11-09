"""
JSON Parsers for TeachAgent

This module contains parsers for all JSON responses from the LLM,
including diagnostic questions, answer evaluations, strategy selection,
and teaching strategy responses.
"""

import json
from typing import Dict, Any, List, Optional, Union
import re


class ParseError(Exception):
    """Custom exception for parsing errors."""
    pass


def parse_diagnostic_question(response: str) -> Dict[str, Any]:
    """
    Parse diagnostic question response from LLM.
    
    Expected JSON format:
    {
        "question": "your question here",
        "expected_level": 0.X,
        "reasoning": "why this question helps"
    }
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed diagnostic question data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        data = json.loads(response)
        
        # Validate required fields
        required_fields = ["question", "expected_level", "reasoning"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        # Validate types
        if not isinstance(data["question"], str):
            raise ParseError("Question must be a string")
        
        if not isinstance(data["expected_level"], (int, float)):
            raise ParseError("Expected level must be a number")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
        # Validate expected_level range
        if not 0.0 <= data["expected_level"] <= 1.0:
            raise ParseError("Expected level must be between 0.0 and 1.0")
        
        return data
        
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ParseError(f"Parsing error: {e}")


def parse_answer_evaluation(response: str) -> Dict[str, Any]:
    """
    Parse answer evaluation response from LLM.
    
    Expected JSON format:
    {
        "quality_score": 0.X,
        "reasoning": "detailed explanation",
        "strengths": ["list of strengths"],
        "weaknesses": ["list of weaknesses"],
        "level_indication": "beginner/intermediate/advanced"
    }
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed evaluation data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        cleaned = _extract_json_string(response)
        data = json.loads(cleaned)
        
        # Validate required fields
        required_fields = ["quality_score", "reasoning", "strengths", "weaknesses", "level_indication"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        # Validate types
        if not isinstance(data["quality_score"], (int, float)):
            raise ParseError("Quality score must be a number")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
        if not isinstance(data["strengths"], list):
            raise ParseError("Strengths must be a list")
        
        if not isinstance(data["weaknesses"], list):
            raise ParseError("Weaknesses must be a list")
        
        if not isinstance(data["level_indication"], str):
            raise ParseError("Level indication must be a string")
        
        # Validate quality_score range
        if not 0.0 <= data["quality_score"] <= 1.0:
            raise ParseError("Quality score must be between 0.0 and 1.0")
        
        # Validate level_indication values (case-insensitive, handle variations)
        valid_levels = ["beginner", "intermediate", "advanced"]
        level_lower = data["level_indication"].lower().strip()
        
        # Map common variations to valid levels
        level_mapping = {
            "beginner": "beginner",
            "novice": "beginner",
            "basic": "beginner",
            "elementary": "beginner",
            "intermediate": "intermediate",
            "medium": "intermediate",
            "moderate": "intermediate",
            "advanced": "advanced",
            "expert": "advanced",
            "proficient": "advanced"
        }
        
        # Normalize the level indication
        normalized_level = level_mapping.get(level_lower, level_lower)
        
        if normalized_level not in valid_levels:
            # If still not valid, default to intermediate
            normalized_level = "intermediate"
        
        data["level_indication"] = normalized_level
        
        return data
        
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ParseError(f"Parsing error: {e}")


def parse_strategy_selection(response: str) -> Dict[str, Any]:
    """
    Parse strategy selection response from LLM.
    
    Expected JSON format:
    {
        "chosen_strategy": "strategy_name",
        "reasoning": "detailed explanation",
        "confidence": 0.X
    }
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed strategy selection data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        cleaned = _extract_json_string(response)
        data = json.loads(cleaned)
        
        # Validate required fields
        required_fields = ["chosen_strategy", "reasoning", "confidence"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        # Validate types
        if not isinstance(data["chosen_strategy"], str):
            raise ParseError("Chosen strategy must be a string")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
        if not isinstance(data["confidence"], (int, float)):
            raise ParseError("Confidence must be a number")
        
        # Validate confidence range
        if not 0.0 <= data["confidence"] <= 1.0:
            raise ParseError("Confidence must be between 0.0 and 1.0")
        
        # Validate strategy name
        valid_strategies = ["direct_explanation", "socratic", "worked_example", "analogy", "visual"]
        if data["chosen_strategy"] not in valid_strategies:
            raise ParseError(f"Invalid strategy: {data['chosen_strategy']}. Must be one of: {valid_strategies}")
        
        return data
        
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ParseError(f"Parsing error: {e}")


def parse_teaching_response(response: str, strategy_name: str) -> Dict[str, Any]:
    """
    Parse teaching strategy response from LLM.
    
    Args:
        response: Raw LLM response string
        strategy_name: Name of the teaching strategy used
        
    Returns:
        Parsed teaching response data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        # Extract JSON from response (handles markdown code blocks)
        cleaned = _extract_json_string(response)
        data = json.loads(cleaned)
        
        # Validate based on strategy type
        if strategy_name == "direct_explanation":
            return _parse_direct_explanation(data)
        elif strategy_name == "socratic":
            return _parse_socratic(data)
        elif strategy_name == "worked_example":
            return _parse_worked_example(data)
        elif strategy_name == "analogy":
            return _parse_analogy(data)
        elif strategy_name == "visual":
            return _parse_visual(data)
        else:
            raise ParseError(f"Unknown strategy: {strategy_name}")
            
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ParseError(f"Parsing error: {e}")


def _parse_direct_explanation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse direct explanation response."""
    required_fields = ["explanation", "key_points", "assessment_question", "expected_answer", "reasoning"]
    
    for field in required_fields:
        if field not in data:
            raise ParseError(f"Missing required field: {field}")
    
    if not isinstance(data["key_points"], list):
        raise ParseError("Key points must be a list")
    
    return data


def _parse_socratic(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Socratic method response."""
    required_fields = ["questions", "question_sequence", "assessment_question", "expected_answer", "reasoning"]
    
    for field in required_fields:
        if field not in data:
            raise ParseError(f"Missing required field: {field}")
    
    if not isinstance(data["questions"], list):
        raise ParseError("Questions must be a list")
    
    if len(data["questions"]) < 3:
        raise ParseError("Must have at least 3 questions")
    
    return data


def _parse_worked_example(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse worked example response."""
    required_fields = ["problem_statement", "solution_steps", "final_answer", "assessment_question", "expected_answer", "reasoning"]
    
    for field in required_fields:
        if field not in data:
            raise ParseError(f"Missing required field: {field}")
    
    if not isinstance(data["solution_steps"], list):
        raise ParseError("Solution steps must be a list")
    
    # Validate solution steps structure
    for i, step in enumerate(data["solution_steps"]):
        if not isinstance(step, dict):
            raise ParseError(f"Solution step {i+1} must be a dictionary")
        
        step_required = ["step", "action", "explanation"]
        for field in step_required:
            if field not in step:
                raise ParseError(f"Solution step {i+1} missing field: {field}")
    
    return data


def _parse_analogy(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse analogy response."""
    required_fields = ["analogy_concept", "analogy_mapping", "explanation", "limitations", "assessment_question", "expected_answer", "reasoning"]
    
    for field in required_fields:
        if field not in data:
            raise ParseError(f"Missing required field: {field}")
    
    if not isinstance(data["analogy_mapping"], dict):
        raise ParseError("Analogy mapping must be a dictionary")
    
    return data


def _parse_visual(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse visual response."""
    required_fields = ["visual_type", "visual_description", "key_components", "connections", "assessment_question", "expected_answer", "reasoning"]
    
    for field in required_fields:
        if field not in data:
            raise ParseError(f"Missing required field: {field}")
    
    if not isinstance(data["key_components"], list):
        raise ParseError("Key components must be a list")
    
    # Validate key components structure
    for i, component in enumerate(data["key_components"]):
        if not isinstance(component, dict):
            raise ParseError(f"Key component {i+1} must be a dictionary")
        
        component_required = ["component", "position", "purpose"]
        for field in component_required:
            if field not in component:
                raise ParseError(f"Key component {i+1} missing field: {field}")
    
    return data


def parse_practice_question(response: str) -> Dict[str, Any]:
    """
    Parse practice question response from LLM.
    
    Expected JSON format:
    {
        "question": "Practice question text",
        "expected_answer": "What a good answer should include",
        "difficulty": 0.X,
        "hints": ["optional hint 1", "optional hint 2"],
        "reasoning": "Why this question helps the student practice"
    }
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed practice question data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        cleaned = _extract_json_string(response)
        data = json.loads(cleaned)
        

        required_fields = ["question", "expected_answer", "difficulty"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        

        if not isinstance(data["question"], str):
            raise ParseError("Question must be a string")
        
        if not isinstance(data["expected_answer"], str):
            raise ParseError("Expected answer must be a string")
        
        if not isinstance(data["difficulty"], (int, float)):
            raise ParseError("Difficulty must be a number")
        
        # Validate difficulty range
        if not 0.0 <= data["difficulty"] <= 1.0:
            raise ParseError("Difficulty must be between 0.0 and 1.0")
        
        # Validate hints if present
        if "hints" in data and not isinstance(data["hints"], list):
            raise ParseError("Hints must be a list")
        
        # Validate reasoning if present
        if "reasoning" in data and not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
        return data
        
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ParseError(f"Parsing error: {e}")


def parse_meta_reasoner_decision(response: str) -> Dict[str, Any]:
    """
    Parse meta-reasoner decision response from LLM.
    
    Expected JSON format:
    {
        "next_action": "continue|end_success|end_max_attempts|end_stuck|prerequisite",
        "goal_achieved": true/false,
        "needs_prerequisite": true/false,
        "prerequisite_topic": "topic name or empty string",
        "reasoning": "detailed explanation",
        "confidence": 0.X
    }
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed meta-reasoner decision data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        cleaned = _extract_json_string(response)
        data = json.loads(cleaned)
        
        # Validate required fields
        required_fields = ["next_action", "goal_achieved", "needs_prerequisite", "reasoning"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        # Validate types
        if not isinstance(data["next_action"], str):
            raise ParseError("Next action must be a string")
        
        if not isinstance(data["goal_achieved"], bool):
            raise ParseError("Goal achieved must be a boolean")
        
        if not isinstance(data["needs_prerequisite"], bool):
            raise ParseError("Needs prerequisite must be a boolean")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
        # Validate next_action values
        valid_actions = ["continue", "end_success", "end_max_attempts", "end_stuck", "prerequisite"]
        if data["next_action"] not in valid_actions:
            raise ParseError(f"Next action must be one of: {valid_actions}")
        
        # Validate prerequisite_topic if needs_prerequisite is True
        if data["needs_prerequisite"]:
            if "prerequisite_topic" not in data:
                raise ParseError("Prerequisite topic required when needs_prerequisite is True")
            if not isinstance(data["prerequisite_topic"], str):
                raise ParseError("Prerequisite topic must be a string")
        else:
            # Set empty string if not needed
            data["prerequisite_topic"] = data.get("prerequisite_topic", "")
        
        # Validate confidence if present
        if "confidence" in data:
            if not isinstance(data["confidence"], (int, float)):
                raise ParseError("Confidence must be a number")
            if not 0.0 <= data["confidence"] <= 1.0:
                raise ParseError("Confidence must be between 0.0 and 1.0")
        else:
            data["confidence"] = 0.7  # Default confidence
        
        return data
        
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ParseError(f"Parsing error: {e}")


def safe_parse(response: str, parser_func, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely parse LLM response with fallback handling.
    
    Args:
        response: Raw LLM response string
        parser_func: Parser function to use
        *args, **kwargs: Arguments to pass to parser function
        
    Returns:
        Parsed data or fallback data if parsing fails
    """
    try:
        return parser_func(response, *args, **kwargs)
    except ParseError as e:
        print(f"⚠️  Parse error: {e}")
        return _get_fallback_data(parser_func.__name__)
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
        return _get_fallback_data(parser_func.__name__)


def _get_fallback_data(parser_name: str) -> Dict[str, Any]:
    """Get fallback data when parsing fails."""
    
    fallbacks = {
        "parse_diagnostic_question": {
            "question": "Can you explain the basic concept?",
            "expected_level": 0.5,
            "reasoning": "Fallback question due to parsing error"
        },
        "parse_answer_evaluation": {
            "quality_score": 0.5,
            "reasoning": "Fallback evaluation due to parsing error",
            "strengths": ["Attempted to answer"],
            "weaknesses": ["Unable to evaluate properly"],
            "level_indication": "intermediate"
        },
        "parse_strategy_selection": {
            "chosen_strategy": "direct_explanation",
            "reasoning": "Fallback to direct explanation due to parsing error",
            "confidence": 0.5
        },
        "parse_practice_question": {
            "question": "What did you learn from the explanation?",
            "expected_answer": "Student should demonstrate understanding",
            "difficulty": 0.5,
            "hints": [],
            "reasoning": "Fallback question due to parsing error"
        },
        "parse_meta_reasoner_decision": {
            "next_action": "continue",
            "goal_achieved": False,
            "needs_prerequisite": False,
            "prerequisite_topic": "",
            "reasoning": "Fallback decision: continue teaching",
            "confidence": 0.5
        }
    }
    
    return fallbacks.get(parser_name, {"error": "Unknown parser"})


def _extract_json_string(text: str) -> str:
    """Best-effort extraction of a JSON object string from arbitrary LLM text.
    Handles fenced code blocks and surrounding prose.
    """
    if not isinstance(text, str):
        raise ParseError("Response is not a string")

    stripped = text.strip()
    # If it's already valid JSON, return early
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    # Handle fenced code blocks ```json ... ``` or ``` ... ```
    if "```" in stripped:
        parts = stripped.split("```")
        # Look through code blocks (odd indices) to find JSON-looking content
        for i in range(1, len(parts), 2):
            block = parts[i]
            # Remove an optional language tag like 'json' at the start of the block
            block = re.sub(r"^\s*json\s*\n", "", block, flags=re.IGNORECASE)
            candidate = block.strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

    # Fallback: find the first {...} span heuristically
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start:end + 1].strip()
        return candidate

    # Nothing JSON-like found
    return stripped


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_parsers():
    """Test all parsers with sample data."""
    
    print("="*70)
    print("🧪 TESTING JSON PARSERS")
    print("="*70)
    
    # Test diagnostic question parser
    print("\n1. Testing Diagnostic Question Parser:")
    diagnostic_response = '''
    {
        "question": "What is the time complexity of binary search?",
        "expected_level": 0.6,
        "reasoning": "This tests understanding of algorithmic complexity"
    }
    '''
    
    try:
        result = parse_diagnostic_question(diagnostic_response)
        print(f"✅ Success: {result['question']}")
    except ParseError as e:
        print(f"❌ Error: {e}")
    
    # Test answer evaluation parser
    print("\n2. Testing Answer Evaluation Parser:")
    evaluation_response = '''
    {
        "quality_score": 0.8,
        "reasoning": "Good understanding shown",
        "strengths": ["Correct concept", "Clear explanation"],
        "weaknesses": ["Missing edge cases"],
        "level_indication": "intermediate"
    }
    '''
    
    try:
        result = parse_answer_evaluation(evaluation_response)
        print(f"✅ Success: Score {result['quality_score']}")
    except ParseError as e:
        print(f"❌ Error: {e}")
    
    # Test strategy selection parser
    print("\n3. Testing Strategy Selection Parser:")
    strategy_response = '''
    {
        "chosen_strategy": "socratic",
        "reasoning": "Student needs guided discovery",
        "confidence": 0.8
    }
    '''
    
    try:
        result = parse_strategy_selection(strategy_response)
        print(f"✅ Success: {result['chosen_strategy']}")
    except ParseError as e:
        print(f"❌ Error: {e}")
    
    # Test teaching response parser
    print("\n4. Testing Teaching Response Parser:")
    teaching_response = '''
    {
        "explanation": "Binary search is a divide and conquer algorithm",
        "key_points": ["Divide array", "Compare middle", "Recurse"],
        "assessment_question": "How does binary search work?",
        "expected_answer": "Student should explain the divide and conquer approach",
        "reasoning": "Direct explanation works well for algorithmic concepts"
    }
    '''
    
    try:
        result = parse_teaching_response(teaching_response, "direct_explanation")
        print(f"✅ Success: {len(result['key_points'])} key points")
    except ParseError as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎉 Parser testing completed!")


if __name__ == "__main__":
    test_parsers()

import json
from typing import Dict, Any
import re


class ParseError(Exception):
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
        
        required_fields = ["question", "expected_level", "reasoning"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        if not isinstance(data["question"], str):
            raise ParseError("Question must be a string")
        
        if not isinstance(data["expected_level"], (int, float)):
            raise ParseError("Expected level must be a number")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
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
        
        required_fields = ["quality_score", "reasoning", "strengths", "weaknesses", "level_indication"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
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
        
        if not 0.0 <= data["quality_score"] <= 1.0:
            raise ParseError("Quality score must be between 0.0 and 1.0")
        
        valid_levels = ["beginner", "intermediate", "advanced"]
        level_lower = data["level_indication"].lower().strip()
        
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
        
        normalized_level = level_mapping.get(level_lower, level_lower)
        
        if normalized_level not in valid_levels:
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
        
        required_fields = ["chosen_strategy", "reasoning", "confidence"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        if not isinstance(data["chosen_strategy"], str):
            raise ParseError("Chosen strategy must be a string")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")
        
        if not isinstance(data["confidence"], (int, float)):
            raise ParseError("Confidence must be a number")
        
        if not 0.0 <= data["confidence"] <= 1.0:
            raise ParseError("Confidence must be between 0.0 and 1.0")
        
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
        cleaned = _extract_json_string(response)
        data = json.loads(cleaned)
        
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
        
        if not 0.0 <= data["difficulty"] <= 1.0:
            raise ParseError("Difficulty must be between 0.0 and 1.0")
        
        if "hints" in data and not isinstance(data["hints"], list):
            raise ParseError("Hints must be a list")
        
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
        
        required_fields = ["next_action", "goal_achieved", "needs_prerequisite", "reasoning"]
        for field in required_fields:
            if field not in data:
                raise ParseError(f"Missing required field: {field}")
        
        if not isinstance(data["next_action"], str):
            raise ParseError("Next action must be a string")
        
        if not isinstance(data["goal_achieved"], bool):
            raise ParseError("Goal achieved must be a boolean")
        
        if not isinstance(data["needs_prerequisite"], bool):
            raise ParseError("Needs prerequisite must be a boolean")
        
        if not isinstance(data["reasoning"], str):
            raise ParseError("Reasoning must be a string")

        valid_actions = ["continue", "end_success", "end_max_attempts", "end_stuck", "prerequisite"]
        if data["next_action"] not in valid_actions:
            raise ParseError(f"Next action must be one of: {valid_actions}")
        
        if data["needs_prerequisite"]:
            if "prerequisite_topic" not in data:
                raise ParseError("Prerequisite topic required when needs_prerequisite is True")
            if not isinstance(data["prerequisite_topic"], str):
                raise ParseError("Prerequisite topic must be a string")
        else:
            data["prerequisite_topic"] = data.get("prerequisite_topic", "")
        
        if "confidence" in data:
            if not isinstance(data["confidence"], (int, float)):
                raise ParseError("Confidence must be a number")
            if not 0.0 <= data["confidence"] <= 1.0:
                raise ParseError("Confidence must be between 0.0 and 1.0")
        else:
            data["confidence"] = 0.7
        
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
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    if "```" in stripped:
        parts = stripped.split("```")
        for i in range(1, len(parts), 2):
            block = parts[i]
            block = re.sub(r"^\s*json\s*\n", "", block, flags=re.IGNORECASE)
            candidate = block.strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start:end + 1].strip()
        return candidate

    return stripped

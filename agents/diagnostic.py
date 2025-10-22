import json
import re
from typing import Any

from pydantic import BaseModel, Field

from core.state import AgentState
from config.prompts import DIAGNOTIC_PROMPT, ANSWER_EVALUATION_PROMPT
from tools.llm import LLM
from utils.log_utils import logger


MIN_DIAGNOSTIC_CONFIDENCE = 0.8
MAX_DIAGNOSTIC_QUESTIONS = 5
CONFIDENCE_INCREMENT = 0.1


class DiagnosticQuestion(BaseModel):
    question: str = Field(description="The diagnostic question")
    expected_level: float = Field(description="The expected difficulty level (0.0 to 1.0)")
    reasoning: str = Field(description="Explanation for why this question helps determine the user's level")


class AnswerEvaluation(BaseModel):
    quality_score: float = Field(description="Quality score from 0.0 to 1.0")
    reasoning: str = Field(description="Detailed explanation of the evaluation")
    strengths: list[str] = Field(description="List of what the student did well")
    weaknesses: list[str] = Field(description="List of areas for improvement")
    level_indication: str = Field(description="Level indication: beginner/intermediate/advanced")


class DiagnosticQuestionParser:
    def __init__(self, pydantic_object: Any):
        self.pydantic_object = pydantic_object

    def parse(self, text: str) -> DiagnosticQuestion:
        cleaned_text = re.sub(r"```json\s*", "", text)
        cleaned_text = re.sub(r"\s*```", "", cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        try:
            json_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse diagnostic question: {cleaned_text}")
            return None

        try:
            return DiagnosticQuestion.model_validate(json_data)
        except Exception as e:
            logger.error(f"Error converting to DiagnosticQuestion object: {e}")
            return None


class AnswerEvaluationParser:
    def __init__(self, pydantic_object: Any):
        self.pydantic_object = pydantic_object

    def parse(self, text: str) -> AnswerEvaluation:
        cleaned_text = re.sub(r"```json\s*", "", text)
        cleaned_text = re.sub(r"\s*```", "", cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        try:
            json_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse answer evaluation: {cleaned_text}")
            return None

        try:
            return AnswerEvaluation.model_validate(json_data)
        except Exception as e:
            logger.error(f"Error converting to AnswerEvaluation object: {e}")
            return None

def evaluate_answer_quality(question: str, user_answer: str, expected_level: float, topic: str) -> dict:
    """
    Evaluate the quality of a user's answer using LLM assessment.
    
    Args:
        question: The diagnostic question asked
        user_answer: The user's response
        expected_level: The expected difficulty level of the question
        topic: The topic being assessed
        
    Returns:
        Dictionary with quality_score, reasoning, strengths, weaknesses, level_indication
    """
    llm = LLM()
    parser = AnswerEvaluationParser(pydantic_object=AnswerEvaluation)
    
    try:
        evaluation_response = llm.invoke(ANSWER_EVALUATION_PROMPT.format(
            topic=topic,
            question=question,
            expected_level=expected_level,
            user_answer=user_answer
        ))
        
        evaluation_obj = parser.parse(evaluation_response)
        
        if evaluation_obj is None:
            logger.error("Failed to parse answer evaluation from LLM response")
            return {
                "quality_score": 0.5,  # Neutral score
                "reasoning": "Error in evaluation parsing, using neutral score",
                "strengths": [],
                "weaknesses": ["Evaluation parsing error occurred"],
                "level_indication": "unknown"
            }
        
        evaluation_data = {
            "quality_score": evaluation_obj.quality_score,
            "reasoning": evaluation_obj.reasoning,
            "strengths": evaluation_obj.strengths,
            "weaknesses": evaluation_obj.weaknesses,
            "level_indication": evaluation_obj.level_indication
        }
        
        logger.info(f"Answer evaluation: {evaluation_data['quality_score']:.2f}")
        logger.info(f"Reasoning: {evaluation_data['reasoning']}")
        
        return evaluation_data
        
    except Exception as e:
        logger.error(f"Error evaluating answer: {e}")

        return {
            "quality_score": 0.5,  # Neutral score
            "reasoning": "Error in evaluation, using neutral score",
            "strengths": [],
            "weaknesses": ["Evaluation error occurred"],
            "level_indication": "unknown"
        }

#gpt logic
def calculate_level_adjustment(answer_quality: float, expected_level: float, current_estimated_level: float) -> float:
    """
    Calculate how much to adjust the estimated level based on answer quality.
    
    Args:
        answer_quality: Score from 0.0 to 1.0 indicating answer quality
        expected_level: The difficulty level the question was designed for
        current_estimated_level: Current estimated user level
        
    Returns:
        Adjustment value (positive = increase level, negative = decrease level)
    """
    # Base adjustment based on how well they answered
    # If they answered well (quality > 0.7), increase level
    # If they answered poorly (quality < 0.3), decrease level
    
    if answer_quality >= 0.8:
        # Excellent answer - significant positive adjustment
        adjustment = 0.15
    elif answer_quality >= 0.6:
        # Good answer - moderate positive adjustment
        adjustment = 0.08
    elif answer_quality >= 0.4:
        # Average answer - small adjustment based on expected level
        if expected_level > current_estimated_level:
            # They struggled with a harder question
            adjustment = -0.05
        else:
            # They did okay with an easier question
            adjustment = 0.02
    elif answer_quality >= 0.2:
        # Poor answer - moderate negative adjustment
        adjustment = -0.10
    else:
        # Very poor answer - significant negative adjustment
        adjustment = -0.20
    
    # Adjust based on how the expected level compares to current estimate
    level_difference = expected_level - current_estimated_level
    
    if level_difference > 0.2:
        # Question was much harder than estimated level
        # If they did well, give bigger boost; if poorly, smaller penalty
        if answer_quality > 0.6:
            adjustment *= 1.5  # Bigger boost for handling harder question
        else:
            adjustment *= 0.5  # Smaller penalty for struggling with harder question
    elif level_difference < -0.2:
        # Question was much easier than estimated level
        # If they did poorly, bigger penalty; if well, smaller boost
        if answer_quality < 0.4:
            adjustment *= 1.5  # Bigger penalty for struggling with easier question
        else:
            adjustment *= 0.5  # Smaller boost for handling easier question
    
    # Cap the adjustment to prevent wild swings
    adjustment = max(-0.25, min(0.25, adjustment))
    
    logger.info(f"Level adjustment: {adjustment:.3f} (quality: {answer_quality:.2f}, expected: {expected_level:.2f})")
    
    return adjustment


def adaptive_diagnostic_node(state: AgentState):

    logger.info(f"Adaptive diagnostic node called with state")

    confidence = state.get("diagnostic_confidence", 0.0)
    questions = state.get("diagnostic_questions", [])
    answers = state.get("diagnostic_answers", [])
    estimated_level = state.get("estimated_level", 0.2)

    topic = state["topic"]
    
    num_questions = len(questions)

    logger.info(f"Number of questions: {num_questions}")
    logger.info(f"Estimated level: {estimated_level}")
    logger.info(f"Topic: {topic}")

    if confidence >= MIN_DIAGNOSTIC_CONFIDENCE:
        decision = (
            f"Diagnostic complete: {num_questions} questions asked, "
            f"confidence {confidence:.2f}"
        )

        return {
            "decision_log": state["decision_log"] + [decision],
        }


    if num_questions >= MAX_DIAGNOSTIC_QUESTIONS:
        decision = f"Max questions ({MAX_DIAGNOSTIC_QUESTIONS}) reached, forcing completion"
        
        return {
            "diagnostic_confidence": MIN_DIAGNOSTIC_CONFIDENCE,
            "decision_log": state.get("decision_log", []) + [decision]
        }
    
    logger.info(f"Generating diagnostic question {num_questions + 1}")
    
    llm = LLM()
    parser = DiagnosticQuestionParser(pydantic_object=DiagnosticQuestion)

    qa_history = "\n".join([
        f"Q{i+1}: {q}\nA{i+1}: {a}"
        for i, (q, a) in enumerate(zip(questions, answers))
    ]) if questions else "No previous questions"

    next_question = None
    expected_level = None
    reasoning = None

    try:
        diagnostic_response = llm.invoke(DIAGNOTIC_PROMPT.format(
            topic=topic,
            estimated_level=estimated_level,
            confidence=confidence,
            num_questions=num_questions,
            qa_history=qa_history
        ))

        diagnostic_question_obj = parser.parse(diagnostic_response)
        
        if diagnostic_question_obj is None:
            logger.error("Failed to parse diagnostic question from LLM response")
            next_question = f"Explain the basic concept of {topic}."
            expected_level = estimated_level
            reasoning = "Fallback question due to parsing error"
        else:
            next_question = diagnostic_question_obj.question
            expected_level = diagnostic_question_obj.expected_level
            reasoning = diagnostic_question_obj.reasoning

        logger.info(f"Generated: {next_question}")
        logger.info(f"Expected level: {expected_level:.1f}")
        logger.info(f"Reasoning: {reasoning}")
        
    except Exception as e:
        logger.error(f"Error generating diagnostic question: {e}")

        next_question = f"Explain the basic concept of {topic}."
        expected_level = estimated_level
        reasoning = "Fallback question due to error"


    if next_question is None:
        logger.error("No valid question generated, using fallback")
        next_question = f"Explain the basic concept of {topic}."
        expected_level = estimated_level
        reasoning = "Fallback question due to no valid question"

    new_questions = questions + [next_question]
    user_answer = input(f"Answer the question: {next_question}")
    new_answers = answers + [user_answer]
    
    answer_evaluation = evaluate_answer_quality(
        question=next_question,
        user_answer=user_answer,
        expected_level=expected_level,
        topic=topic
    )
    
    level_adjustment = calculate_level_adjustment(
        answer_quality=answer_evaluation["quality_score"],
        expected_level=expected_level,
        current_estimated_level=estimated_level
    )
    
    new_estimated_level = max(0.0, min(1.0, estimated_level + level_adjustment))
    new_confidence = min(1.0, confidence + CONFIDENCE_INCREMENT)
    
    decision = f"Q{len(new_questions)}: {next_question[:60]}..."
    if reasoning:
        decision += f" | Reasoning: {reasoning}"
    
    decision += f" | Answer Quality: {answer_evaluation['quality_score']:.2f}"
    decision += f" | Level: {estimated_level:.2f} → {new_estimated_level:.2f} (Δ{level_adjustment:+.3f})"
    
    logger.info(f"\nState updates:")
    logger.info(f"  - New confidence: {new_confidence:.2f}")
    logger.info(f"  - Total questions: {len(new_questions)}")
    logger.info(f"  - Level adjustment: {level_adjustment:+.3f}")
    logger.info(f"  - New estimated level: {new_estimated_level:.2f}")
    logger.info(f"  - Answer quality: {answer_evaluation['quality_score']:.2f}")
    
    updates = {
        "diagnostic_questions": new_questions,
        "diagnostic_answers": new_answers,
        "diagnostic_confidence": new_confidence,
        "estimated_level": new_estimated_level,
        "decision_log": state.get("decision_log", []) + [decision]
    }
    
    return updates








    


    
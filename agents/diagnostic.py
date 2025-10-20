import json

from core.state import AgentState
from config.prompts import DIAGNOTIC_PROMPT
from tools.llm import LLM
from utils.log_utils import logger


MIN_DIAGNOSTIC_CONFIDENCE = 0.8
MAX_DIAGNOSTIC_QUESTIONS = 5
CONFIDENCE_INCREMENT = 0.1


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

    qa_history = "\n".join([
        f"Q{i+1}: {q}\nA{i+1}: {a}"
        for i, (q, a) in enumerate(zip(questions, answers))
    ]) if questions else "No previous questions"

    try:
        diagnostic_question = llm.invoke(DIAGNOTIC_PROMPT.format(
            topic=topic,
            estimated_level=estimated_level,
            confidence=confidence,
            num_questions=num_questions,
            qa_history=qa_history
        ))

        diagnostic_question_data = json.loads(diagnostic_question)
        next_question = diagnostic_question_data.get("question", "")
        expected_level = diagnostic_question_data.get("expected_level", estimated_level)
        reasoning = diagnostic_question_data.get("reasoning", "")

        logger.info(f"Generated: {next_question}")
        logger.info(f"Expected level: {expected_level:.1f}")
        logger.info(f"Reasoning: {reasoning}")
        
    except Exception as e:
        logger.error(f"Error generating diagnostic question: {e}")


    new_questions = questions + [next_question]
    new_answers = answers + [input(f"Answer the question: {next_question}")]
    

    new_confidence = min(1.0, confidence + CONFIDENCE_INCREMENT)
    
    new_estimated_level = estimated_level
    
    decision = f"Q{len(new_questions)}: {next_question[:60]}..."
    if reasoning:
        decision += f" | Reasoning: {reasoning}"
    
    logger.info(f"\nState updates:")
    logger.info(f"  - New confidence: {new_confidence:.2f}")
    logger.info(f"  - Total questions: {len(new_questions)}")
    
    updates = {
        "diagnostic_questions": new_questions,
        "diagnostic_answers": new_answers,
        "diagnostic_confidence": new_confidence,
        "estimated_level": new_estimated_level,
        "decision_log": state.get("decision_log", []) + [decision]
    }
    
    return updates








    


    
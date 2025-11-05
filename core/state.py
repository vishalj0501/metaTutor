from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Literal, Any
from pydantic import BaseModel, Field


class TeachingStrategy(TypedDict):
    name: str
    description: str
    effectiveness: float

class LearningSession(TypedDict):
    session_id: int
    topic: str
    strategy: str
    explanation: str
    question: str
    user_answer: str
    correct_answer: str
    feedback: str
    score: float 
    timestamp: str

class AgentState(TypedDict):
    # input 
    topic: str
    target_score: float 

    # diagnotics

    current_level: float
    current_confidence: float
    current_questions: List[str]
    current_answers: List[str]

    # goal

    learning_goal: str
    current_proficiency: float

    # strategy

    current_strategy: str
    available_strategies: List[TeachingStrategy]
    strategy_attempts: Dict[str, int]
    consecutive_failures: int
    target_proficiency: float

    # session history

    sessions: List[LearningSession]

    # teaching/practice state
    current_explanation: str  # Current teaching explanation
    current_question: str  # Current practice question
    current_correct_answer: str  # Expected answer for current question
    current_user_answer: str  # Student's answer to current question
    current_question_difficulty: float  # Difficulty level of current question
    current_teaching_data: Dict[str, Any]  # Full teaching data from teach_node
        
    # Meta-reasoning
    stuck_counter: int  # How many times tried without progress
    needs_prerequisite: bool
    prerequisite_topic: str
    
    # Agent decisions (audit trail)
    decision_log: List[str]
    
    # Control flow
    next_action: str  # What agent decided to do next
    goal_achieved: bool
    max_attempts: int
    current_attempt: int


def create_initial_state(topic: str) -> AgentState:
    """
    Create initial state for a new learning session.
    """
    return AgentState(
        topic=topic,
        target_score=0.8,
        current_level=0.0,
        current_confidence=0.0,
        current_questions=[],
        current_answers=[],
        learning_goal=f"Master {topic}",
        current_proficiency=0.0,
        current_strategy="",
        available_strategies=[],
        strategy_attempts={},
        consecutive_failures=0,
        target_proficiency=0.8,
        sessions=[],
        stuck_counter=0,
        needs_prerequisite=False,
        prerequisite_topic="",
        decision_log=[],
        next_action="diagnose",
        goal_achieved=False,
        max_attempts=10,
        current_attempt=0,
        current_explanation="",
        current_question="",
        current_correct_answer="",
        current_user_answer="",
        current_question_difficulty=0.5,
        current_teaching_data={}
    )








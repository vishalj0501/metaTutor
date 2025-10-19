from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Literal
from pydantic import BaseModel, Field


class TeachingStrategy(TypedDict):
    name: str
    description: str
    effectiveness_history: List[float]

class LearningSession(TypedDict):
    topic: str
    explanation: str
    question: str
    user_answer: str
    score: float 
    strategy_used: TeachingStrategy
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
    available_strategies: List[str]
    failed_strategies: List[str]

    # session history

    sessions: List[LearningSession]

        
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








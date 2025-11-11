"""
LangGraph Workflow Definition

This module defines the complete teaching agent workflow using LangGraph.
All nodes are connected with edges and conditional routing.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from core.state import AgentState
from agents.diagnostic import adaptive_diagnostic_node, MIN_DIAGNOSTIC_CONFIDENCE, MAX_DIAGNOSTIC_QUESTIONS
from agents.strategy_selector import strategy_selector_node
from agents.teach_node import teach_node
from agents.practice_node import practice_node
from agents.evaluate_node import evaluate_node
from agents.meta_reasoner_node import meta_reasoner_node


def diagnostic_phase_node(state: AgentState) -> Dict[str, Any]:
    """
    Wrapper node that handles the diagnostic loop internally.
    
    Calls adaptive_diagnostic_node repeatedly until diagnostic is complete
    (confidence >= threshold or max questions reached).
    
    Args:
        state: Current agent state
        
    Returns:
        State updates including diagnostic completion status
    """
    
    print("\n" + "="*60)
    print("🔍 DIAGNOSTIC PHASE NODE")
    print("="*60)
    
    # Create a working copy of state for the loop
    working_state = dict(state)
    
    # Check if diagnostic is already complete
    confidence = working_state.get("diagnostic_confidence", 0.0)
    num_questions = len(working_state.get("diagnostic_questions", []))
    
    if confidence >= MIN_DIAGNOSTIC_CONFIDENCE:
        print(f"\n✅ Diagnostic already complete (confidence: {confidence:.2f})")
        # Set initial proficiency based on diagnostic
        estimated_level = working_state.get("estimated_level", 0.2)
        return {
            "current_proficiency": estimated_level,
            "decision_log": working_state.get("decision_log", []) + [
                f"✅ Diagnostic phase complete: {num_questions} questions, confidence {confidence:.2f}"
            ]
        }
    
    # Run diagnostic loop until complete
    print(f"\n🔍 Running diagnostic assessment...")
    
    while confidence < MIN_DIAGNOSTIC_CONFIDENCE and num_questions < MAX_DIAGNOSTIC_QUESTIONS:
        updates = adaptive_diagnostic_node(working_state)
        working_state.update(updates)
        
        confidence = working_state.get("diagnostic_confidence", 0.0)
        num_questions = len(working_state.get("diagnostic_questions", []))
    
    # Diagnostic complete
    estimated_level = working_state.get("estimated_level", 0.2)
    
    print(f"\n✅ Diagnostic phase completed.")
    print(f"   Questions asked: {num_questions}")
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Estimated Level: {estimated_level:.2f}")
    
    # Return all diagnostic updates plus proficiency
    return {
        "diagnostic_confidence": working_state.get("diagnostic_confidence", 0.0),
        "diagnostic_questions": working_state.get("diagnostic_questions", []),
        "diagnostic_answers": working_state.get("diagnostic_answers", []),
        "estimated_level": estimated_level,
        "current_proficiency": estimated_level,
        "decision_log": working_state.get("decision_log", []) + [
            f"✅ Diagnostic complete: {num_questions} questions, confidence {confidence:.2f}, level {estimated_level:.2f}"
        ]
    }


def route_decision(state: AgentState) -> str:
    """
    Conditional routing function based on meta-reasoner decision.
    
    Routes to:
    - "strategy_selector" if next_action is "continue"
    - "end" for all other actions (end_success, end_max_attempts, end_stuck, prerequisite)
    
    Args:
        state: Current agent state
        
    Returns:
        String key that maps to next node or END
    """
    
    next_action = state.get("next_action", "continue")
    goal_achieved = state.get("goal_achieved", False)
    current_attempt = state.get("current_attempt", 0)
    max_attempts = state.get("max_attempts", 10)
    
    print(f"\n🔄 Routing Decision:")
    print(f"   Next Action: {next_action}")
    print(f"   Goal Achieved: {goal_achieved}")
    print(f"   Attempt: {current_attempt}/{max_attempts}")
    
    # Safety check: stop if max attempts reached, even if meta-reasoner says continue
    if current_attempt >= max_attempts:
        print(f"   ⚠️  Max attempts reached! Forcing end.")
        return "end"
    
    # Safety check: stop if goal achieved, even if meta-reasoner says continue
    if goal_achieved:
        print(f"   ✅ Goal achieved! Forcing end.")
        return "end"
    
    if next_action == "continue" and not goal_achieved:
        print(f"   → Routing to: strategy_selector (continue teaching)")
        return "strategy_selector"
    else:
        print(f"   → Routing to: END")
        return "end"


def build_teaching_graph():
    """
    Build and compile the complete teaching agent workflow graph.
    
    Graph Structure:
    START → diagnostic_phase → strategy_selector → teach → practice → evaluate → meta_reasoner → route_decision
                                                                                                        ↓
                                                                                    [continue → strategy_selector]
                                                                                    [end_* → END]
    
    Returns:
        Compiled LangGraph workflow
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("diagnostic_phase", diagnostic_phase_node)
    workflow.add_node("strategy_selector", strategy_selector_node)
    workflow.add_node("teach", teach_node)
    workflow.add_node("practice", practice_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("meta_reasoner", meta_reasoner_node)
    
    # Add edges
    workflow.set_entry_point("diagnostic_phase")
    workflow.add_edge("diagnostic_phase", "strategy_selector")
    workflow.add_edge("strategy_selector", "teach")
    workflow.add_edge("teach", "practice")
    workflow.add_edge("practice", "evaluate")
    workflow.add_edge("evaluate", "meta_reasoner")
    
    # Conditional routing from meta_reasoner
    workflow.add_conditional_edges(
        "meta_reasoner",
        route_decision,
        {
            "strategy_selector": "strategy_selector",  # Loop back for continue
            "end": END  # End for all other cases (end_success, end_max_attempts, end_stuck, prerequisite)
        }
    )
    
    # Compile graph
    app = workflow.compile()
    
    return app


def run_teaching_workflow(initial_state: AgentState) -> AgentState:
    """
    Run the complete teaching workflow using LangGraph.
    
    Args:
        initial_state: Initial state with topic and configuration
        
    Returns:
        Final state after workflow completion
    """
    
    graph = build_teaching_graph()
    
    # Run the workflow
    final_state = graph.invoke(initial_state)
    
    return final_state


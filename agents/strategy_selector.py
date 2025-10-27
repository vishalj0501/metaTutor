from typing import Dict, Any, List


from core.state import AgentState, LearningSession, TeachingStrategy
from agents.strategies import (
    get_viable_strategies,
    rank_strategies,
    get_strategy_selection_prompt
)
from agents.parsers import parse_strategy_selection
from tools.llm import get_llm


def strategy_selector_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent decides which teaching strategy to use next.
    
    AGENTIC BEHAVIORS:
    - Analyzes session history to see what's working
    - Considers strategy effectiveness scores
    - Notices patterns (e.g., "user keeps failing with direct")
    - Makes intelligent choice based on context
    - Updates attempt counters
    
    This is DYNAMIC TOOL SELECTION - the core of agentic behavior.
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with state updates
    """
    
    print("\n" + "="*60)
    print("STRATEGY SELECTOR NODE")
    print("="*60)
    

    available_strategies = state.get("available_strategies", [])
    strategy_attempts = state.get("strategy_attempts", {})
    sessions = state.get("sessions", [])
    stuck_counter = state.get("stuck_counter", 0)
    consecutive_failures = state.get("consecutive_failures", 0)
    current_proficiency = state.get("current_proficiency", 0.0)
    target_proficiency = state.get("target_proficiency", 0.8)
    
    print(f"\nCurrent context:")
    print(f"  - Available strategies: {len(available_strategies)}")
    print(f"  - Sessions completed: {len(sessions)}")
    print(f"  - Stuck counter: {stuck_counter}")
    print(f"  - Consecutive failures: {consecutive_failures}")
    print(f"  - Current proficiency: {current_proficiency:.2f}")
    

    viable_strategies = get_viable_strategies(
        available_strategies,
        strategy_attempts,
        max_attempts=2 
    )
    
    print(f"\nFiltering strategies:")
    print(f"  - Viable strategies: {len(viable_strategies)}")
    
    if not viable_strategies:
        # All strategies exhausted - reset
        print("All strategies exhausted - resetting attempts")
        
        decision = "Reset strategy attempts - trying fresh approach"
        
        return {
            "strategy_attempts": {s["name"]: 0 for s in available_strategies},
            "decision_log": state.get("decision_log", []) + [decision]
        }
    
    # Analyze Recent Performance
    
    # Get last 3 sessions
    recent_sessions = sessions[-3:] if len(sessions) >= 3 else sessions
    
    print(f"\nRecent performance:")
    for i, session in enumerate(recent_sessions, 1):
        print(f"  {i}. {session['strategy']:20s} - Score: {session['score']:.2f}")
    
    # Build context summary for LLM
    if recent_sessions:
        recent_summary = "\n".join([
            f"- Session {session['session_id']}: "
            f"Strategy '{session['strategy']}' → Score {session['score']:.2f}"
            for session in recent_sessions
        ])
    else:
        recent_summary = "No sessions yet (this is the first)"
    
    # Prepare Strategy Options
    
    # Rank strategies by effectiveness
    ranked_strategies = rank_strategies(viable_strategies, recent_sessions)
    
    strategies_desc = "\n".join([
        f"- {s['name']:20s} | "
        f"Effectiveness: {s['effectiveness']:.2f} | "
        f"Attempts: {strategy_attempts.get(s['name'], 0)} | "
        f"Description: {s['description'][:50]}..."
        for s in ranked_strategies
    ])
    
    print(f"\nStrategy options (ranked by effectiveness):")
    for s in ranked_strategies:
        print(f"  - {s['name']:20s} (eff: {s['effectiveness']:.2f})")
    
    # Agent Meta-Reasons About Strategy Choice
    
    print(f"\nAgent reasoning about strategy choice...")
    
    llm = get_llm(use_mock=False)
    
    prompt = get_strategy_selection_prompt(
        strategies_desc=strategies_desc,
        recent_summary=recent_summary,
        stuck_counter=stuck_counter,
        consecutive_failures=consecutive_failures,
        current_proficiency=current_proficiency,
        target_proficiency=target_proficiency,
        total_sessions=len(sessions)
    )
    
    try:
        response = llm.invoke(prompt)
        
        data = parse_strategy_selection(response)
        
        chosen_strategy = data["chosen_strategy"]
        reasoning = data["reasoning"]
        confidence = data.get("confidence", 0.7)
        
        print(f"\nAgent decision:")
        print(f"  Strategy: {chosen_strategy}")
        print(f"  Reasoning: {reasoning}")
        print(f"  Confidence: {confidence:.2f}")
        
    except Exception as e:
        print(f"\nError in meta-reasoning: {e}")
        print(f"  Falling back to highest effectiveness strategy")
        
        chosen_strategy = ranked_strategies[0]["name"]
        reasoning = f"Fallback: chose highest effectiveness strategy"
        confidence = 0.5
    
    # Validate Choice
    
    valid_strategy_names = [s["name"] for s in viable_strategies]
    
    if chosen_strategy not in valid_strategy_names:
        print(f"Chosen strategy '{chosen_strategy}' not viable")
        chosen_strategy = ranked_strategies[0]["name"]
        reasoning = f"Adjusted to viable strategy: {chosen_strategy}"
    
    # Update State
    
    new_attempts = strategy_attempts.copy()
    new_attempts[chosen_strategy] = new_attempts.get(chosen_strategy, 0) + 1
    
    decision = (
        f"🎯 Strategy: {chosen_strategy} "
        f"(attempt #{new_attempts[chosen_strategy]}) | "
        f"Reason: {reasoning}"
    )
    
    print(f"\nUpdating state:")
    print(f"  - Current strategy: {chosen_strategy}")
    print(f"  - Attempts: {new_attempts[chosen_strategy]}")
    
    updates = {
        "current_strategy": chosen_strategy,
        "strategy_attempts": new_attempts,
        "decision_log": state.get("decision_log", []) + [decision]
    }
    
    return updates


def analyze_strategy_pattern(sessions: List[LearningSession]) -> Dict[str, Any]:
    """
    Analyze session history to detect patterns.
    
    Returns insights like:
    - Which strategies are working
    - Which are failing
    - Is there a trend
    """
    
    if not sessions:
        return {
            "pattern": "no_data",
            "recommendation": "try_highest_effectiveness"
        }
    
    # Count successes per strategy
    strategy_performance = {}
    
    for session in sessions:
        strategy = session["strategy"]
        score = session["score"]
        
        if strategy not in strategy_performance:
            strategy_performance[strategy] = {"scores": [], "avg": 0.0}
        
        strategy_performance[strategy]["scores"].append(score)
    
    # Calculate averages
    for strategy, data in strategy_performance.items():
        data["avg"] = sum(data["scores"]) / len(data["scores"])
    
    # Find best and worst
    if strategy_performance:
        best_strategy = max(strategy_performance.items(), key=lambda x: x[1]["avg"])
        worst_strategy = min(strategy_performance.items(), key=lambda x: x[1]["avg"])
        
        return {
            "pattern": "data_available",
            "best_strategy": best_strategy[0],
            "best_avg": best_strategy[1]["avg"],
            "worst_strategy": worst_strategy[0],
            "worst_avg": worst_strategy[1]["avg"],
            "recommendation": f"favor_{best_strategy[0]}"
        }
    
    return {"pattern": "insufficient_data"}


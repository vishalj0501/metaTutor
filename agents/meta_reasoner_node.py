"""
Meta-Reasoner Node

This module implements the meta-reasoner node that analyzes learning progress
and makes intelligent decisions about what action to take next.
"""

from typing import Dict, Any

from core.state import AgentState
from config.parsers import parse_meta_reasoner_decision, safe_parse
from config.prompts import META_REASONER_PROMPT
from tools.llm import get_llm


def meta_reasoner_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyze learning progress and decide next action.
    
    This node:
    1. Analyzes current state (proficiency, attempts, failures, trends)
    2. Calls LLM for intelligent decision-making
    3. Parses decision response
    4. Updates state with decision
    
    Possible decisions:
    - continue: Keep teaching
    - end_success: Goal achieved
    - end_max_attempts: Max attempts reached
    - end_stuck: Student stuck
    - prerequisite: Need prerequisite topic
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with state updates (next_action, goal_achieved, etc.)
    """
    
    print("\n" + "="*60)
    print("🧠 META-REASONER NODE")
    print("="*60)
    
    # ===== STEP 1: Extract Context =====
    
    topic = state.get("topic", "Unknown Topic")
    learning_goal = state.get("learning_goal", f"Master {topic}")
    current_proficiency = state.get("current_proficiency", 0.0)
    target_proficiency = state.get("target_proficiency", 0.8)
    current_attempt = state.get("current_attempt", 0)
    max_attempts = state.get("max_attempts", 10)
    consecutive_failures = state.get("consecutive_failures", 0)
    stuck_counter = state.get("stuck_counter", 0)
    sessions = state.get("sessions", [])
    total_sessions = len(sessions)
    
    print(f"\n📊 Current State:")
    print(f"   Topic: {topic}")
    print(f"   Current Proficiency: {current_proficiency:.2f}")
    print(f"   Target Proficiency: {target_proficiency:.2f}")
    print(f"   Progress: {(current_proficiency/target_proficiency)*100:.1f}%")
    print(f"   Attempt: {current_attempt}/{max_attempts}")
    print(f"   Consecutive Failures: {consecutive_failures}")
    print(f"   Stuck Counter: {stuck_counter}")
    print(f"   Total Sessions: {total_sessions}")
    
    # ===== STEP 2: Build Context Summary =====
    
    # Calculate progress percentage
    progress_percentage = (current_proficiency / target_proficiency * 100) if target_proficiency > 0 else 0.0
    
    # Analyze recent performance (last 3-5 sessions)
    recent_sessions = sessions[-5:] if len(sessions) >= 5 else sessions
    recent_summary = _build_recent_summary(recent_sessions)
    
    # Calculate average recent score
    if recent_sessions:
        avg_recent_score = sum(s["score"] for s in recent_sessions) / len(recent_sessions)
    else:
        avg_recent_score = 0.5
    
    # Determine trend
    trend = _calculate_trend(recent_sessions)
    
    # Calculate progress rate (proficiency gain per attempt)
    if total_sessions > 0:
        # Use estimated_level from diagnostic as initial, or 0.0 if not available
        initial_proficiency = state.get("estimated_level", 0.0)
        if total_sessions == 1:
            # First session, use estimated_level as baseline
            progress_rate = (current_proficiency - initial_proficiency) / 1.0
        else:
            # Multiple sessions, calculate average gain per session
            progress_rate = (current_proficiency - initial_proficiency) / total_sessions
    else:
        progress_rate = 0.0
    
    print(f"\n📈 Performance Analysis:")
    print(f"   Average Recent Score: {avg_recent_score:.2f}")
    print(f"   Trend: {trend}")
    print(f"   Progress Rate: {progress_rate:.3f} per session")
    
    # ===== STEP 3: Call LLM for Decision =====
    
    print(f"\n🤖 Meta-reasoning about next action...")
    
    prompt = META_REASONER_PROMPT.format(
        topic=topic,
        learning_goal=learning_goal,
        current_proficiency=current_proficiency,
        target_proficiency=target_proficiency,
        progress_percentage=progress_percentage,
        current_attempt=current_attempt,
        max_attempts=max_attempts,
        consecutive_failures=consecutive_failures,
        stuck_counter=stuck_counter,
        total_sessions=total_sessions,
        recent_summary=recent_summary,
        avg_recent_score=avg_recent_score,
        trend=trend,
        progress_rate=progress_rate
    )
    
    # Call LLM
    llm = get_llm(use_mock=False)
    response = llm.invoke(prompt)
    
    # Handle response format
    if hasattr(response, 'content'):
        response_text = response.content
    else:
        response_text = str(response)
    
    print(f"✅ LLM response received")
    
    # ===== STEP 4: Parse Decision Response =====
    
    print(f"\n🔍 Parsing meta-reasoner decision...")
    
    try:
        decision_data = parse_meta_reasoner_decision(response_text)
        print(f"✅ Successfully parsed decision")
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        print(f"   Using fallback decision")
        
        # Use safe parser with fallback
        decision_data = safe_parse(response_text, parse_meta_reasoner_decision)
    
    next_action = decision_data["next_action"]
    goal_achieved = decision_data["goal_achieved"]
    needs_prerequisite = decision_data["needs_prerequisite"]
    prerequisite_topic = decision_data.get("prerequisite_topic", "")
    reasoning = decision_data["reasoning"]
    confidence = decision_data.get("confidence", 0.7)
    
    # ===== STEP 5: Display Decision =====
    
    print(f"\n🎯 Meta-Reasoner Decision:")
    print(f"   Next Action: {next_action}")
    print(f"   Goal Achieved: {goal_achieved}")
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Reasoning: {reasoning}")
    
    if needs_prerequisite and prerequisite_topic:
        print(f"\n   📚 Prerequisite Needed: {prerequisite_topic}")
    
    # ===== STEP 6: Update State =====
    
    decision = (
        f"🧠 Meta-Reasoner: {next_action.upper()} | "
        f"Goal: {'✅' if goal_achieved else '⏳'} | "
        f"Reason: {reasoning[:60]}..."
    )
    
    updates = {
        "next_action": next_action,
        "goal_achieved": goal_achieved,
        "needs_prerequisite": needs_prerequisite,
        "prerequisite_topic": prerequisite_topic,
        "decision_log": state.get("decision_log", []) + [decision]
    }
    
    return updates


def _build_recent_summary(recent_sessions: list) -> str:
    """Build a summary of recent session performance."""
    
    if not recent_sessions:
        return "No sessions yet"
    
    summary_parts = []
    for i, session in enumerate(recent_sessions, 1):
        session_num = session.get("session_id", i)
        strategy = session.get("strategy", "unknown")
        score = session.get("score", 0.0)
        summary_parts.append(
            f"Session {session_num}: {strategy} → Score {score:.2f}"
        )
    
    return "\n".join(summary_parts)


def _calculate_trend(recent_sessions: list) -> str:
    """Calculate performance trend from recent sessions."""
    
    if len(recent_sessions) < 2:
        return "insufficient_data"
    
    scores = [s.get("score", 0.0) for s in recent_sessions]
    
    # Simple trend: compare first half to second half
    mid = len(scores) // 2
    first_half_avg = sum(scores[:mid]) / len(scores[:mid])
    second_half_avg = sum(scores[mid:]) / len(scores[mid:])
    
    diff = second_half_avg - first_half_avg
    
    if diff > 0.1:
        return "improving"
    elif diff < -0.1:
        return "declining"
    else:
        return "stable"



from typing import List, Dict, Any
import json
from datetime import datetime

from core.state import TeachingStrategy
from config.prompts import STRATEGY_PROMPTS, STRATEGY_SELECTION_PROMPT


def get_default_strategies() -> List[TeachingStrategy]:
    """
    Returns the 5 core teaching strategies available to the agent.
    
    Each strategy starts with 0.7 effectiveness (neutral assumption).
    As the agent uses them, effectiveness updates based on actual results.
    """
    
    return [
        TeachingStrategy(
            name="direct_explanation",
            description=(
                "Provide clear, structured explanation with definitions and key concepts. "
                "Best for logical, analytical learners."
            ),
            effectiveness=0.7  # Initial neutral score
        ),
        
        TeachingStrategy(
            name="socratic",
            description=(
                "Guide understanding through thought-provoking questions. "
                "Let student discover concepts rather than telling directly. "
                "Best for discovery-oriented learners."
            ),
            effectiveness=0.7
        ),
        
        TeachingStrategy(
            name="worked_example",
            description=(
                "Demonstrate step-by-step problem solving with concrete example. "
                "Show the process, not just the result. "
                "Best for visual and procedural learners."
            ),
            effectiveness=0.7
        ),
        
        TeachingStrategy(
            name="analogy",
            description=(
                "Explain using relatable real-world analogies and metaphors. "
                "Connect abstract concepts to familiar experiences. "
                "Best for abstract thinkers."
            ),
            effectiveness=0.7
        ),
        
        TeachingStrategy(
            name="visual",
            description=(
                "Use diagrams, flowcharts, or visual representations. "
                "Describe spatial relationships and structures. "
                "Best for visual learners."
            ),
            effectiveness=0.7
        ),
    ]



def update_strategy_effectiveness(
    strategies: List[TeachingStrategy],
    strategy_name: str,
    score: float,
    learning_rate: float = 0.3
) -> List[TeachingStrategy]:
    """
    Update a strategy's effectiveness based on session score.
    
    Uses exponential moving average to track effectiveness over time.
    
    Args:
        strategies: List of all strategies
        strategy_name: Which strategy to update
        score: Score from session (0.0 to 1.0)
        learning_rate: How much to weight new score (0.0 to 1.0)
            - Higher = more reactive to recent results
            - Lower = more stable, considers long history
    
    Returns:
        Updated strategies list
    
    Example:
        Old effectiveness: 0.7
        New score: 0.9
        Learning rate: 0.3
        New effectiveness: (0.7 * 0.7) + (0.9 * 0.3) = 0.49 + 0.27 = 0.76
    """
    
    updated_strategies = []
    
    for strategy in strategies:
        if strategy["name"] == strategy_name:
            # Update this strategy's effectiveness
            old_effectiveness = strategy["effectiveness"]
            new_effectiveness = (
                (old_effectiveness * (1 - learning_rate)) + 
                (score * learning_rate)
            )
            
            # Clamp between 0.0 and 1.0
            new_effectiveness = max(0.0, min(1.0, new_effectiveness))
            
            updated_strategy = strategy.copy()
            updated_strategy["effectiveness"] = new_effectiveness
            updated_strategies.append(updated_strategy)
        else:
            # Keep other strategies unchanged
            updated_strategies.append(strategy)
    
    return updated_strategies


def get_viable_strategies(
    strategies: List[TeachingStrategy],
    strategy_attempts: Dict[str, int],
    max_attempts: int = 2
) -> List[TeachingStrategy]:
    """
    Filter out strategies that have been tried too many times without success.
    
    This prevents the agent from getting stuck trying the same failing strategy.
    
    Args:
        strategies: All available strategies
        strategy_attempts: How many times each has been tried
        max_attempts: Max times to try a strategy before filtering it out
    
    Returns:
        List of strategies that haven't been over-tried
    """
    
    viable = [
        s for s in strategies
        if strategy_attempts.get(s["name"], 0) < max_attempts
    ]
    
    # If all strategies exhausted, reset and return all
    if not viable:
        return strategies
    
    return viable


def rank_strategies(
    strategies: List[TeachingStrategy],
    recent_sessions: List[Dict]
) -> List[TeachingStrategy]:
    """
    Rank strategies by effectiveness, considering recent context.
    
    Args:
        strategies: All available strategies
        recent_sessions: Recent learning sessions
    
    Returns:
        Strategies sorted by effectiveness (highest first)
    """
    
    # ranking by effectiveness
    ranked = sorted(
        strategies,
        key=lambda s: s["effectiveness"],
        reverse=True  # Highest first
    )
    
    return ranked


def get_strategy_prompt(strategy_name: str, topic: str, student_level: float = 0.5) -> str:
    """
    Get the teaching prompt for a specific strategy using JSON format.
    
    Args:
        strategy_name: Name of strategy
        topic: What to teach
        student_level: Student's current proficiency level
    
    Returns:
        Formatted prompt for LLM
    """
    
    
    template = STRATEGY_PROMPTS.get(
        strategy_name,
        STRATEGY_PROMPTS["direct_explanation"]  # Default fallback
    )
    
    return template.format(topic=topic, student_level=student_level)


def get_strategy_selection_prompt(strategies_desc: str, recent_summary: str, 
                                  stuck_counter: int, consecutive_failures: int,
                                  current_proficiency: float, target_proficiency: float,
                                  total_sessions: int) -> str:
    """
    Get the strategy selection prompt.
    
    Args:
        strategies_desc: Description of available strategies
        recent_summary: Summary of recent sessions
        stuck_counter: How many attempts without progress
        consecutive_failures: Number of consecutive failures
        current_proficiency: Current student proficiency
        target_proficiency: Target proficiency level
        total_sessions: Total sessions completed
    
    Returns:
        Formatted strategy selection prompt
    """
    
    
    return STRATEGY_SELECTION_PROMPT.format(
        strategies_desc=strategies_desc,
        recent_summary=recent_summary,
        stuck_counter=stuck_counter,
        consecutive_failures=consecutive_failures,
        current_proficiency=current_proficiency,
        target_proficiency=target_proficiency,
        total_sessions=total_sessions
    )


if __name__ == "__main__":
    
    print("="*70)
    print("TESTING STRATEGY MANAGEMENT")
    print("="*70)
    
    # Get default strategies
    strategies = get_default_strategies()
    
    print(f"\n📚 Available Strategies ({len(strategies)}):")
    for s in strategies:
        print(f"\n  {s['name']}:")
        print(f"    {s['description'][:60]}...")
        print(f"    Initial effectiveness: {s['effectiveness']:.2f}")
    
    # Simulate some teaching sessions
    print("\n" + "="*70)
    print("SIMULATING SESSIONS")
    print("="*70)
    
    # Session 1: Direct explanation works well
    print("\n📖 Session 1: Using 'direct_explanation', score: 0.9")
    strategies = update_strategy_effectiveness(strategies, "direct_explanation", 0.9)
    
    direct_strat = [s for s in strategies if s["name"] == "direct_explanation"][0]
    print(f"   Updated effectiveness: {direct_strat['effectiveness']:.2f}")
    
    # Session 2: Socratic fails
    print("\n📖 Session 2: Using 'socratic', score: 0.3")
    strategies = update_strategy_effectiveness(strategies, "socratic", 0.3)
    
    socratic_strat = [s for s in strategies if s["name"] == "socratic"][0]
    print(f"   Updated effectiveness: {socratic_strat['effectiveness']:.2f}")
    
    # Rank strategies
    print("\n" + "="*70)
    print("RANKED STRATEGIES (by effectiveness)")
    print("="*70)
    
    ranked = rank_strategies(strategies, [])
    
    for i, s in enumerate(ranked, 1):
        print(f"  {i}. {s['name']:20s} - {s['effectiveness']:.2f}")


class StrategyEffectivenessTracker:
    """
    Advanced tracking system for strategy effectiveness.
    
    Features:
    - Session-by-session tracking
    - Performance analytics
    - Trend analysis
    - Context-aware effectiveness
    """
    
    def __init__(self):
        self.session_history: List[Dict[str, Any]] = []
        self.strategy_stats: Dict[str, Dict[str, Any]] = {}
    
    def record_session(self, strategy_name: str, score: float, topic: str, 
                      user_level: float, session_context: Dict[str, Any] = None):
        """
        Record a teaching session result.
        
        Args:
            strategy_name: Which strategy was used
            score: Session effectiveness score (0.0 to 1.0)
            topic: What was taught
            user_level: Student's proficiency level
            session_context: Additional context (difficulty, time, etc.)
        """
        
        session_record = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_name,
            "score": score,
            "topic": topic,
            "user_level": user_level,
            "context": session_context or {}
        }
        
        self.session_history.append(session_record)
        
        # Update strategy statistics
        if strategy_name not in self.strategy_stats:
            self.strategy_stats[strategy_name] = {
                "total_sessions": 0,
                "total_score": 0.0,
                "avg_score": 0.0,
                "best_score": 0.0,
                "worst_score": 1.0,
                "success_rate": 0.0,
                "recent_trend": [],
                "topic_performance": {},
                "level_performance": {}
            }
        
        stats = self.strategy_stats[strategy_name]
        stats["total_sessions"] += 1
        stats["total_score"] += score
        stats["avg_score"] = stats["total_score"] / stats["total_sessions"]
        stats["best_score"] = max(stats["best_score"], score)
        stats["worst_score"] = min(stats["worst_score"], score)
        
        # Track recent trend (last 5 sessions)
        stats["recent_trend"].append(score)
        if len(stats["recent_trend"]) > 5:
            stats["recent_trend"].pop(0)
        
        # Track topic-specific performance
        if topic not in stats["topic_performance"]:
            stats["topic_performance"][topic] = {"scores": [], "avg": 0.0}
        
        topic_stats = stats["topic_performance"][topic]
        topic_stats["scores"].append(score)
        topic_stats["avg"] = sum(topic_stats["scores"]) / len(topic_stats["scores"])
        
        # Track level-specific performance
        level_bucket = self._get_level_bucket(user_level)
        if level_bucket not in stats["level_performance"]:
            stats["level_performance"][level_bucket] = {"scores": [], "avg": 0.0}
        
        level_stats = stats["level_performance"][level_bucket]
        level_stats["scores"].append(score)
        level_stats["avg"] = sum(level_stats["scores"]) / len(level_stats["scores"])
        
        # Calculate success rate (scores >= 0.7)
        successful_sessions = sum(1 for s in self.session_history 
                                if s["strategy"] == strategy_name and s["score"] >= 0.7)
        stats["success_rate"] = successful_sessions / stats["total_sessions"]
    
    def _get_level_bucket(self, level: float) -> str:
        """Convert numeric level to bucket for analysis."""
        if level < 0.2:
            return "beginner"
        elif level < 0.5:
            return "intermediate"
        elif level < 0.8:
            return "advanced"
        else:
            return "expert"
    
    def get_strategy_effectiveness(self, strategy_name: str, context: Dict[str, Any] = None) -> float:
        """
        Get effectiveness score for a strategy, considering context.
        
        Args:
            strategy_name: Strategy to analyze
            context: Current context (topic, user_level, etc.)
        
        Returns:
            Effectiveness score (0.0 to 1.0)
        """
        
        if strategy_name not in self.strategy_stats:
            return 0.7  # Default neutral score
        
        stats = self.strategy_stats[strategy_name]
        base_effectiveness = stats["avg_score"]
        
        # Context adjustments
        if context:
            # Topic-specific adjustment
            topic = context.get("topic")
            if topic and topic in stats["topic_performance"]:
                topic_avg = stats["topic_performance"][topic]["avg"]
                base_effectiveness = (base_effectiveness + topic_avg) / 2
            
            # Level-specific adjustment
            user_level = context.get("user_level", 0.5)
            level_bucket = self._get_level_bucket(user_level)
            if level_bucket in stats["level_performance"]:
                level_avg = stats["level_performance"][level_bucket]["avg"]
                base_effectiveness = (base_effectiveness + level_avg) / 2
        
        # Recent trend adjustment
        if stats["recent_trend"]:
            recent_avg = sum(stats["recent_trend"]) / len(stats["recent_trend"])
            # Weight recent performance more heavily
            base_effectiveness = (base_effectiveness * 0.7) + (recent_avg * 0.3)
        
        return max(0.0, min(1.0, base_effectiveness))
    
    def get_strategy_analytics(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a strategy.
        """
        
        if strategy_name not in self.strategy_stats:
            return {"error": "Strategy not found"}
        
        stats = self.strategy_stats[strategy_name]
        
        return {
            "strategy_name": strategy_name,
            "total_sessions": stats["total_sessions"],
            "avg_score": round(stats["avg_score"], 3),
            "best_score": stats["best_score"],
            "worst_score": stats["worst_score"],
            "success_rate": round(stats["success_rate"], 3),
            "recent_trend": [round(x, 3) for x in stats["recent_trend"]],
            "topic_performance": {
                topic: round(data["avg"], 3) 
                for topic, data in stats["topic_performance"].items()
            },
            "level_performance": {
                level: round(data["avg"], 3)
                for level, data in stats["level_performance"].items()
            }
        }
    
    def get_all_analytics(self) -> Dict[str, Any]:
        """
        Get analytics for all strategies.
        """
        
        return {
            strategy: self.get_strategy_analytics(strategy)
            for strategy in self.strategy_stats.keys()
        }
    
    def export_data(self, filename: str = None) -> str:
        """
        Export tracking data to JSON file.
        """
        
        if not filename:
            filename = f"strategy_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "session_history": self.session_history,
            "strategy_stats": self.strategy_stats,
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def load_data(self, filename: str):
        """
        Load tracking data from JSON file.
        """
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.session_history = data.get("session_history", [])
        self.strategy_stats = data.get("strategy_stats", {})


# Global tracker instance
effectiveness_tracker = StrategyEffectivenessTracker()


def track_session_effectiveness(strategy_name: str, score: float, topic: str, 
                               user_level: float, context: Dict[str, Any] = None):
    """
    Convenience function to track session effectiveness.
    """
    effectiveness_tracker.record_session(strategy_name, score, topic, user_level, context)


def get_contextual_effectiveness(strategies: List[TeachingStrategy], 
                                context: Dict[str, Any] = None) -> List[TeachingStrategy]:
    """
    Update strategy effectiveness scores based on current context.
    
    Args:
        strategies: List of strategies to update
        context: Current learning context
    
    Returns:
        Updated strategies with contextual effectiveness scores
    """
    
    updated_strategies = []
    
    for strategy in strategies:
        strategy_name = strategy["name"]
        contextual_score = effectiveness_tracker.get_strategy_effectiveness(strategy_name, context)
        
        updated_strategy = strategy.copy()
        updated_strategy["effectiveness"] = contextual_score
        updated_strategies.append(updated_strategy)
    
    return updated_strategies
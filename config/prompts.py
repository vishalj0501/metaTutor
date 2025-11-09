DIAGNOTIC_PROMPT = """

You are an adaptive diagnostic agent. Generate the NEXT diagnostic question.

Topic: {topic}
Current estimated level: {estimated_level:.1f}/1.0
Current confidence: {confidence:.1f}/1.0
Questions asked so far: {num_questions}

Previous Q&A:
{qa_history}

Generate ONE question that will help determine the user's level.
- If estimated_level is low (< 0.4), ask a basic/fundamental question
- If estimated_level is medium (0.4-0.7), ask an intermediate question  
- If estimated_level is high (> 0.7), ask an advanced question

Return JSON format:

{{
    "question": "your question here",
    "expected_level": 0.X,
    "reasoning": "why this question helps"
}}

"""

ANSWER_EVALUATION_PROMPT = """
You are an expert evaluator assessing a student's answer to a diagnostic question.

Topic: {topic}
Question: {question}
Expected Level: {expected_level:.1f}/1.0
Student Answer: {user_answer}

Evaluate the answer quality on a scale of 0.0 to 1.0 considering:
- Accuracy and correctness
- Depth of understanding shown
- Use of appropriate terminology
- Logical reasoning
- Completeness of response

Return JSON format:
{{
    "quality_score": 0.X,
    "reasoning": "detailed explanation of the evaluation",
    "strengths": ["list of what the student did well"],
    "weaknesses": ["list of areas for improvement"],
    "level_indication": "beginner/intermediate/advanced"
}}
"""

# ============================================================================
# STRATEGY TEACHING PROMPTS (JSON Format)
# ============================================================================

STRATEGY_PROMPTS = {
    "direct_explanation": """You are a teaching expert using the Direct Explanation strategy.

Topic: {topic}
Student Level: {student_level:.2f}/1.0

Provide a clear, structured explanation using the Direct Explanation approach.

Return JSON format:
{{
    "explanation": "Clear, structured explanation with definitions and key concepts",
    "key_points": ["list of 3-4 main points"],
    "assessment_question": "Question to test understanding",
    "expected_answer": "What a good answer should include",
    "reasoning": "Why this approach works for this topic"
}}""",

    "socratic": """You are a teaching expert using the Socratic Method.

Topic: {topic}
Student Level: {student_level:.2f}/1.0

Guide understanding through thoughtful questions that build on each other.

Return JSON format:
{{
    "questions": [
        "First question that introduces the concept",
        "Second question that builds on the first",
        "Third question that deepens understanding",
        "Fourth question that applies the concept"
    ],
    "question_sequence": "Explanation of how questions build on each other",
    "assessment_question": "Final question to test understanding",
    "expected_answer": "What a good answer should include",
    "reasoning": "Why this Socratic approach works for this topic"
}}""",

    "worked_example": """You are a teaching expert using the Worked Example strategy.

Topic: {topic}
Student Level: {student_level:.2f}/1.0

Demonstrate step-by-step problem solving with a concrete example.

Return JSON format:
{{
    "problem_statement": "Specific problem that demonstrates the concept",
    "solution_steps": [
        {{"step": 1, "action": "First step description", "explanation": "Why this step"}},
        {{"step": 2, "action": "Second step description", "explanation": "Why this step"}},
        {{"step": 3, "action": "Third step description", "explanation": "Why this step"}},
        {{"step": 4, "action": "Fourth step description", "explanation": "Why this step"}}
    ],
    "final_answer": "The complete solution",
    "assessment_question": "Question to test if student can apply the method",
    "expected_answer": "What a good answer should include",
    "reasoning": "Why this worked example approach works for this topic"
}}""",

    "analogy": """You are a teaching expert using the Analogy strategy.

Topic: {topic}
Student Level: {student_level:.2f}/1.0

Explain using a relatable real-world analogy that maps key features clearly.

Return JSON format:
{{
    "analogy_concept": "The familiar concept you're using as analogy",
    "analogy_mapping": {{
        "concept_feature_1": "analogy_feature_1",
        "concept_feature_2": "analogy_feature_2",
        "concept_feature_3": "analogy_feature_3"
    }},
    "explanation": "How the analogy helps understand the topic",
    "limitations": "Where the analogy breaks down or is limited",
    "assessment_question": "Question to test understanding",
    "expected_answer": "What a good answer should include",
    "reasoning": "Why this analogy approach works for this topic"
}}""",

    "visual": """You are a teaching expert using the Visual strategy.

Topic: {topic}
Student Level: {student_level:.2f}/1.0

Create a visual representation using diagrams, flowcharts, or spatial descriptions.

Return JSON format:
{{
    "visual_type": "diagram/flowchart/structure/map",
    "visual_description": "Detailed description of the visual layout",
    "ascii_art": "ASCII representation if applicable",
    "key_components": [
        {{"component": "Component name", "position": "Where it's located", "purpose": "What it represents"}},
        {{"component": "Component name", "position": "Where it's located", "purpose": "What it represents"}},
        {{"component": "Component name", "position": "Where it's located", "purpose": "What it represents"}}
    ],
    "connections": "How components relate to each other",
    "assessment_question": "Question to test visual understanding",
    "expected_answer": "What a good answer should include",
    "reasoning": "Why this visual approach works for this topic"
}}"""
}

# ============================================================================
# PRACTICE QUESTION PROMPT
# ============================================================================

PRACTICE_QUESTION_PROMPT = """
Generate practice questions for the student based on what was just taught.

Topic: {topic}
Student Level: {student_level:.2f}/1.0
Teaching Strategy Used: {strategy}
Teaching Content Summary: {teaching_summary}

Generate ONE practice question that:
- Tests understanding of the concept taught
- Matches the student's proficiency level
- Aligns with the teaching strategy style ({strategy})
- Is specific and answerable based on the teaching content

Return JSON format:
{{
    "question": "Practice question text",
    "expected_answer": "What a good answer should include",
    "difficulty": 0.X,
    "hints": ["optional hint 1", "optional hint 2"],
    "reasoning": "Why this question helps the student practice"
}}
"""

# ============================================================================
# STRATEGY SELECTION PROMPT
# ============================================================================

STRATEGY_SELECTION_PROMPT = """You are a meta-learning agent. Analyze the student's learning pattern and decide which teaching strategy to use NEXT.

Available strategies:
{strategies_desc}

Recent session history:
{recent_summary}

Current situation:
- Stuck counter: {stuck_counter} (how many attempts without progress)
- Consecutive failures: {consecutive_failures} (failures in a row)
- Current proficiency: {current_proficiency:.2f}
- Target proficiency: {target_proficiency:.2f}
- Sessions so far: {total_sessions}

META-REASONING GUIDELINES:
1. If a strategy just failed (score < 0.6), DON'T pick it again
2. If student is stuck (consecutive_failures >= 2), try a DIFFERENT approach
3. Consider strategy effectiveness scores - higher is better
4. If no clear pattern, choose highest effectiveness strategy
5. Variety helps - don't repeat same strategy too many times

Based on the above analysis, which strategy should we try NEXT and WHY?

Return JSON:
{{
    "chosen_strategy": "strategy_name",
    "reasoning": "detailed explanation of why this choice makes sense",
    "confidence": 0.X
}}"""

# ============================================================================
# META-REASONER PROMPT
# ============================================================================

META_REASONER_PROMPT = """You are a meta-learning agent analyzing the overall learning progress and deciding what action to take next.

Topic: {topic}
Learning Goal: {learning_goal}

Current State:
- Current Proficiency: {current_proficiency:.2f}/1.0
- Target Proficiency: {target_proficiency:.2f}/1.0
- Progress: {progress_percentage:.1f}%
- Current Attempt: {current_attempt}/{max_attempts}
- Consecutive Failures: {consecutive_failures}
- Stuck Counter: {stuck_counter}
- Total Sessions: {total_sessions}

Recent Performance:
{recent_summary}

Performance Metrics:
- Average Recent Score: {avg_recent_score:.2f}
- Trend: {trend}
- Progress Rate: {progress_rate:.3f} per attempt

DECISION CRITERIA:

1. **CONTINUE** - Keep teaching if:
   - Current proficiency < target proficiency AND
   - Current attempt < max attempts AND
   - (Making progress OR not stuck) AND
   - Not consistently failing

2. **END_SUCCESS** - Goal achieved if:
   - Current proficiency >= target proficiency

3. **END_MAX_ATTEMPTS** - Max attempts reached if:
   - Current attempt >= max attempts

4. **END_STUCK** - Student stuck if:
   - Consecutive failures >= 3 AND
   - No progress (proficiency not increasing) AND
   - Tried multiple strategies without success

5. **PREREQUISITE** - Need prerequisite if:
   - Student consistently struggling (scores < 0.4) AND
   - No progress despite multiple attempts AND
   - Topic likely requires foundational knowledge

Based on the above analysis, what should we do NEXT?

Return JSON format:
{{
    "next_action": "continue|end_success|end_max_attempts|end_stuck|prerequisite",
    "goal_achieved": true/false,
    "needs_prerequisite": true/false,
    "prerequisite_topic": "topic name or empty string",
    "reasoning": "detailed explanation of why this decision makes sense",
    "confidence": 0.X
}}"""
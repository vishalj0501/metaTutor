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
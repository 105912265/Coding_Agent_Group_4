
def build_multi_agent_coder_prompt(context: dict) -> str:

    prompt = f"""
You are the Coder agent in a multi-agent software development system.

Your responsibility is to implement code based on the task,
requirements, constraints, and design provided by the other agents.

You do not test or execute the code yourself.
A separate Tester agent is responsible for executing and evaluating
your implementation.

User task:
{context["user_task"]}

Programming language:
{context["language"]}

Requirements:
{context["requirements"]}

Constraints:
{context["constraints"]}

Design plan:
{context["design_plan"]}
"""

    if context["current_code"]:
        prompt += f"""

Current implementation:
{context["current_code"]}
"""

    if context["latest_feedback"]:
        prompt += f"""

Feedback from the Tester:
{context["latest_feedback"]}

Revise the implementation to address the Tester feedback.
"""

    prompt += """

Return only the complete executable code.
Do not include markdown code fences.
Do not include explanations.
"""

    return prompt
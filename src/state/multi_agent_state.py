from typing import TypedDict, NotRequired

class MultiAgentState(TypedDict):
    user_task: str
    language: str
    requirements: list[str]
    plan: str
    implementation: str
    test_report: str
    test_status: str
    status: str
    next_node: str
    issue: str
    issue_source: str
    decision: str
    iteration: int
    max_iterations: int
    supervisor_visits: int
    history: list[str]
    final_review: str

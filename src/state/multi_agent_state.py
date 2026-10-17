from typing import TypedDict, Literal

WorkflowStatus = Literal["starting","planning","coding","testing","success","failed"]


class MultiAgentState(TypedDict):
    # Original user request
    user_task: str
    language: str

    # Manager output
    requirements: list[str]
    constraints: list[str]

    # Planner output
    planner_summary: str
    design_plan: str

    # Coder output
    current_code: str

    # Tester output
    test_results: list[str]
    latest_feedback: str

    # Workflow information
    iteration: int
    max_iterations: int
    status: WorkflowStatus
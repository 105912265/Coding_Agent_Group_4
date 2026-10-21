from typing import TypedDict, Literal

WorkflowStatus = Literal["starting","researching","coding","testing","success","failed"]
Nodes = Literal["Manager", "Researcher", "Coder", "Tester", "End"]


class MultiAgentState(TypedDict):
    # Original user request
    user_task: str
    language: str

    #layer 1 scope filtering
    scope_status: str
    rejection_reason: str

    # Manager output
    requirements: list[str]
    constraints: list[str]

    # Researcher output
    research_summary: str
    design_plan: str

    # Coder output
    current_code: str

    # Tester output
    test_results: list[str]
    latest_feedback: str

    test_status: str

    # Workflow information
    iteration: int
    max_iterations: int
    status: WorkflowStatus
    next_node: Nodes
    #next_node for routing
from state.multi_agent_state import MultiAgentState


def get_manager_context(state: MultiAgentState) -> dict:
    return {
        "user_task": state["user_task"],
        "language": state["language"],
        "requirements": state["requirements"],
        "constraints": state["constraints"],
        "test_results": state["test_results"],
        "latest_feedback": state["latest_feedback"],
        "status": state["status"]
    }


def get_researcher_context(state: MultiAgentState) -> dict:
    return {
        "user_task": state["user_task"],
        "language": state["language"],
        "requirements": state["requirements"],
        "constraints": state["constraints"]
    }


def get_coder_context(state: MultiAgentState) -> dict:
    return {
        "user_task": state["user_task"],
        "language": state["language"],
        "requirements": state["requirements"],
        "constraints": state["constraints"],
        "design_plan": state["design_plan"],
        "current_code": state["current_code"],
        "latest_feedback": state["latest_feedback"]
    }


def get_tester_context(state: MultiAgentState) -> dict:
    return {
        "user_task": state["user_task"],
        "language": state["language"],
        "requirements": state["requirements"],
        "current_code": state["current_code"]
    }
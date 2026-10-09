from state.multi_agent_state import MultiAgentState


def scope_guard_node(state: MultiAgentState):

    """
    code to be written properly.

    bascially, if user task is not within scope, 
    then it will write either scope: rejected or accepted.

    based on that, there will be a conditional edge to determine
    where langgraph shuold go next.
    """
from langgraph.graph import StateGraph, START, END

from state.multi_agent_state import MultiAgentState

from multi_agent.manager_node import manager_node
from multi_agent.researcher_node import researcher_node
from multi_agent.coder_node import coder_node
from multi_agent.tester_node import tester_node


def route_after_testing(state: MultiAgentState):

    # Successful execution
    if state["test_status"] == "PASS":
        return "finish"

    # Prevent infinite retry loops
    if state["iteration"] >= state["max_iterations"]:
        return "failed"

    # Code failed, so send it back to the Coder
    return "retry"


def build_multi_agent_graph():

    workflow = StateGraph(MultiAgentState)

    # NODES
   
    workflow.add_node("manager", manager_node)

    workflow.add_node("researcher", researcher_node)

    workflow.add_node("coder", coder_node)

    workflow.add_node("tester", tester_node)
    
    # NORMAL EDGES

    workflow.add_edge(START, "manager")

    workflow.add_edge("manager", "researcher")

    workflow.add_edge("researcher", "coder")

    workflow.add_edge("coder", "tester")

    # CONDITIONAL EDGE

    workflow.add_conditional_edges(
        "tester",
        route_after_testing,
        {
            "retry": "coder",
            "finish": END,
            "failed": END
        }
    )

    # Compile graph
    return workflow.compile()
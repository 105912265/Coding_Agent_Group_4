from langgraph.graph import StateGraph, START, END

from state.multi_agent_state import MultiAgentState

from multi_agent.manager_node import manager_node
from multi_agent.researcher_node import researcher_node
from multi_agent.coder_node import create_coder_node
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

def get_manager_decision(state: MultiAgentState):
    
    return state["next_node"]


def build_multi_agent_graph():

    workflow = StateGraph(MultiAgentState)

    #lmm_client is not defined yet
    # Create the Coder node with access to the LLM
    coder_node = create_coder_node(llm_client)
    #Note: Agent.py will be llm_client

    # NODES
   
    workflow.add_node("manager", manager_node)

    workflow.add_node("researcher", researcher_node)

    workflow.add_node("coder", coder_node)

    workflow.add_node("tester", tester_node)
    
    # NORMAL EDGES

    workflow.add_edge(START, "manager")

    workflow.add_edge("researcher", "manager")

    workflow.add_edge("coder", "tester")

    # CONDITIONAL EDGE

    workflow.add_conditional_edges(
        "tester",
        route_after_testing,
        {
            "retry": "coder",
            "finish": "manager",
            "failed": END
        }
    )
    
    workflow.add_conditional_edges(
        "manager",
        get_manager_decision,
        {
            "Researcher": "researcher",
            "Coder": "coder",
            "End": END
        }
    )

    # Compile graph
    return workflow.compile()
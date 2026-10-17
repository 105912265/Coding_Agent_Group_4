from state.multi_agent_state import MultiAgentState
from memory.context_views import get_planner_context

def planner_node(state: MultiAgentState):
    context = get_planner_context(state)
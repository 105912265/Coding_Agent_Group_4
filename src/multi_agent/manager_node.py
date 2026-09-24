from state.multi_agent_state import MultiAgentState
from memory.context_views import get_manager_context

def manager_node(state: MultiAgentState):
    context = get_manager_context(state)

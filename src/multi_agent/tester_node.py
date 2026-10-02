from state.multi_agent_state import MultiAgentState
from memory.context_views import get_tester_context

def tester_node(state: MultiAgentState):
    context = get_tester_context(state)
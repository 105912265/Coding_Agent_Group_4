from state.multi_agent_state import MultiAgentState
from memory.context_views import get_coder_context

def coder_node(state: MultiAgentState):
    context = get_coder_context(state)
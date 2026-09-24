from state.multi_agent_state import MultiAgentState
from memory.context_views import get_researcher_context

def researcher_node(state: MultiAgentState):
    context = get_researcher_context(state)
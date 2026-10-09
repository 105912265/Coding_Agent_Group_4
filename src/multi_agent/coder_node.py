from state.multi_agent_state import MultiAgentState
from memory.context_views import get_coder_context
from prompts.multi_agent_coder_prompt import build_multi_agent_coder_prompt


def create_coder_node(llm_client):

    def coder_node(state: MultiAgentState):

        """
        internal loop with max iterations need to be defined with tandem with tester
        agent.
        """

        print("\n--- CODER AGENT ---")

        # gives the Coder only the shared-state information that is relevant to its role
        context = get_coder_context(state)

        # Build the Coder-specific LLM prompt
        prompt = build_multi_agent_coder_prompt(context)

        # Generate or revise the implementation
        code = llm_client.generate_code(prompt)

        # A new coding attempt has been made
        iteration = state["iteration"] + 1

        print(f"\nCoding iteration: {iteration}")

        print("\nGenerated code:")
        print(code)

        # LangGraph merges these updates into MultiAgentState
        return {
            "current_code": code,
            "iteration": iteration,
            "status": "testing"
        }

    return coder_node
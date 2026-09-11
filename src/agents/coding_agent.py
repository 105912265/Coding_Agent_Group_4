from state.agent_state import AgentState
from prompts.coding_agent_prompt import build_coding_prompt
from tools.execution.code_executor import execute_code


class CodingAgent:

    def __init__(self, llm_client, max_iterations=5):
        self.llm = llm_client
        self.max_iterations = max_iterations

    def run(self, task: str, language: str = "python"):

        #working memory
        state = AgentState(task=task, language=language)

        #max interations to prevent infinite loops
        while state.iteration < self.max_iterations:

            state.iteration += 1

            print(f"\n--- Iteration {state.iteration} ---")

            # Build the context that will be given to the LLM
            prompt = build_coding_prompt(state)

            # Ask the LLM to generate or revise code
            code = self.llm.generate_code(prompt)

            state.current_code = code

            print("\nGenerated code:")
            print(code)

            # Execute the generated code using the code_executor.py
            result = execute_code(
                code=code,
                language=state.language
            )

            # Store the observation in working memory
            state.stdout = result["stdout"]
            state.stderr = result["stderr"]

            # Check whether execution succeeded
            if result["success"]:

                state.status = "success"

                print("\nExecution successful.")

                print("\nOutput:")
                print(state.stdout)

                return state

            print("\nExecution failed.")

            print("\nError:")
            print(state.stderr)

        # Reached maximum attempts
        state.status = "failed"

        print("\nAgent failed after maximum iterations.")

        return state
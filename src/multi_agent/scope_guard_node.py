from state.multi_agent_state import MultiAgentState


def create_scope_guard_node(llm_client):
    def scope_guard_node(state: MultiAgentState):
        print("\n--- SCOPE GUARD ---")

        # Get the user's original request
        user_task = state["user_task"]

        # Build the classification prompt
        prompt = build_scope_guard_prompt(user_task)

        try:
            # Ask the LLM to classify the request
            response = llm_client.generate_text(prompt)

            # Convert the LLM's JSON response into a dictionary
            result = json.loads(response)

            # Validate the classification
            if not isinstance(result, dict):
                raise ValueError("Expected a JSON object")

            scope_status = result.get("scope_status")
            rejection_reason = result.get("rejection_reason", "")

            if scope_status not in ("allowed", "rejected"):
                raise ValueError("Invalid scope classification")

            if not isinstance(rejection_reason, str):
                raise ValueError("Invalid rejection reason")

            if scope_status == "allowed":
                print("Request allowed")

                return {
                    "scope_status": "allowed",
                    "rejection_reason": "",
                    "status": "starting"
                }

            print("Request rejected")

            return {
                "scope_status": "rejected",
                "rejection_reason": (
                    rejection_reason.strip()
                    or "Request is outside the supported scope."
                ),
                "status": "failed"
            }

        except Exception as error:
            print(f"Scope classification error: {error}")

            # If classification fails, do not allow the request
            return {
                "scope_status": "rejected",
                "rejection_reason": "Unable to validate the request.",
                "status": "failed"
            }

    return scope_guard_node
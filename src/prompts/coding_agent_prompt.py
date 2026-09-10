def build_coding_prompt(state) -> str:
    # The inital prompt gives the base context to the LLM
    # gives state.task/programming language/iteration number
    prompt = f"""
You are an autonomous coding agent.

Your task is:

{state.task}

Programming language:
{state.language}

Current iteration:
{state.iteration}
"""

    #after the initial run, latest code will be appended to LLMs context 
    if state.current_code:
        prompt += f"""

Current code:

{state.current_code}
"""

    #on first run or any succesful runs, sterr (errors) will be empty so this is skipped
    #if there is an failure, execution failure logs will be appended to prompt so LLm knows waht to fix.
    if state.stderr:
        prompt += f"""

The previous execution failed with this error:

{state.stderr}

Fix the code.
"""

    
    # Directs the model to output raw code only, making automated parsing easier.
    prompt += """

Return only the complete executable code.
"""

    return prompt
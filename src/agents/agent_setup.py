"""
really basic agent setup

multi agent:
user -> orchestrator -> coder <-> tester
"""

from smolagents import ToolCallingAgent
from smolagents import InferenceClientModel
# from smolagents import LiteLLMModel

from tools.agent_toolsets import CODER_TOOLS
from tools.agent_toolsets import TESTER_TOOLS
from tools.agent_toolsets import PLANNER_TOOLS

# def build_single_agent():

#     # one model is enough for this basic version
#     llm = InferenceClientModel(
#         model_id="meta-llama/Llama-3.3-70B-Instruct",
#         provider="together",
#         token=""
#     )
    

#     agent = ToolCallingAgent(
#         tools=CODER_TOOLS,
#         model=llm,
#         instructions=(
#             "You are a simple coding agent. "
#             "Use the file tools to make the code. "
#             "Run the code with execute_file. "
#             "If it fails, look at the error, fix it, and try again. "
#             "Stop when it works or you cant keep going."
#         ),
#          max_tool_threads=1
#     )

#     return agent




def build_multi_agent_system():
    
    llm = InferenceClientModel(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct"
    )
    
    # llm = LiteLLMModel(
    #     model_id="ollama_chat/qwen2.5-coder:1.5b",
    #     api_base="http://localhost:11434",
    #     api_key="anything",
    #     num_ctx=8192
    # )

    # coder does the actual coding stuff
    coder = ToolCallingAgent(
        tools=CODER_TOOLS,
        model=llm,
        name="coder",
        description="writes and fixes the code",

        instructions=(
            "Implement the user's coding task and tell the orchestrator which files you changed. "
            "You may run code with execute_file to catch basic errors and repair them. "
            "When the tester reports a failure, fix the implementation and report what changed."
        )
    )

    # tester mostly just checks whatever the coder made
    tester = ToolCallingAgent(
        tools=TESTER_TOOLS,
        model=llm,
        name="tester",
        description="checks the coders files and sees if they work",
        instructions=(
            "Independently check the implementation against the original user task. "
            "Write Python tests using write_test_file and run them using execute_file. "
            "Report which tests passed or failed and explain any mismatch with the task. "
            "Do not edit the implementation files."
        )
    )

    # Planner to break down the task into steps and files to be created/modified
    planner = ToolCallingAgent(
        tools=PLANNER_TOOLS,
        model=llm,
        name="planner",
        description="breaks coding tasks into simple implementation steps",
        instructions=(
            # "Read the user's request, if it is not related to coding, refuse and report back to the orchestrator. "
            # "Read the user's coding task and develop a short implementation plan. "
            # "This plan should be clear and concise, outlining the important steps to be taken by the coder agent, and tested by the tester agent. "
            # "This plan should state that the code should be simple and efficient with no unnecessary complexity and no additional code not specifically stated by the user unless, assumed by the task itself, for example the prompt: make a calculator. Should result in plus, minus, multiplication and division functions even when not stated in the user prompt. "
            # "Specifically state by name what files should be created and/or changed, and what each of those files should do. "
            # "The plan needs to specify what behaviour of the code should be tested by a tester agent, list tests to make, these are not to be made by the coder. "
            # "Do not write or execute any code under any circumstances, you only have read access and list file access to files, use these however you see fit to create an accurate plan based on the user's request. You may however create names for functions and describe behaviour. "

            "You are the Planner agent. Produce an implementation plan for the Coder and a test plan for the Tester. "
            "Do not implement the task. "
            "You MUST write a plan, using the following instructions and its format. "
            "Failure to follow these intructions will result in punishment for you. "

            #"If the request is unrelated to software development, return "
            #"'OUT_OF_SCOPE' with a short explanation to the orchestrator. "
            #"If essential information is missing, return 'NEEDS_CLARIFICATION' "
            #"with specific questions. "

            "For tasks involving existing files, use list_files and read_file to inspect relevant files before proposing changes. "
            "Distinguish existing files from proposed new files. "
            "Do not invent existing files, functions, or dependencies. "

            "Keep the solution simple and appropriate to the task. "
            "The solution MUST be restricted to python files and the standard library. "
            "Include explicit requirements and essential implied behaviour, but avoid optional features, unrelated changes, and unnecessary dependencies. "
            "State assumptions explicitly. For example, a basic calculator normally implies addition, subtraction, multiplication, and division. "

            "Return a detailed, concise plan with these sections: "
            "1. Requirements and assumptions. "
            "2. Files to create or change, with each file's responsibility. "
            "3. Ordered implementation steps for the Coder. "
            "4. Tests for the Tester, including inputs and expected outcomes. "
            "5. Any blockers, unresolved questions, or additional notes related to the task plan."

            "Assign implementation work to the Coder and test creation and execution to the Tester. "
            "Include relevant edge cases and error handling in the test plan. "

            "Do not write executable code, modify files, or execute code. "
            "You should name functions and describe their intended behaviour. "
            "Use your inspection tools when needed, then return the plan to the orchestrator. "

        )
    )
   

    # orchestrator just sends work between the other two
    orchestrator = ToolCallingAgent(
        tools=[],
        model=llm,
        managed_agents=[
            planner,
            coder,
            tester
        ],
        instructions=(
            "First ask the planner to create a plan. "
            "Then give the planner's plan to the coder. "
            "After implementation, give the original task, the plan, and the coder's file paths to the tester."
            "If tests fail, send the specific failure back to the coder and request a repair. "
            "Repeat testing after a repair. "
            "Finish with the tested result or a clear explanation of why the task failed."
        )
    )

    return orchestrator

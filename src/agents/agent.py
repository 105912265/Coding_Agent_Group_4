from smolagents import ToolCallingAgent

#Basic superclass 'Agent' that all agents can take from - i.e. initialising LLM, instructions, max steps by default is 4

class Agent:
    def __init__(self, model, instructions: str, name: str, max_steps: int = 4):
        self.agent = ToolCallingAgent(model=model, tools=[], instructions=instructions,name=name, max_steps=max_steps, verbosity_level=0)
        
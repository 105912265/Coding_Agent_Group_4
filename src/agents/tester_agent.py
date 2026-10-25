from agents.agent import Agent
from tools.agent_toolsets import TESTER_TOOLS

class Tester(Agent):
    def __init__(self, model):
        super().__init__(self, model, get_tester_instructions() , 'tester' , 4, TESTER_TOOLS)
    
from agents.agent import Agent

class ManagerAgent(Agent):
    
    def __init__(self, model, instructions, name, max_steps = 4):
        super().__init__(model, instructions, name, max_steps)
        
        #need to add instructions
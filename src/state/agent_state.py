from dataclasses import dataclass

#providse a concise way te create classes that store data without needing boilterplate info 
@dataclass
class AgentState:
    task: str
    language: str = "python"

    current_code: str = ""

    stdout: str = ""
    stderr: str = ""

    iteration: int = 0
    status: str = "running"
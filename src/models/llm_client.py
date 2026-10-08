import os
from pathlib import Path

from dotenv import load_dotenv
from smolagents import OpenAIServerModel

#Creating llm client that is compatible with OpenAI models
#includes gemini since it has OpenAI compatability
#MAKE SURE THAT .ENV IS IN GITIGNORE OR ELSE YOUR API KEY IS LEAKED
#setup a .env file under the root directory (not src) with the following:

#LLM_API_KEY=
#LLM_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
#LLM_MODEL=gemini-3.5-flash-lite

# you may change the llm model, but this is the one that is working



def create_llm_client():
    root = Path(__file__).resolve().parent[2] #Goes to Coding_Agent_Group_4/
    load_dotenv(root / ".env")
    
    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model_id = os.getenv("LLM_MODEL")
    
    if not all([api_key, api_base, model_id]):
        raise ValueError(
            "Make sure api key, base and model id is set in .env"
        )
    
    return OpenAIServerModel(
        model_id=model_id,
        api_base=api_base,
        api_key=api_key,
        client_kwargs={
            "timeout": 60,
            "max_retries": 3,
        }
    )
When setting up your API keys to run the project, make sure to create a .env file under the root directory
ENSURE THAT .env IS IN .gitignore

.env should have:

LLM_API_KEY= YOUR KEY
LLM_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-3.5-flash-lite

you may change API base/model to something else (ensure that it is openai compatible)


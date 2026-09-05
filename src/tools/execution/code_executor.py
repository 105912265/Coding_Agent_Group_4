from .python_runner import run_python


RUNNERS = {
    "python": run_python
}


def execute_code(code: str, language: str) -> dict:
    """
    Execute code using the runner for the requested programming language.
    Requested programming language currently is requested by the user. (Currently just python, other langauges will be implmented later)
    Once LLM is connected, the parameter language would we inputed by LLM after detecting 
    programming language accordingly.

    paramters: code to be executed as string, programming language to be used
    """

    language = language.lower().strip()

    runner = RUNNERS.get(language)

    if runner is None:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unsupported programming language: {language}",
            "exit_code": None
        }

    return runner(code)
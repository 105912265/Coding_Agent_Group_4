
"""Launch the multi-agent workflow in the background."""

import os
import sys
import subprocess
import traceback
from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
UI_FOLDER = PROJECT_FOLDER / "src" / "ui"

PROMPT_FILE = UI_FOLDER / "pending_prompt.txt"
SCRIPT_FILE = PROJECT_FOLDER / "src" / "run_multi_agent.py"
MESSAGES_FILE = UI_FOLDER / "messages.txt"
ERRORS_FILE = UI_FOLDER / "errors.txt"
LOG_FILE = UI_FOLDER / "agent_output.log"


def log_message(sender, message):
    message = str(message)
    message = message.replace("|", "/")
    message = message.replace("\r", " ").replace("\n", " ")

    with open(MESSAGES_FILE, "a", encoding="utf-8") as file:
        file.write(f"{sender}|{message}\n")


def report_error(message):
    log_message(
        "AGENT",
        "The coding agent could not start correctly. Check the Errors panel."
    )

    with open(ERRORS_FILE, "a", encoding="utf-8") as file:
        file.write(str(message) + "\n")


def main():
    try:
        if not PROMPT_FILE.is_file():
            raise FileNotFoundError("pending_prompt.txt was not found.")

        if not SCRIPT_FILE.is_file():
            raise FileNotFoundError("run_multi_agent.py was not found.")

        prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()

        if not prompt:
            raise ValueError("The submitted prompt was empty.")

        max_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3

        if max_iterations < 1 or max_iterations > 5:
            raise ValueError("Invalid max_iterations value.")

        # Remove the prompt file after reading it.
        PROMPT_FILE.unlink(missing_ok=True)

        # Launch the actual multi-agent workflow.
        with open(LOG_FILE, "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                [
                    sys.executable,
                    str(SCRIPT_FILE),
                    prompt,
                    "--max-iterations",
                    str(max_iterations)
                ],
                cwd=str(PROJECT_FOLDER),
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    except Exception:
        report_error(traceback.format_exc())


if __name__ == "__main__":
    main()

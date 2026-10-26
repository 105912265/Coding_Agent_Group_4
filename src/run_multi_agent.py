"""Run from project root: python src/run_multi_agent.py "Build a calculator""" 

import os
import traceback
import argparse
from models.llm_client import create_llm_client
from multi_agent.graph import build_multi_agent_graph, initial_state

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_FOLDER = os.path.join(PROJECT_FOLDER, "src", "ui")

MESSAGES_FILE = os.path.join(UI_FOLDER, "messages.txt")
STATUS_FILE = os.path.join(UI_FOLDER, "status.txt")
ERRORS_FILE = os.path.join(UI_FOLDER, "errors.txt")

def write_status(title, stage, progress):
    with open(STATUS_FILE, "w", encoding="utf-8") as file:
        file.write(f"TITLE|{title}\n")
        file.write(f"STAGE|{stage}\n")
        file.write(f"PROGRESS|{progress}\n")

def write_error(message):
    with open(ERRORS_FILE, "a", encoding="utf-8") as file:
        file.write(str(message) + "\n")


def log_message(sender, message):
    """Print a message and append it to the UI chat."""
    message = str(message)

    print(message, flush=True)

    # maintain message txt format.
    message = message.replace("|", "/")
    message = message.replace("\r", " ").replace("\n", " ")

    with open(MESSAGES_FILE, "a", encoding="utf-8") as file:
        file.write(f"{sender}|{message}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', nargs='?', help='Coding task (prompted if omitted)')
    parser.add_argument('--max-iterations', type=int, default=3)
    args = parser.parse_args()
    task = args.task or input('Coding task: ')
    if args.max_iterations < 1:
        parser.error('--max-iterations must be at least 1')

    os.makedirs(UI_FOLDER, exist_ok=True)
    # refresh error output
    with open(ERRORS_FILE, "w", encoding="utf-8") as file:
        file.write("")
    title = task[:45] + ("..." if len(task) > 45 else "")
    
    try:
        write_status(title, "Starting agent system", 5)
        log_message("AGENT", "Starting the multi-agent workflow.")

        log_message("AGENT", "Creating LLM client...")
        llm = create_llm_client()

        log_message("AGENT", "Building multi-agent graph...")
        graph = build_multi_agent_graph(llm)

        log_message("AGENT", "Preparing initial task state...")
        state = initial_state(task, args.max_iterations)

        write_status(title, "Running multi-agent workflow", 20)
        log_message("AGENT", "Agents are now working on your task.")

        result = graph.invoke(
            state,
            config={
                "recursion_limit": max(
                    30, args.max_iterations * 12 + 20
                )
            }
        )

        write_status(title, "Processing results", 90)

        status = result["status"]
        history = result["history"]
        implementation = result["implementation"]
        test_report = result["test_report"]
        final_review = result["final_review"]

        log_message("AGENT", f"Workflow status: {status}")
        log_message("AGENT", "Workflow: " + " -> ".join(history))
        log_message("AGENT", "Implementation: " + str(implementation))
        log_message("AGENT", "Tests: " + str(test_report))
        log_message("AGENT", "Supervisor: " + str(final_review))

        if status == "needs_clarification":
            log_message(
                "AGENT",
                "Please clarify: " + str(final_review)
            )
            write_status(title, "Needs clarification", 100)

        elif status in ("failed", "error"):
            write_status(title, "Task failed", 100)

        else:
            write_status(title, "Completed", 100)

    except Exception:
        error_details = traceback.format_exc()

        print(error_details, flush=True)
        write_error(error_details)

        write_status(title, "Task failed", 100)

        log_message(
            "AGENT",
            "An error occurred. Check the Errors panel for details."
        )


if __name__ == '__main__':
    main()

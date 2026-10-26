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

        write_status(title, "Creating LLM client", 10)
        llm = create_llm_client()

        write_status(title, "Building multi-agent graph", 15)
        graph = build_multi_agent_graph(llm)

        state = initial_state(task, args.max_iterations)

        write_status(title, "Running multi-agent workflow", 20)
        log_message("AGENT", "Agents are now working on your task.")



        config = {
            "recursion_limit": max(
                30, args.max_iterations * 12 + 20
            )
        }

        result = None
        update_count = 0
        last_stage = ""

        #graph.stream instead of graph.invoke for progress snapshots

        for snapshot in graph.stream(
            state,
            config=config,
            stream_mode="values"
        ):
            result = snapshot
            update_count += 1

            history = snapshot.get("history", [])

            if history:
                stage = str(history[-1])
            else:
                stage = "Running multi-agent workflow"

            if stage != last_stage:
                progress = min(90, 20 + update_count * 5)
                write_status(title, stage, progress)
                print(f"Workflow stage: {stage}", flush=True)
                last_stage = stage

        if result is None:
            raise RuntimeError("The graph did not return any state.")


        write_status(title, "Processing results", 90)

        status = result["status"]
        history = result["history"]
        implementation = result["implementation"]
        test_report = result["test_report"]
        final_review = result["final_review"]

        print("\nSTATUS:", status, flush=True)
        print("\nWORKFLOW:", " -> ".join(history), flush=True)
        print("\nIMPLEMENTATION:", implementation, flush=True)
        print("\nTESTS:", test_report, flush=True)
        print("\nSUPERVISOR:", final_review, flush=True)

        log_message("AGENT", f"Workflow finished with status: {status}")

        if status == "needs_clarification":
            log_message(
                "AGENT",
                "The agent needs more information: " + str(final_review)
            )
            write_status(title, "Needs clarification", 100)

        elif status in ("failed", "error"):
            log_message(
                "AGENT",
                "The task could not be completed. Check the output or errors."
            )
            write_status(title, "Task failed", 100)

        else:
            log_message(
                "AGENT",
                "Task completed. Review the generated files and test results."
            )
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

"""
starts the multi agent version

this is the main.py for the multi agent system i just didnt want ot make it too confusing for now!!
"""
import os

import sys

import traceback


from agents.agent_setup import build_multi_agent_system

project_folder = os.path.dirname(os.path.abspath(__file__))
ui_folder = os.path.join(project_folder, "ui")

messages_file = os.path.join(ui_folder, "messages.txt")
status_file = os.path.join(ui_folder, "status.txt")
errors_file = os.path.join(ui_folder, "errors.txt")

def write_status(title, stage, progress):
    with open(status_file, "w", encoding="utf-8") as file:
        file.write(f"TITLE|{title}\n")
        file.write(f"STAGE|{stage}\n")
        file.write(f"PROGRESS|{progress}\n")


def append_message(sender, message):
    with open(messages_file, "a", encoding="utf-8") as file:
        file.write(f"{sender}|{message}\n")

def main():

    #if launched with argument (from ui prompt), use arg as prompt
    if len(sys.argv) > 1:
        user_task = sys.argv[1]
    else:
        # user can just type whatever small coding task they want
        user_task = input("Enter a coding task: ")


    #project title = task
    title = user_task[:50].replace("\n", " ").strip() or "New Project"


    try:
        write_status(title, "Building agent system", 10)

        # build everyone first
        multi_agent_system = build_multi_agent_system()

        write_status(title, "Agents working", 25)

        #run orchestrator
        final_answer = multi_agent_system.run(user_task)

        write_status(title, "Task completed", 100)
        append_message("AGENT", str(final_answer))
    except Exception:
        error_message = traceback.format_exc()

        with open(errors_file, "a", encoding="utf-8") as file:
            file.write(error_message + "\n")

        write_status(title, "Task failed", 0)
        append_message("AGENT", "Sorry, the task failed. Check the error log.")

        sys.exit(1)

if __name__ == "__main__":
    main()

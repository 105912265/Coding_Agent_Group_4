"""
starts the multi agent version

this is the main.py for the multi agent system i just didnt want ot make it too confusing for now!!
"""

from agents.agent_setup import build_multi_agent_system


def main():

    # build everyone first
    multi_agent_system = build_multi_agent_system()

    # user can just type whatever small coding task they want
    user_task = input("enter a coding task: ")

    final_answer = multi_agent_system.run(user_task)

    print("\nfinal result:")
    print(final_answer)


if __name__ == "__main__":
    main()

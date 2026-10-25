"""Run from project root: python src/run_multi_agent.py "Build a calculator""" 
import argparse
from models.llm_client import create_llm_client
from multi_agent.graph import build_multi_agent_graph, initial_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', nargs='?', help='Coding task (prompted if omitted)')
    parser.add_argument('--max-iterations', type=int, default=3)
    args = parser.parse_args()
    task = args.task or input('Coding task: ')
    if args.max_iterations < 1:
        parser.error('--max-iterations must be at least 1')
    graph = build_multi_agent_graph(create_llm_client())
    result = graph.invoke(initial_state(task, args.max_iterations), config={'recursion_limit': max(30, args.max_iterations * 12 + 20)})
    print('\nSTATUS:', result['status'])
    print('\nWORKFLOW:', ' -> '.join(result['history']))
    print('\nIMPLEMENTATION:', result['implementation'])
    print('\nTESTS:', result['test_report'])
    print('\nSUPERVISOR:', result['final_review'])
    if result['status'] == 'needs_clarification':
        print('\nPlease clarify:', result['final_review'])


if __name__ == '__main__':
    main()

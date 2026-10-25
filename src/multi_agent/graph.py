from langgraph.graph import StateGraph, START, END
from state.multi_agent_state import MultiAgentState
from multi_agent.worker_nodes import create_nodes


def build_multi_agent_graph(model):
    planner, coder, tester, supervisor = create_nodes(model)
    graph = StateGraph(MultiAgentState)
    graph.add_node('planner', planner)
    graph.add_node('coder', coder)
    graph.add_node('tester', tester)
    graph.add_node('supervisor', supervisor)
    graph.add_edge(START, 'planner')
    graph.add_conditional_edges('planner', lambda s: 'coder' if s['status'] == 'planned' else 'supervisor', {'coder':'coder','supervisor':'supervisor'})
    graph.add_conditional_edges('coder', lambda s: 'tester' if s['status'] == 'coded' else 'supervisor', {'tester':'tester','supervisor':'supervisor'})
    graph.add_edge('tester', 'supervisor')
    graph.add_conditional_edges('supervisor', lambda s: s['next_node'], {'planner':'planner','coder':'coder','tester':'tester','approve':END,'clarify':END,'stop':END})
    return graph.compile()


def initial_state(task, max_iterations=3):
    return dict(user_task=task, language='auto', requirements=[], plan='', implementation='', test_report='', test_status='not_run', status='starting', next_node='planner', issue='', issue_source='', decision='', iteration=0, max_iterations=max_iterations, supervisor_visits=0, history=[], final_review='')

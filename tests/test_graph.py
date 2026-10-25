import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from multi_agent.graph import build_multi_agent_graph, initial_state

class GraphTests(unittest.TestCase):
    def test_happy_path(self):
        def plan(s): return {'status':'planned','history':s['history']+['planner']}
        def code(s): return {'status':'coded','iteration':s['iteration']+1,'history':s['history']+['coder']}
        def test(s): return {'status':'tested','test_status':'pass','history':s['history']+['tester']}
        def review(s): return {'status':'success','next_node':'approve','history':s['history']+['supervisor']}
        with patch('multi_agent.graph.create_nodes', return_value=(plan,code,test,review)):
            result=build_multi_agent_graph(None).invoke(initial_state('task'))
        self.assertEqual(result['history'],['planner','coder','tester','supervisor'])

    def test_escalation_and_retry(self):
        def plan(s): return {'status':'planned','history':s['history']+['planner']}
        def code(s): return {'status':'coded','iteration':s['iteration']+1,'history':s['history']+['coder']}
        def test(s): return {'status':'tested' if s['iteration']>1 else 'escalated','test_status':'pass' if s['iteration']>1 else 'fail','history':s['history']+['tester']}
        def review(s): return {'status':'success' if s['test_status']=='pass' else 'redirected','next_node':'approve' if s['test_status']=='pass' else 'coder','history':s['history']+['supervisor']}
        with patch('multi_agent.graph.create_nodes', return_value=(plan,code,test,review)):
            result=build_multi_agent_graph(None).invoke(initial_state('task'))
        self.assertEqual(result['iteration'],2)
        self.assertEqual(result['status'],'success')

if __name__=='__main__': unittest.main()

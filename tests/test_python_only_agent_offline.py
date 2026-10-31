"""Offline tests for the Python-only single coding agent; no Gemini/Docker needed."""
import importlib.util
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'src' / 'single_coding_agent.py'

# Stub third-party imports so these tests run without contacting an LLM.
smolagents = types.ModuleType('smolagents')
smolagents.ToolCallingAgent = object
smolagents.tool = lambda f: f
models = types.ModuleType('models')
models.__path__ = []
client = types.ModuleType('models.llm_client')
client.create_llm_client = lambda: None
with patch.dict(sys.modules, {
    'smolagents': smolagents,
    'models': models,
    'models.llm_client': client,
}):
    spec = importlib.util.spec_from_file_location('single_coding_agent_pyonly', SCRIPT)
    agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent)


class PythonOnlyRunnerTests(unittest.TestCase):
    def test_docker_runs_only_python(self):
        cmd = agent.docker_command(Path('/tmp/workspace'), ['-c', 'print(1)'])
        self.assertIn('python:3.12-slim', cmd)
        self.assertEqual(cmd[cmd.index('python'):cmd.index('python')+2], ['python', '-B'])
        self.assertNotIn('node', ' '.join(cmd).lower())

    def test_parses_three_passed_tests(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            (w / 'tests').mkdir()
            (w / 'tests' / 'test_math.py').write_text('import unittest\n')
            with patch.object(agent, 'run_docker', return_value=(0, 'Ran 3 tests in 0.005s\n\nOK\n')):
                self.assertEqual(agent.run_docker_tests(w)[:3], ('passed', 3, 0))

    def test_parses_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            (w / 'test_math.py').write_text('import unittest\n')
            with patch.object(agent, 'run_docker', return_value=(1, 'Ran 2 tests in 0.005s\nFAILED (failures=1)')):
                self.assertEqual(agent.run_docker_tests(w)[:3], ('failed', 2, 1))

    def test_missing_tests_returns_no_tests(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(agent.run_docker_tests(Path(folder))[0], 'no_tests')

    def test_zero_tests_does_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            (w / 'test_math.py').write_text('import unittest\n')
            with patch.object(agent, 'run_docker', return_value=(0, 'Ran 0 tests in 0.002s\n\nOK\n')):
                self.assertEqual(agent.run_docker_tests(w)[0], 'no_tests')

    def test_docker_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            (w / 'test_math.py').write_text('import unittest\n')
            with patch.object(agent, 'run_docker', return_value=(125, 'docker unavailable')):
                self.assertEqual(agent.run_docker_tests(w)[0], 'not_run')

    def test_test_file_classification(self):
        self.assertTrue(agent.is_test_file('tests/test_game.py'))
        self.assertFalse(agent.is_test_file('game.py'))
        self.assertFalse(agent.is_test_file('tests/game.test.js'))

    def test_failed_test_then_test_correction_not_implementation_repair(self):
        history = [
            {'status': 'failed', 'changed_files': ['game.py', 'tests/test_game.py']},
            {'status': 'passed', 'changed_files': ['tests/test_game.py']},
            {'status': 'passed', 'changed_files': ['game.py']},
        ]
        self.assertEqual(agent.classify_repairs(history), (False, True))

    def test_failed_test_then_implementation_correction(self):
        history = [
            {'status': 'failed', 'changed_files': ['game.py', 'tests/test_game.py']},
            {'status': 'passed', 'changed_files': ['game.py']},
        ]
        self.assertEqual(agent.classify_repairs(history), (True, False))

    def test_real_unittest_runner_executes_two_tests_without_docker(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            (w / 'math_utils.py').write_text('def add(a, b): return a + b\n')
            (w / 'tests').mkdir()
            (w / 'tests' / 'test_math_utils.py').write_text(
                'import unittest\n'
                'from math_utils import add\n'
                'class TestMath(unittest.TestCase):\n'
                '    def test_positive(self): self.assertEqual(add(2, 3), 5)\n'
                '    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n'
            )
            code = agent.TEST_RUNNER.replace("Path('/workspace')", f'Path({str(w)!r})')
            proc = subprocess.run(
                [sys.executable, '-B', '-c', code],
                cwd=w, capture_output=True, text=True,
                env={**__import__('os').environ, 'PYTHONPATH': str(w)},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('Ran 2 tests', proc.stderr)

    def test_real_unittest_runner_rejects_a_broken_function(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            (w / 'math_utils.py').write_text('def add(a, b): return a - b\n')
            (w / 'test_math_utils.py').write_text(
                'import unittest\n'
                'from math_utils import add\n'
                'class TestMath(unittest.TestCase):\n'
                '    def test_add(self): self.assertEqual(add(2, 3), 5)\n'
            )
            code = agent.TEST_RUNNER.replace("Path('/workspace')", f'Path({str(w)!r})')
            proc = subprocess.run(
                [sys.executable, '-B', '-c', code],
                cwd=w, capture_output=True, text=True,
                env={**__import__('os').environ, 'PYTHONPATH': str(w)},
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('FAILED', proc.stderr)

    def test_file_path_confined_to_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Path(folder)
            self.assertEqual(agent.safe_path(w, 'tests/test_x.py'), w / 'tests' / 'test_x.py')
            with self.assertRaises(ValueError):
                agent.safe_path(w, '../bad.py')


if __name__ == '__main__':
    unittest.main()

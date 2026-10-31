"""One Smolagents coding agent with multi-file tools and Python unittest in Docker.

Run from the project root:
    python src/single_coding_agent.py "Build a Python calculator with unit tests"
    python src/single_coding_agent.py --repair-test
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from smolagents import ToolCallingAgent, tool
from models.llm_client import create_llm_client


PROJECT_DIR = Path(__file__).resolve().parent.parent

# Run a Python unittest suite from multiple files, including files in tests/.
# This is executed *inside Docker*, never on the host computer.
TEST_RUNNER = """
import importlib.util
import sys
import unittest
from pathlib import Path

root = Path('/workspace')
files = sorted(root.rglob('test_*.py'))
suite = unittest.TestSuite()

for index, path in enumerate(files):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f'generated_test_{index}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))

test_count = suite.countTestCases()
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() and test_count > 0 else 1)
"""


# Optional controlled repair experiment, retained from the previous version.
BROKEN_SOLUTION = """def is_prime(n):
    if n < 2:
        return True
    for divisor in range(2, int(n ** 0.5)):
        if n % divisor == 0:
            return False
    return True
"""

REPAIR_TESTS = """import unittest
from solution import is_prime

class TestPrime(unittest.TestCase):
    def test_negative(self): self.assertFalse(is_prime(-5))
    def test_zero(self): self.assertFalse(is_prime(0))
    def test_one(self): self.assertFalse(is_prime(1))
    def test_two(self): self.assertTrue(is_prime(2))
    def test_three(self): self.assertTrue(is_prime(3))
    def test_four(self): self.assertFalse(is_prime(4))
    def test_nine(self): self.assertFalse(is_prime(9))
    def test_twenty_five(self): self.assertFalse(is_prime(25))
    def test_ninety_seven(self): self.assertTrue(is_prime(97))
    def test_one_hundred(self): self.assertFalse(is_prime(100))
"""


def safe_path(workspace, path):
    """Resolve a relative path without allowing it outside this run's workspace."""
    requested = Path(path)
    if requested.is_absolute():
        raise ValueError("Use a relative file path.")

    full_path = (workspace / requested).resolve()
    if not full_path.is_relative_to(workspace.resolve()):
        raise ValueError("Path is outside the workspace.")
    return full_path


PYTHON_IMAGE = "python:3.12-slim"


def docker_command(workspace, python_args):
    """Run Python in a restricted temporary Docker container."""
    return [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "256m",
        "--cpus", "1",
        "--pids-limit", "64",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,noexec,size=64m",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "PYTHONPATH=/workspace",
        "-e", "HOME=/tmp",
        "-v", f"{workspace.resolve()}:/workspace:ro",
        "-w", "/workspace",
        PYTHON_IMAGE,
        "python", "-B", *python_args,
    ]


def run_docker(workspace, python_args, timeout=60):
    """Return the exit code and combined output from Python inside Docker."""
    try:
        result = subprocess.run(
            docker_command(workspace, python_args),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return None, f"Docker execution timed out after {timeout} seconds."
    except OSError as error:
        return None, f"Could not start Docker: {error}"



def run_docker_tests(workspace):
    """Find test_*.py files and run their unittest tests together in Docker."""
    test_files = list(workspace.rglob("test_*.py"))
    if not test_files:
        return "no_tests", 0, None, "No test_*.py files were found."

    exit_code, output = run_docker(workspace, ["-c", TEST_RUNNER])
    matches = re.findall(r"Ran (\d+) tests?", output)
    count = int(matches[-1]) if matches else 0

    if exit_code is None or exit_code in (125, 126, 127):
        status = "not_run" if exit_code is not None else (
            "timeout" if "timed out" in output else "not_run"
        )
    elif exit_code == 0 and count == 0:
        status = "no_tests"
    elif exit_code == 0 and count > 0:
        status = "passed"
    else:
        status = "failed"

    return status, count, exit_code, output



def is_test_file(path):
    """Recognize Python unittest files, including in nested tests/ folders."""
    path = Path(path)
    return path.suffix == ".py" and path.name.startswith("test_")


def classify_repairs(test_history):
    """Count edits between a failed test run and the next successful run.

    Test-only edits count as test correction, not implementation self-repair.
    """
    implementation_repair = False
    test_repair = False
    waiting_for_pass = False
    changed_after_failure = set()

    for entry in test_history:
        status = entry["status"]

        if waiting_for_pass:
            changed_after_failure.update(entry.get("changed_files", []))
            if status == "passed":
                if any(not is_test_file(name) for name in changed_after_failure):
                    implementation_repair = True
                if any(is_test_file(name) for name in changed_after_failure):
                    test_repair = True
                waiting_for_pass = False
                changed_after_failure.clear()
        elif status == "failed":
            waiting_for_pass = True
            changed_after_failure.clear()

    return implementation_repair, test_repair



def main():
    repair_test = "--repair-test" in sys.argv[1:]
    task = " ".join(arg for arg in sys.argv[1:] if arg != "--repair-test").strip()

    if repair_test:
        task = "Fix the existing is_prime function using the failing unit tests."
    if not task:
        task = input("What would you like me to build? ").strip()
    if not task:
        print("Please enter a coding task.")
        return

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = PROJECT_DIR / "runtime" / "evaluation" / "single_agent" / run_id
    workspace = output_dir / "workspace"
    workspace.mkdir(parents=True)

    revision = 0  # Increments whenever a file is created, edited, or deleted.
    version_numbers = {}  # One code version per set of files tested.
    test_history = []
    changed_files = set()
    agent = None
    agent_answer = ""
    error_message = ""
    start = time.perf_counter()

    # The agent can change normal generated tests, but not the fixed repair tests.
    def file_is_protected(path):
        return repair_test and path.relative_to(workspace).as_posix() == "test_repair.py"

    @tool
    def write_file(path: str, content: str) -> str:
        """Create or update a text file in the current workspace.

        Args:
            path: Relative filename, such as app.py, index.html, style.css, or tests/test_game.py.
            content: Full contents of the file.
        """
        nonlocal revision
        try:
            target = safe_path(workspace, path)
            if file_is_protected(target):
                return "Error: the fixed acceptance tests cannot be changed."
            if len(content) > 200_000:
                return "Error: file content is too large."
            old_content = target.read_text(encoding="utf-8") if target.is_file() else None
            if old_content != content:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                revision += 1
                changed_files.add(target.relative_to(workspace).as_posix())
            return f"Saved {path}."
        except (OSError, ValueError) as error:
            return f"Error: {error}"

    @tool
    def read_file(path: str) -> str:
        """Read a text file from the current workspace.

        Args:
            path: Relative filename to read, such as app.py or tests/test_game.py.
        """
        try:
            target = safe_path(workspace, path)
            if not target.is_file():
                return f"Error: {path} does not exist."
            return target.read_text(encoding="utf-8")[:30000]
        except (OSError, ValueError, UnicodeError) as error:
            return f"Error: {error}"

    @tool
    def list_files(path: str = ".") -> str:
        """List files in the current workspace, including subfolders.

        Args:
            path: Relative folder to list; use '.' for the whole project.
        """
        try:
            folder = safe_path(workspace, path or ".")
            if not folder.is_dir():
                return "Error: folder does not exist."
            files = [f.relative_to(workspace).as_posix() for f in folder.rglob("*") if f.is_file()]
            return "\n".join(sorted(files)) or "Folder is empty."
        except (OSError, ValueError) as error:
            return f"Error: {error}"

    @tool
    def delete_file(path: str) -> str:
        """Delete one generated file from the current workspace.

        Args:
            path: Relative filename to delete.
        """
        nonlocal revision
        try:
            target = safe_path(workspace, path)
            if file_is_protected(target):
                return "Error: the fixed acceptance tests cannot be deleted."
            if not target.is_file():
                return "Error: file does not exist."
            target.unlink()
            revision += 1
            changed_files.add(target.relative_to(workspace).as_posix())
            return f"Deleted {path}."
        except (OSError, ValueError) as error:
            return f"Error: {error}"

    @tool
    def execute_file(path: str) -> str:
        """Execute a generated Python file in Docker and return its output.

        Args:
            path: Relative Python filename to execute, such as app.py.
        """
        try:
            target = safe_path(workspace, path)
            if target.suffix != ".py" or not target.is_file():
                return "Error: provide an existing Python file."
            relative = target.relative_to(workspace).as_posix()
            code, output = run_docker(workspace, [relative], timeout=15)
            return f"Exit code: {code}\n{output[-8000:]}"
        except (OSError, ValueError) as error:
            return f"Error: {error}"

    @tool
    def run_tests() -> str:
        """Run all Python test_*.py unit tests in Docker and report actual results."""
        status, count, exit_code, output = run_docker_tests(workspace)
        suites = {"python": {"status": status, "test_count": count, "exit_code": exit_code}}
        # HTML/CSS/JS-only projects are outside this Python-only benchmark.
        browser_files = [p for p in workspace.rglob("*") if p.is_file()
                         and p.suffix.lower() in {".html", ".htm", ".js", ".mjs", ".cjs"}]
        if status == "passed" and browser_files:
            status = "needs_review"
            output += ("\nPython unit tests passed, but browser/JavaScript behaviour "
                       "was not verified. This evaluation is Python-only.")
        version = version_numbers.setdefault(revision, len(version_numbers) + 1)
        changes = sorted(changed_files)

        test_history.append({
            "version": version,
            "revision": revision,
            "changed_files": changes,
            "status": status,
            "test_count": count,
            "exit_code": exit_code,
            "test_suites": suites,
            "output": output,
        })
        changed_files.clear()
        return f"Tests: {status} ({count} found).\n{output[-12000:]}"

    instructions = (
        "You are ONE coding agent responsible for planning, coding, testing, and fixing problems. "
        "You are not part of a multi-agent team and you do not use LangGraph. "
        "Use the file tools to build the user's project in the workspace. "
        "For this evaluation, implement tasks in Python and use Python's unittest framework only. "
        "You may create multiple Python files and supporting files with sensible filenames. "
        "Create meaningful behaviour tests named test_*.py, including tests/test_*.py. "
        "Use only Python standard-library dependencies; do not install packages. "
        "Use run_tests to execute these unit tests in Docker. "
        "If tests fail, inspect the failure and fix the implementation or an incorrect test, then rerun. "
        "Never remove or weaken a valid test merely to make it pass. "
        "Do not claim that Python tests verify browser or JavaScript behaviour. "
        "If Docker is unavailable, report the infrastructure failure instead of hiding it. "
        "You may use execute_file for Python scripts, but it does not replace run_tests. "
        "Do not claim files exist unless write_file confirms it. "
        "Do not claim tests passed unless run_tests passes for the latest files. "
        "Finish with a brief summary of generated files and the verified test outcome."
    )

    if repair_test:
        (workspace / "solution.py").write_text(BROKEN_SOLUTION, encoding="utf-8")
        (workspace / "test_repair.py").write_text(REPAIR_TESTS, encoding="utf-8")
        revision = 1
        status, count, exit_code, output = run_docker_tests(workspace)
        suites = {"python": {"status": status, "test_count": count, "exit_code": exit_code}}
        version_numbers[revision] = 1
        test_history.append({
            "version": 1, "revision": revision, "changed_files": ["solution.py"],
            "status": status, "test_count": count,
            "exit_code": exit_code, "test_suites": suites, "output": output,
        })
        print(f"Initial buggy code: {status} ({count} tests)")
        instructions += (
            " This is a controlled repair exercise. The fixed tests in test_repair.py "
            "cannot be edited. Read and fix solution.py, then call run_tests."
        )
        task += "\nInitial failed tests:\n" + output[-5000:]

    try:
        if repair_test and test_history[-1]["status"] != "failed":
            raise RuntimeError("The seeded repair test must fail before starting the agent.")
        model = create_llm_client()  # Same Gemini configuration as the hybrid.
        agent = ToolCallingAgent(
            model=model,
            tools=[write_file, read_file, list_files, delete_file, execute_file, run_tests],
            instructions=instructions,
            max_steps=30,
        )
        print("Single coding agent is working...")
        agent_answer = str(agent.run(task))
    except Exception as error:
        error_message = f"{type(error).__name__}: {error}"
        print("Agent error:", error_message)

    last_test = test_history[-1] if test_history else None
    if last_test and last_test["revision"] == revision:
        test_suites = last_test.get("test_suites", {})
        test_status = last_test["status"]
        test_count = last_test["test_count"]
        exit_code = last_test["exit_code"]
        test_output = last_test["output"]
    else:
        test_suites = {}
        test_status, test_count, exit_code = "not_run", 0, None
        test_output = "The latest files have not been tested."

    token_count = None
    if agent:
        try:
            counts = agent.monitor.get_total_token_counts()
            if isinstance(counts, dict):
                token_count = counts.get("total_tokens")
                if token_count is None and counts.get("input") is not None:
                    token_count = counts["input"] + counts.get("output", 0)
            else:
                token_count = getattr(counts, "total_tokens", None)
        except (AttributeError, TypeError, ValueError):
            pass

    all_files = sorted(
        f.relative_to(workspace).as_posix()
        for f in workspace.rglob("*") if f.is_file()
    )
    code_versions = len(version_numbers) + (1 if changed_files else 0)
    if error_message:
        overall_status = "failed"
    elif test_status == "passed":
        overall_status = "success"
    elif test_status in ("no_tests", "needs_review") and all_files:
        overall_status = "needs_review"
    else:
        overall_status = "failed"

    # Classify repairs from complete test history, not from any past failure.
    repaired, tests_repaired = classify_repairs(test_history)

    results = {
        "task": task.split("\nInitial failed tests:")[0],
        "run_type": "seeded_repair_test" if repair_test else "normal",
        "model": os.getenv("LLM_MODEL"),
        "total_time_seconds": round(time.perf_counter() - start, 2),
        "total_tokens": token_count,
        "test_status": test_status,
        "test_count": test_count,
        "test_exit_code": exit_code,
        "test_suites": test_suites,
        "attempts": code_versions,
        "test_runs": len(test_history),
        "self_repair": repaired,
        "test_repair": tests_repaired,
        "self_correction": repaired or tests_repaired,
        "browser_verified": False,
        "status": overall_status,
        "generated_files": all_files,
        "agent_answer": agent_answer,
        "error": error_message,
    }

    (output_dir / "result.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (output_dir / "test_history.json").write_text(json.dumps(test_history, indent=2), encoding="utf-8")
    (output_dir / "test_output.txt").write_text(test_output, encoding="utf-8")

    print("\nResult:", results["status"])
    print("Tests:", test_status, f"({test_count} found)")
    print("Code versions:", code_versions, "| Test runs:", len(test_history))
    print("Implementation self-repair:", repaired)
    print("Test correction:", tests_repaired)
    for language, suite in test_suites.items():
        print(f"{language.title()} tests: {suite['status']} ({suite['test_count']} found)")
    print("Total time:", results["total_time_seconds"], "seconds")
    print("Files saved to:", workspace)


if __name__ == "__main__":
    main()

"""One-shot coding baseline: generate code, run its tests once, and save results.

Run from the project folder:
    python src/baseline.py "Build a small Tic-Tac-Toe game"
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


def run_tests(output_dir):
    """Run the generated unit tests once inside Docker."""
    command = [
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
        "-v", f"{output_dir.resolve()}:/workspace:ro",
        "-w", "/workspace",
        "python:3.12-slim",
        "python", "-B", "-m", "unittest", "solution", "-v",
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        match = re.search(r"Ran (\d+) tests?", output)
        test_count = int(match.group(1)) if match else 0

        if result.returncode in (125, 126, 127):
            status = "not_run"  # Docker could not start the test container
        elif test_count == 0 and result.returncode == 0:
            status = "no_tests"
        elif result.returncode == 0:
            status = "passed"
        else:
            status = "failed"

        return status, test_count, result.returncode, output

    except subprocess.TimeoutExpired:
        return "timeout", 0, None, "Docker test run exceeded 60 seconds."
    except FileNotFoundError:
        return "not_run", 0, None, "Docker was not found. Check Docker Desktop."
    except OSError as error:
        return "not_run", 0, None, f"Could not start Docker: {error}"


def main():
    task = " ".join(sys.argv[1:]).strip()
    if not task:
        task = input("What would you like to build? ").strip()

    if not task:
        print("Please enter a coding task.")
        return

    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL")

    if not all([api_key, api_base, model]):
        print("Missing LLM settings in .env")
        return

    client = OpenAI(api_key=api_key, base_url=api_base, timeout=60)

    print("Generating code and tests with Gemini...")
    start = time.perf_counter()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a complete Python solution for the user's coding task. "
                    "Return only Python code for a single file called solution.py. "
                    "Include unit tests in the SAME file using Python's unittest module. "
                    "The tests must be methods starting with test_ in a unittest.TestCase class. "
                    "Put any interactive program or unittest.main() call inside "
                    "if __name__ == '__main__': so tests can run when imported. "
                    "Use only Python's standard library. No explanations or Markdown. "
                    "Do not claim you executed the code or tests."
                ),
            },
            {"role": "user", "content": task},
        ],
    )

    generation_time = round(time.perf_counter() - start, 2)
    code = (response.choices[0].message.content or "").strip()

    # Gemini sometimes wraps the code in Markdown fences.
    match = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()

    if not code:
        print("Gemini did not return any code.")
        return

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = PROJECT_DIR / "runtime" / "evaluation" / "baseline" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    code_file = output_dir / "solution.py"
    code_file.write_text(code + "\n", encoding="utf-8")

    print("Running generated tests once in Docker...")
    test_status, test_count, exit_code, test_output = run_tests(output_dir)
    (output_dir / "test_output.txt").write_text(test_output, encoding="utf-8")

    usage = response.usage
    results = {
        "task": task,
        "model": model,
        "generation_time_seconds": generation_time,
        "total_time_seconds": round(time.perf_counter() - start, 2),
        "total_tokens": usage.total_tokens if usage else None,
        "test_status": test_status,
        "test_count": test_count,
        "test_exit_code": exit_code,
        "attempts": 1,
        "self_repair": False,
    }
    (output_dir / "result.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    print("Code saved to:", code_file)
    print("Tests:", test_status, f"({test_count} found)")
    print("Total time:", results["total_time_seconds"], "seconds")
    print("Test details:", output_dir / "test_output.txt")
    print("No code repairs attempted (baseline).")


if __name__ == "__main__":
    main()

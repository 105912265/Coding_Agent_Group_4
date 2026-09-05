import subprocess
import sys
import tempfile
from pathlib import Path


def run_python(code: str) -> dict:
    """
    Execute Python code and return the execution result.
    """

    #creates temporary python directory where code to be executed it written and then run
    with tempfile.TemporaryDirectory() as temp_directory:

        file_path = Path(temp_directory) / "program.py"

        file_path.write_text(code, encoding="utf-8")

        try:
            #subprovesses allow a running python program to run invoke anothe puython program
            result = subprocess.run(
                [sys.executable, "-I", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=temp_directory
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Execution timed out.",
                "exit_code": None
            }
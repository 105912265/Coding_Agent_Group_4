"""
docker tool for running the code the agent writes

docker is only being used for the generated code here
the actual ai system is still just running normally
"""

import os
import subprocess
from smolagents import tool

from .file_manager import workspace_folder
from .file_manager import get_safe_path


def run_file(path: str) -> dict:
    """Run a workspace Python file in Docker and return execution details."""
    try:
        full_safe_path = get_safe_path(path)

        if os.path.isfile(full_safe_path) == False:
            return {"success": False, "stdout": "", "stderr": "python file doesnt exist", "exit_code": None}

        # docker sees the same workspace but at /workspace
        little_relative_path = os.path.relpath(full_safe_path, workspace_folder)

        docker_file_path = little_relative_path.replace("\\", "/")
        docker_file_path = "/workspace/" + docker_file_path

        # fairly basic sandbox limits for now
        docker_bits = [
            "docker",
            "run",
            "--rm",
            "--network", "none",
            "--memory", "128m",
            "--cpus", "0.5",
            "--pids-limit", "64",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-v", workspace_folder + ":/workspace:ro",
            "python:3.12-slim",
            "python",
            docker_file_path
        ]

        # actually runs the temporary container here
        docker_result = subprocess.run(
            docker_bits,
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "success": docker_result.returncode == 0,
            "stdout": docker_result.stdout,
            "stderr": docker_result.stderr,
            "exit_code": docker_result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Execution timed out.", "exit_code": None}

    except Exception as little_error:
        return {"success": False, "stdout": "", "stderr": str(little_error), "exit_code": None}


@tool
def execute_file(path: str) -> str:
    """
    runs a python file inside a temporary docker container

    Args:
        path: python file inside the workspace
    """
    result = run_file(path)
    if result["success"]:
        return "execution worked\noutput:\n" + result["stdout"]
    return "execution failed\nerrors:\n" + result["stderr"]

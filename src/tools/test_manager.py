from pathlib import Path

from smolagents import tool

from .file_manager import workspace_folder


@tool
def write_test_file(path: str, content: str) -> str:
    """
    Write a Python test under the workspace's tests folder.

    Args:
        path: Relative filename inside tests, such as test_solution.py.
        content: Complete Python test code.
    """
    try:
        workspace = Path(workspace_folder).resolve()
        tests_folder = (workspace / "tests").resolve()
        requested = Path(path)

        if requested.is_absolute() or requested.suffix != ".py":
            return "error: provide a relative Python test filename"

        target = (tests_folder / requested).resolve()

        if not tests_folder.is_relative_to(workspace):
            return "error: tests folder is outside the workspace"

        if not target.is_relative_to(tests_folder):
            return "error: test path is outside the tests folder"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return "saved test file: " + target.relative_to(workspace).as_posix()

    except Exception as error:
        return "error: " + str(error)
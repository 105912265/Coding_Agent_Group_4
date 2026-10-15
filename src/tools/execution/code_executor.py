from pathlib import Path
from uuid import uuid4

from tools.code_executor import run_file
from tools.file_manager import get_safe_path


def execute_code(code: str, language: str) -> dict:
    """Execute generated Python in the workspace using the Docker runner."""
    language = language.lower().strip()
    if language != "python":
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unsupported programming language: {language}",
            "exit_code": None,
        }

    relative_path = f"agent_run_{uuid4().hex}.py"
    file_path = Path(get_safe_path(relative_path))
    try:
        file_path.write_text(code, encoding="utf-8")
        return run_file(relative_path)
    except OSError as error:
        return {"success": False, "stdout": "", "stderr": str(error), "exit_code": None}
    finally:
        file_path.unlink(missing_ok=True)

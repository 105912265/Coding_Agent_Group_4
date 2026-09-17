"""
just the tool lists for each agent

kept here so agent_setup doesnt need to know where every single tool came from
"""

from .file_manager import read_file
from .file_manager import write_file
from .file_manager import list_files
from .file_manager import make_directory
from .file_manager import delete_file
from .code_executor import execute_file
from .test_manager import write_test_file



# coder gets the bigger tool set because it actually changes the project
CODER_TOOLS = [
    read_file,
    write_file,
    list_files,
    make_directory,
    delete_file,
    execute_file
]


# tester only needs to look at stuff and run it for now??
TESTER_TOOLS = [
    read_file,
    write_test_file,
    execute_file,
]

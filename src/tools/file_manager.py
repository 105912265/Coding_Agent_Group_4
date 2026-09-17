"""
basic file tools for the agents

nothing too fancy here, this just keeps the agent inside runtime/workspace
"""

import os
from smolagents import tool


# just figuring out where the project folders are
this_file = os.path.abspath(__file__)
tools_folder = os.path.dirname(this_file)
src_folder = os.path.dirname(tools_folder)
project_folder = os.path.dirname(src_folder)

workspace_folder = os.path.join(project_folder, "runtime", "workspace")
workspace_folder = os.path.abspath(workspace_folder)

# make it if it isnt there yet
os.makedirs(workspace_folder, exist_ok=True)


def get_safe_path(path):
    """gets the proper path but makes sure it stays in the workspace"""

    full_safe_path = os.path.abspath(os.path.join(workspace_folder, path))
    shared_folder = os.path.commonpath([workspace_folder, full_safe_path])

    # basically stops ../ stuff from escaping the workspace
    if shared_folder != workspace_folder:
        raise ValueError("path is outside the workspace")

    return full_safe_path


@tool
def read_file(path: str) -> str:
    """
    reads a text file from the workspace

    Args:
        path: the file path inside the workspace
    """

    try:
        full_safe_path = get_safe_path(path)

        if os.path.isfile(full_safe_path) == False:
            return "error: file doesnt exist"

        opened_file = open(full_safe_path, "r", encoding="utf-8")
        file_text = opened_file.read()
        opened_file.close()

        return file_text

    except Exception as little_error:
        return "error: " + str(little_error)


@tool
def write_file(path: str, content: str) -> str:
    """
    writes text into a file in the workspace

    Args:
        path: the file path inside the workspace
        content: the text/code to put in the file
    """

    try:
        full_safe_path = get_safe_path(path)

        parent_folder = os.path.dirname(full_safe_path)

        # makes missing folders on the way if needed
        os.makedirs(parent_folder, exist_ok=True)

        opened_file = open(full_safe_path, "w", encoding="utf-8")
        opened_file.write(content)
        opened_file.close()

        return "saved file: " + path

    except Exception as little_error:
        return "error: " + str(little_error)


@tool
def list_files(path: str = ".") -> str:
    """
    lists whats inside a workspace folder

    Args:
        path: folder inside the workspace, "." means the main workspace folder
    """

    try:
        full_safe_path = get_safe_path(path)

        if os.path.isdir(full_safe_path) == False:
            return "error: folder doesnt exist"

        folder_items = os.listdir(full_safe_path)

        if len(folder_items) == 0:
            return "folder is empty"

        simple_list = ""

        for little_item in folder_items:
            simple_list = simple_list + little_item + "\n"

        return simple_list

    except Exception as little_error:
        return "error: " + str(little_error)


@tool
def make_directory(path: str) -> str:
    """
    makes a folder in the workspace

    Args:
        path: folder path to make
    """

    try:
        full_safe_path = get_safe_path(path)

        os.makedirs(full_safe_path, exist_ok=True)

        return "made folder: " + path

    except Exception as little_error:
        return "error: " + str(little_error)


@tool
def delete_file(path: str) -> str:
    """
    deletes one file from the workspace

    Args:
        path: file path to delete
    """

    try:
        full_safe_path = get_safe_path(path)

        if os.path.isfile(full_safe_path) == False:
            return "error: file doesnt exist"

        os.remove(full_safe_path)

        return "deleted file: " + path

    except Exception as little_error:
        return "error: " + str(little_error)

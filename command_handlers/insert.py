import os
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

DELIMITER = 10 * "-"

# TODO : add rate limiting


def read_file_content(file_path: str) -> str:
    """
    Reads the content of a file given its path.

    Parameters:
    ----------
    file_path : str
        The path of the file to read the content from.

    Returns:
    -------
    str
        The content of the file if found, otherwise an error message.
    """
    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        error_message = f"ERROR! The file '{file_path}' does not exist."
        logging.error(error_message)
        return error_message


def insert_from_file(filename: str) -> str:
    """
    Inserts content from a file. Checks both relative and absolute paths for the file.

    Parameters:
    ----------
    filename : str
        The name of the file to read the content from.

    Returns:
    -------
    str
        The content of the file if found, otherwise an error message.
    """
    # Check if the file exists using relative path
    if os.path.isfile(filename):
        return read_file_content(filename)
    else:
        # Attempt to use absolute path
        abs_path = os.path.abspath(filename)
        return read_file_content(abs_path)


def process_file(file_path: str) -> str:
    """
    Processes a single file by reading its content and formatting it.

    Parameters:
    ----------
    file_path : str
        The path of the file to process.

    Returns:
    -------
    str
        The formatted content of the file.
    """
    return f"[{file_path}]\n{insert_from_file(file_path)}\n{DELIMITER}"


def handle_insert_command(parameters: List[Tuple[str, List[str]]]) -> str:
    """
    Handles the 'insert' command, processing both 'filename' and 'directory' parameters.

    Parameters:
    ----------
    parameters : list of tuple
        The parameters for the 'insert' command in the form of a list of tuples.
        Each tuple contains a parameter name and a list of values.

    Returns:
    -------
    str
        The concatenated content of the files if found, otherwise an error message.
    """
    file_content_list = []

    # Convert the list of tuples to a dictionary for easy lookup
    param_dict = {param[0]: param[1][0] for param in parameters}

    if "directory" in param_dict:
        directory = param_dict["directory"]
        if os.path.isdir(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_content_list.append(process_file(file_path))
        else:
            error_message = f"ERROR! The directory '{directory}' does not exist."
            logging.error(error_message)
            return error_message
    else:
        if "filename" in param_dict:
            file_content_list.append(process_file(param_dict["filename"]))
        elif "file" in param_dict:
            file_content_list.append(process_file(param_dict["file"]))

    # Join all file contents with double newlines
    return "\n\n".join(file_content_list)

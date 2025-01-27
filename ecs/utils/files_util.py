import os


def write_to_file(file_path: str, content: str):
    """
    Write the given content to a file at the specified file path.

    Args:
        file_path (str): The path to the file.
        content (str): The content to write to the file.
    """
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, 'w') as file:
            file.write(content)

        print(f"Successfully wrote content to {file_path}")
    except IOError as e:
        print(f"An error occurred while writing to file: {e}")


def append_to_file(file_path: str, content: str):
    """
    Append the given content to a file as a new line at the specified file path.

    Args:
        file_path (str): The path to the file.
        content (str): The content to append to the file.
    """
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, 'a') as file:
            file.write('\n' + content)

        print(f"Successfully appended content to {file_path}")
    except IOError as e:
        print(f"An error occurred while appending to file: {e}")

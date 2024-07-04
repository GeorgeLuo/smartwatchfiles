import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from command_handlers.insert import read_file_content, insert_from_file, process_file, handle_insert_command


class TestInsertHandlers(unittest.TestCase):

    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open, read_data="file content")
    def test_read_file_content_file_exists(self, mock_open, mock_isfile):
        mock_isfile.return_value = True
        result = read_file_content('dummy_path')
        self.assertEqual(result, "file content")
        mock_open.assert_called_once_with('dummy_path', 'r', encoding='utf-8')

    @patch('os.path.isfile')
    def test_read_file_content_file_not_exists(self, mock_isfile):
        mock_isfile.return_value = False
        result = read_file_content('dummy_path')
        self.assertIn("ERROR! The file 'dummy_path' does not exist.", result)

    @patch('os.path.isfile')
    @patch('command_handlers.insert.read_file_content')
    def test_insert_from_file_relative_path(self, mock_read_file_content, mock_isfile):
        mock_isfile.return_value = True
        mock_read_file_content.return_value = "file content"
        result = insert_from_file('dummy_path')
        self.assertEqual(result, "file content")
        mock_read_file_content.assert_called_once_with('dummy_path')

    @patch('os.path.isfile')
    @patch('os.path.abspath')
    @patch('command_handlers.insert.read_file_content')
    def test_insert_from_file_absolute_path(self, mock_read_file_content, mock_abspath, mock_isfile):
        mock_isfile.side_effect = [False, True]
        mock_abspath.return_value = '/abs/dummy_path'
        mock_read_file_content.return_value = "file content"
        result = insert_from_file('dummy_path')
        self.assertEqual(result, "file content")
        mock_read_file_content.assert_called_once_with('/abs/dummy_path')

    @patch('command_handlers.insert.insert_from_file')
    def test_process_file(self, mock_insert_from_file):
        mock_insert_from_file.return_value = "file content"
        result = process_file('dummy_path')
        self.assertEqual(result, "[dummy_path]\nfile content\n----------")

    @patch('os.path.isdir')
    @patch('os.walk')
    @patch('command_handlers.insert.process_file')
    def test_handle_insert_command_directory(self, mock_process_file, mock_os_walk, mock_isdir):
        mock_isdir.return_value = True
        mock_os_walk.return_value = [
            ('/root', ('subdir',), ('file1', 'file2'))]
        mock_process_file.side_effect = lambda x: f"processed {x}"
        parameters = [('directory', ['dummy_dir'])]
        result = handle_insert_command(parameters)
        self.assertIn("processed /root/file1", result)
        self.assertIn("processed /root/file2", result)

    @patch('command_handlers.insert.process_file')
    def test_handle_insert_command_filename(self, mock_process_file):
        mock_process_file.return_value = "processed file"
        parameters = [('filename', ['dummy_file'])]
        result = handle_insert_command(parameters)
        self.assertEqual(result, "processed file")

    @patch('command_handlers.insert.process_file')
    def test_handle_insert_command_file(self, mock_process_file):
        mock_process_file.return_value = "processed file"
        parameters = [('file', ['dummy_file'])]
        result = handle_insert_command(parameters)
        self.assertEqual(result, "processed file")

    @patch('os.path.isdir')
    def test_handle_insert_command_directory_not_exists(self, mock_isdir):
        mock_isdir.return_value = False
        parameters = [('directory', ['dummy_dir'])]
        result = handle_insert_command(parameters)
        self.assertIn(
            "ERROR! The directory 'dummy_dir' does not exist.", result)


if __name__ == '__main__':
    unittest.main()

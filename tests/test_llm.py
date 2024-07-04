import unittest
from unittest.mock import patch, mock_open, MagicMock
from command_handlers.llm import (
    build_query, append_file_contents_to_query, extract_code_blocks,
    call_llm, is_rate_limited, should_extract_code, call_llm_api, Model
)
import command_handlers.llm


class TestLLMHandlers(unittest.TestCase):

    def setUp(self):
        self.model = Model(name='gpt-3.5-turbo', api_key='test_api_key')
        self.instruction = "Translate the following text to French."
        self.parameters = [("file", ["test_file.txt"]), ("extract", ["code"])]

    @patch("builtins.open", new_callable=mock_open, read_data="file content")
    def test_append_file_contents_to_query(self):
        query = "Initial query"
        updated_query = append_file_contents_to_query(query, self.parameters)
        self.assertIn("file content", updated_query)

    def test_build_query(self):
        query, key = build_query(
            self.instruction, self.parameters, self.model.name)
        self.assertIn(self.instruction, query)
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 32)  # MD5 hash length

    def test_extract_code_blocks(self):
        rendered_text = "Here is some code:\n```python\nprint('Hello, world!')\n```"
        extracted_code = extract_code_blocks(rendered_text)
        self.assertIn("print('Hello, world!')", extracted_code)

    @patch("command_handlers.llm.time.time", return_value=100)
    def test_is_rate_limited(self, mock_time):
        command_handlers.llm.last_call_time = 95
        self.assertTrue(is_rate_limited(100))
        command_handlers.llm.last_call_time = 90
        self.assertTrue(is_rate_limited(100))
        command_handlers.llm.last_call_time = 80
        self.assertFalse(is_rate_limited(100))

    def test_should_extract_code(self):
        self.assertTrue(should_extract_code(self.parameters))
        self.assertFalse(should_extract_code([("param", ["value"])]))

    @patch("command_handlers.llm.OpenAI")
    def test_call_llm_api(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "API response"
        mock_client.chat.completions.create.return_value = mock_response

        response = call_llm_api(self.model, "query")
        self.assertEqual(response, "API response")

    @patch("command_handlers.llm.call_llm_api", return_value="API response")
    @patch("command_handlers.llm.time.time", return_value=100)
    def test_call_llm(self):
        self.parameters = []
        command_handlers.llm.last_call_time = 80
        error, response = call_llm(
            self.instruction, self.parameters, self.model)
        self.assertFalse(error)
        self.assertEqual(response, "API response")

    @patch("command_handlers.llm.call_llm_api", side_effect=Exception("API error"))
    @patch("command_handlers.llm.time.time", return_value=100)
    def test_call_llm_with_exception(self):
        self.parameters = []
        command_handlers.llm.last_call_time = 80
        error, response = call_llm(
            self.instruction, self.parameters, self.model)
        self.assertTrue(error)
        self.assertIn("Error: API error", response)

    @patch("command_handlers.llm.is_rate_limited", return_value=True)
    def test_call_llm_rate_limited(self):
        error, response = call_llm(
            self.instruction, self.parameters, self.model)
        self.assertTrue(error)
        self.assertEqual(response, '<LLM RATE LIMIT>')


if __name__ == '__main__':
    unittest.main()

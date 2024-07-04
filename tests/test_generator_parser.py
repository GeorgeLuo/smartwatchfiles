import unittest
from ecs.utils.generator_parser import (
    split_into_sections,
    parse_section,
    is_command_section,
    parse_command_section,
    split_command_line,
    extract_parameters,
    parse_sections
)


class TestGeneratorParser(unittest.TestCase):

    def test_split_into_sections(self):
        content = "Section 1\n\nSection 2\n\nSection 3"
        expected = [{'raw_text': 'Section 1'}, {
            'raw_text': 'Section 2'}, {'raw_text': 'Section 3'}]
        self.assertEqual(split_into_sections(content), expected)

    def test_parse_section_text(self):
        section = {'raw_text': 'This is a text section.'}
        expected = {'section_type': 'text',
                    'raw_text': 'This is a text section.'}
        self.assertEqual(parse_section(section), expected)

    def test_parse_section_command(self):
        section = {
            'raw_text': '?command Do something\nparam1=value1\nparam2=value2\n.'}
        expected = {
            'section_type': 'command',
            'command': 'command',
            'instruction': 'Do something',
            'parameters': {'param1': 'value1', 'param2': 'value2'},
            'raw_text': '?command Do something\nparam1=value1\nparam2=value2\n.'
        }
        self.assertEqual(parse_section(section), expected)

    def test_is_command_section(self):
        self.assertTrue(is_command_section('?command Do something\n.'))
        self.assertFalse(is_command_section('This is a text section.'))

    def test_parse_command_section(self):
        raw_text = '?command Do something\nparam1=value1\nparam2=value2\n.'
        expected = {
            'section_type': 'command',
            'command': 'command',
            'instruction': 'Do something',
            'parameters': {'param1': 'value1', 'param2': 'value2'},
            'raw_text': raw_text
        }
        self.assertEqual(parse_command_section(raw_text), expected)

    def test_split_command_line(self):
        command_line = 'command Do something'
        expected = ('command', 'Do something')
        self.assertEqual(split_command_line(command_line), expected)

    def test_extract_parameters(self):
        lines = ['param1=value1', 'param2=value2']
        expected = {'param1': 'value1', 'param2': 'value2'}
        self.assertEqual(extract_parameters(lines), expected)

    def test_parse_sections(self):
        sections = [
            {'raw_text': 'This is a text section.'},
            {'raw_text': '?command Do something\nparam1=value1\nparam2=value2\n.'}
        ]
        expected = [
            {'section_type': 'text', 'raw_text': 'This is a text section.'},
            {
                'section_type': 'command',
                'command': 'command',
                'instruction': 'Do something',
                'parameters': {'param1': 'value1', 'param2': 'value2'},
                'raw_text': '?command Do something\nparam1=value1\nparam2=value2\n.'
            }
        ]
        self.assertEqual(parse_sections(sections), expected)

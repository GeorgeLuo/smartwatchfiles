import unittest
from models.section import Section, parse_section, parse_lines, handle_start_state, handle_command_state, handle_parameters_state, handle_text_state, add_parameter


class TestSection(unittest.TestCase):

    def test_section_initialization(self):
        section = Section(
            raw_text="Sample text",
            opening_labels=["label1"],
            closing_labels=["label2"],
            section_type=Section.SectionType.TEXT,
            command="sample_command",
            instruction="sample_instruction",
            parameters=[("param1", ["value1"])],
            text_content="Sample text content"
        )
        self.assertEqual(section.raw_text, "Sample text")
        self.assertEqual(section.opening_labels, ["label1"])
        self.assertEqual(section.closing_labels, ["label2"])
        self.assertEqual(section.section_type, Section.SectionType.TEXT)
        self.assertEqual(section.command, "sample_command")
        self.assertEqual(section.instruction, "sample_instruction")
        self.assertEqual(section.parameters, [("param1", ["value1"])])
        self.assertEqual(section.text_content, "Sample text content")

    def test_section_equality(self):
        section1 = Section(
            raw_text="Sample text",
            opening_labels=["label1"],
            closing_labels=["label2"],
            section_type=Section.SectionType.TEXT,
            command="sample_command",
            instruction="sample_instruction",
            parameters=[("param1", ["value1"])],
            text_content="Sample text content"
        )
        section2 = Section(
            raw_text="Sample text",
            opening_labels=["label1"],
            closing_labels=["label2"],
            section_type=Section.SectionType.TEXT,
            command="sample_command",
            instruction="sample_instruction",
            parameters=[("param1", ["value1"])],
            text_content="Sample text content"
        )
        self.assertEqual(section1, section2)

    def test_parse_section_text(self):
        input_text = "/label1\nThis is a text section.\n\\label2"
        section = parse_section(input_text)
        self.assertEqual(section.raw_text, input_text)
        self.assertEqual(section.opening_labels, ["label1"])
        self.assertEqual(section.closing_labels, ["label2"])
        self.assertEqual(section.section_type, Section.SectionType.TEXT)
        self.assertIsNone(section.command)
        self.assertIsNone(section.instruction)
        self.assertEqual(section.parameters, [])
        self.assertEqual(section.text_content, "This is a text section.")

    def test_parse_section_command(self):
        input_text = "/label1\n?command\nparam1=value1\nparam2=value2\n\\label2"
        section = parse_section(input_text)
        self.assertEqual(section.raw_text, input_text)
        self.assertEqual(section.opening_labels, ["label1"])
        self.assertEqual(section.closing_labels, ["label2"])
        self.assertEqual(section.section_type, Section.SectionType.COMMAND)
        self.assertEqual(section.command, "command")
        self.assertIsNone(section.instruction)
        self.assertEqual(section.parameters, [
                         ("param1", ["value1"]), ("param2", ["value2"])])
        self.assertIsNone(section.text_content)

    def test_add_parameter(self):
        parameters = []
        parameters = add_parameter(parameters, "param1", "value1")
        parameters = add_parameter(parameters, "param1", "value2")
        parameters = add_parameter(parameters, "param2", "value3")
        self.assertEqual(
            parameters, [("param1", ["value1", "value2"]), ("param2", ["value3"])])

    def test_handle_start_state(self):
        state, section_type, command, instruction, opening_labels, text_content, replay = handle_start_state(
            "/label1", None, None, [], [], [])
        self.assertEqual(state, 'start')
        self.assertEqual(opening_labels, ["label1"])
        self.assertFalse(replay)

        state, section_type, command, instruction, opening_labels, text_content, replay = handle_start_state(
            "?command", None, None, [], [], [])
        self.assertEqual(state, 'command')
        self.assertEqual(section_type, Section.SectionType.COMMAND)
        self.assertEqual(command, "command")
        self.assertFalse(replay)

        state, section_type, command, instruction, opening_labels, text_content, replay = handle_start_state(
            "This is a text section.", None, None, [], [], [])
        self.assertEqual(state, 'text')
        self.assertEqual(section_type, Section.SectionType.TEXT)
        self.assertEqual(text_content, ["This is a text section."])
        self.assertFalse(replay)

    def test_handle_command_state(self):
        state, parameters, instruction, replay = handle_command_state(
            "param1=value1", [], [])
        self.assertEqual(state, 'parameters')
        self.assertEqual(parameters, [("param1", ["value1"])])
        self.assertFalse(replay)

        state, parameters, instruction, replay = handle_command_state(
            "Additional instruction", [], [])
        self.assertEqual(state, 'command')
        self.assertEqual(instruction, ["Additional instruction"])
        self.assertFalse(replay)

    def test_handle_parameters_state(self):
        state, parameters, closing_labels, replay = handle_parameters_state(
            "param1=value1", [], [])
        self.assertEqual(state, 'parameters')
        self.assertEqual(parameters, [("param1", ["value1"])])
        self.assertFalse(replay)

        state, parameters, closing_labels, replay = handle_parameters_state(
            "\\label2", [], [])
        self.assertEqual(state, 'parameters')
        self.assertEqual(closing_labels, ["label2"])
        self.assertFalse(replay)

    def test_handle_text_state(self):
        state, closing_labels, text_content, replay = handle_text_state(
            "\\label2", [], [])
        self.assertEqual(state, 'text')
        self.assertEqual(closing_labels, ["label2"])
        self.assertFalse(replay)

        state, closing_labels, text_content, replay = handle_text_state(
            "This is a text section.", [], [])
        self.assertEqual(state, 'text')
        self.assertEqual(text_content, ["This is a text section."])
        self.assertFalse(replay)


if __name__ == '__main__':
    unittest.main()

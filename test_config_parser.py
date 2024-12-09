import unittest
from config_parser import ConfigParser, ConfigParserError, remove_comments

class TestConfigParser(unittest.TestCase):
    def test_basic_parsing(self):
        input_text = """
        var name := [[Test]]
        var value := 123
        .{name}.
        """
        parser = ConfigParser(remove_comments(input_text))
        result = parser.parse()
        expected = {
            "variables": {
                "name": "Test",
                "value": 123
            },
            "_result": "Test"
        }
        self.assertEqual(result, expected)

    def test_array_parsing(self):
        input_text = "array(1, 2, 3, [[four]])"
        parser = ConfigParser(remove_comments(input_text))
        result = parser.parse()
        expected = {
            "variables": {},
            "_result": [1, 2, 3, "four"]
        }
        self.assertEqual(result, expected)

    def test_comments_removal(self):
        input_text = """
        || This is a comment
        var a := 10
        /+ Multi-line
        comment +/
        var b := .{a}.
        """
        parser = ConfigParser(remove_comments(input_text))
        result = parser.parse()
        expected = {
            "variables": {
                "a": 10,
                "b": 10
            }
        }
        self.assertEqual(result, expected)

    def test_const_ref(self):
        input_text = """
        var greeting := [[Hello]]
        var message := [[Greeting: .{greeting}.]]
        .{message}.
        """
        parser = ConfigParser(remove_comments(input_text))
        result = parser.parse()
        expected = {
            "variables": {
                "greeting": "Hello",
                "message": "Greeting: Hello"
            },
            "_result": "Greeting: Hello"
        }
        self.assertEqual(result, expected)

    def test_syntax_error_missing_var(self):
        input_text = "name := [[Test]]"  # Missing 'var' keyword
        parser = ConfigParser(remove_comments(input_text))
        with self.assertRaises(ConfigParserError):
            parser.parse()

    def test_syntax_error_unclosed_string(self):
        input_text = "var name := [[Test"
        parser = ConfigParser(remove_comments(input_text))
        with self.assertRaises(ConfigParserError):
            parser.parse()

    def test_syntax_error_invalid_const_ref(self):
        input_text = "var message := .{undefined}."
        parser = ConfigParser(remove_comments(input_text))
        with self.assertRaises(ConfigParserError):
            parser.parse()

if __name__ == '__main__':
    unittest.main()

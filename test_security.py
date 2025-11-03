"""
Security test suite for input validation and sanitization.
Tests various attack vectors and validation scenarios.
"""

import unittest
import sys
from security import SecurityValidator, ValidationError, RateLimiter


class TestSecurityValidator(unittest.TestCase):
    """Test cases for SecurityValidator."""
    
    def test_sanitize_string_valid(self):
        """Test sanitizing valid strings."""
        result = SecurityValidator.sanitize_string("Hello World")
        self.assertEqual(result, "Hello World")
        
        result = SecurityValidator.sanitize_string("Test with spaces and 123")
        self.assertEqual(result, "Test with spaces and 123")
    
    def test_sanitize_string_html_escape(self):
        """Test HTML escaping in string sanitization."""
        # XSS patterns should be blocked by dangerous pattern detection
        with self.assertRaises(ValidationError):
            SecurityValidator.sanitize_string("<script>alert('xss')</script>")
    
    def test_sanitize_string_length_limit(self):
        """Test string length validation."""
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.sanitize_string("x" * 20000, max_length=1000)
        self.assertIn("too long", str(context.exception))
    
    def test_sanitize_string_dangerous_patterns(self):
        """Test detection of dangerous patterns."""
        dangerous_inputs = [
            "test; rm -rf /",
            "$(whoami)",
            "test | cat /etc/passwd",
            "../../../etc/passwd",
            "javascript:alert(1)",
            "eval(malicious_code)",
        ]
        
        for dangerous in dangerous_inputs:
            with self.assertRaises(ValidationError) as context:
                SecurityValidator.sanitize_string(dangerous)
            self.assertIn("dangerous", str(context.exception).lower())
    
    def test_sanitize_string_invalid_type(self):
        """Test string validation with invalid types."""
        with self.assertRaises(ValidationError):
            SecurityValidator.sanitize_string(123)
        
        with self.assertRaises(ValidationError):
            SecurityValidator.sanitize_string(None)
    
    def test_validate_integer_valid(self):
        """Test validating valid integers."""
        result = SecurityValidator.validate_integer(42)
        self.assertEqual(result, 42)
        
        result = SecurityValidator.validate_integer("123")
        self.assertEqual(result, 123)
        
        result = SecurityValidator.validate_integer(-50)
        self.assertEqual(result, -50)
    
    def test_validate_integer_bounds(self):
        """Test integer bounds checking."""
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_integer(2000000)
        self.assertIn("too large", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_integer(-2000000)
        self.assertIn("too small", str(context.exception))
    
    def test_validate_integer_custom_bounds(self):
        """Test integer validation with custom bounds."""
        result = SecurityValidator.validate_integer(25, minimum=1, maximum=50)
        self.assertEqual(result, 25)
        
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_integer(100, minimum=1, maximum=50)
    
    def test_validate_integer_invalid_type(self):
        """Test integer validation with invalid types."""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_integer("not a number")
        
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_integer(True)  # Boolean not allowed
    
    def test_validate_number_valid(self):
        """Test validating valid numbers."""
        result = SecurityValidator.validate_number(3.14)
        self.assertEqual(result, 3.14)
        
        result = SecurityValidator.validate_number("42.5")
        self.assertEqual(result, 42.5)
    
    def test_validate_number_special_values(self):
        """Test number validation with special values."""
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_number(float('inf'))
        self.assertIn("Infinity", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_number(float('nan'))
        self.assertIn("NaN", str(context.exception))
    
    def test_validate_number_bounds(self):
        """Test number bounds checking."""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_number(1e15)
        
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_number(-1e15)
    
    def test_validate_enum_valid(self):
        """Test enum validation with valid values."""
        result = SecurityValidator.validate_enum("add", ["add", "subtract", "multiply"])
        self.assertEqual(result, "add")
    
    def test_validate_enum_invalid(self):
        """Test enum validation with invalid values."""
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_enum("invalid", ["add", "subtract"])
        self.assertIn("Must be one of", str(context.exception))
    
    def test_validate_enum_wrong_type(self):
        """Test enum validation with wrong type."""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_enum(123, ["add", "subtract"])
    
    def test_validate_object_depth_valid(self):
        """Test object depth validation with valid objects."""
        obj = {"a": {"b": {"c": "value"}}}
        SecurityValidator.validate_object_depth(obj, max_depth=10)
    
    def test_validate_object_depth_exceeded(self):
        """Test object depth validation with excessive nesting."""
        # Create deeply nested object
        obj = {"level": 1}
        current = obj
        for i in range(15):
            current["nested"] = {"level": i + 2}
            current = current["nested"]
        
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_object_depth(obj, max_depth=10)
        self.assertIn("too deep", str(context.exception))
    
    def test_validate_json_size_valid(self):
        """Test JSON size validation with valid size."""
        json_str = '{"test": "value"}'
        SecurityValidator.validate_json_size(json_str, max_size=1024)
    
    def test_validate_json_size_exceeded(self):
        """Test JSON size validation with excessive size."""
        json_str = "x" * 10000
        with self.assertRaises(ValidationError) as context:
            SecurityValidator.validate_json_size(json_str, max_size=100)
        self.assertIn("too large", str(context.exception))
    
    def test_validate_tool_name_valid(self):
        """Test tool name validation with valid names."""
        result = SecurityValidator.validate_tool_name("calculate")
        self.assertEqual(result, "calculate")
        
        result = SecurityValidator.validate_tool_name("text_analyzer")
        self.assertEqual(result, "text_analyzer")
        
        result = SecurityValidator.validate_tool_name("_private_tool")
        self.assertEqual(result, "_private_tool")
    
    def test_validate_tool_name_invalid(self):
        """Test tool name validation with invalid names."""
        invalid_names = [
            "tool-name",  # hyphens not allowed
            "tool name",  # spaces not allowed
            "123tool",    # cannot start with number
            "tool.name",  # dots not allowed
            "tool;drop",  # semicolons not allowed
            "../etc",     # path traversal
        ]
        
        for invalid in invalid_names:
            with self.assertRaises(ValidationError):
                SecurityValidator.validate_tool_name(invalid)
    
    def test_validate_tool_name_too_long(self):
        """Test tool name validation with excessive length."""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_tool_name("x" * 200)


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter."""
    
    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            self.assertTrue(limiter.is_allowed("test_client"))
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Use up the limit
        for i in range(3):
            self.assertTrue(limiter.is_allowed("test_client_2"))
        
        # Next request should be blocked
        self.assertFalse(limiter.is_allowed("test_client_2"))
    
    def test_rate_limiter_different_clients(self):
        """Test that different clients have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        self.assertTrue(limiter.is_allowed("client_a"))
        self.assertTrue(limiter.is_allowed("client_b"))
        self.assertTrue(limiter.is_allowed("client_a"))
        self.assertTrue(limiter.is_allowed("client_b"))


class TestCommandInjectionPrevention(unittest.TestCase):
    """Test cases specifically for command injection prevention."""
    
    def test_shell_metacharacters_blocked(self):
        """Test that shell metacharacters are blocked."""
        dangerous_chars = [";", "|", "&", "`", "$", "(", ")", "{", "}"]
        
        for char in dangerous_chars:
            test_input = f"test{char}malicious"
            with self.assertRaises(ValidationError):
                SecurityValidator.sanitize_string(test_input)
    
    def test_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        path_traversals = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "./../secret",
        ]
        
        for traversal in path_traversals:
            with self.assertRaises(ValidationError):
                SecurityValidator.sanitize_string(traversal)
    
    def test_code_injection_patterns_blocked(self):
        """Test that code injection patterns are blocked."""
        injection_attempts = [
            "eval(malicious)",
            "exec(dangerous)",
            "__import__('os').system('rm -rf /')",
            "import os; os.system('pwd')",
        ]
        
        for attempt in injection_attempts:
            with self.assertRaises(ValidationError):
                SecurityValidator.sanitize_string(attempt)
    
    def test_xss_patterns_blocked(self):
        """Test that XSS patterns are blocked and escaped."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<body onload=alert(1)>",
        ]
        
        for attempt in xss_attempts:
            # Should either raise error or escape
            try:
                result = SecurityValidator.sanitize_string(attempt)
                # If not raising error, should be escaped
                self.assertNotIn("<script>", result.lower())
                self.assertNotIn("javascript:", result.lower())
            except ValidationError:
                # Raising error is also acceptable
                pass


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary conditions and edge cases."""
    
    def test_empty_string(self):
        """Test handling of empty strings."""
        result = SecurityValidator.sanitize_string("")
        self.assertEqual(result, "")
    
    def test_zero_values(self):
        """Test handling of zero values."""
        result = SecurityValidator.validate_integer(0)
        self.assertEqual(result, 0)
        
        result = SecurityValidator.validate_number(0.0)
        self.assertEqual(result, 0.0)
    
    def test_negative_values(self):
        """Test handling of negative values."""
        result = SecurityValidator.validate_integer(-42)
        self.assertEqual(result, -42)
        
        result = SecurityValidator.validate_number(-3.14)
        self.assertEqual(result, -3.14)
    
    def test_boundary_integers(self):
        """Test integers at boundaries."""
        # Test at max boundary
        result = SecurityValidator.validate_integer(1000000)
        self.assertEqual(result, 1000000)
        
        # Test at min boundary
        result = SecurityValidator.validate_integer(-1000000)
        self.assertEqual(result, -1000000)
    
    def test_unicode_strings(self):
        """Test handling of unicode strings."""
        unicode_strings = [
            "Hello 世界",
            "Привет мир",
            "مرحبا العالم",
            "🌍🌎🌏",
        ]
        
        for s in unicode_strings:
            result = SecurityValidator.sanitize_string(s)
            self.assertIsInstance(result, str)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

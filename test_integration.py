"""
Integration tests for MCP Server Flask application.
Tests API endpoints with security validations.
"""

import unittest
import json
from app import app
from security import rate_limit_storage


class TestFlaskIntegration(unittest.TestCase):
    """Integration tests for Flask application."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        # Clear rate limit storage
        rate_limit_storage.clear()
    
    def tearDown(self):
        """Clean up after tests."""
        rate_limit_storage.clear()
    
    def test_index_route(self):
        """Test the index route returns HTML."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MCP Server', response.data)
    
    def test_get_tools_endpoint(self):
        """Test the /api/tools endpoint."""
        response = self.client.get('/api/tools')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        
        # Check first tool has required fields
        tool = data[0]
        self.assertIn('name', tool)
        self.assertIn('description', tool)
        self.assertIn('parameters', tool)
    
    def test_get_server_info_endpoint(self):
        """Test the /api/server-info endpoint."""
        response = self.client.get('/api/server-info')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('name', data)
        self.assertIn('version', data)
        self.assertIn('tool_count', data)
    
    def test_execute_tool_valid_request(self):
        """Test executing a tool with valid parameters."""
        payload = {
            "tool_name": "calculate",
            "parameters": {
                "operation": "add",
                "a": 10,
                "b": 5
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('result'), 15)
    
    def test_execute_tool_missing_tool_name(self):
        """Test executing without tool_name."""
        payload = {
            "parameters": {"a": 10, "b": 5}
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_execute_tool_invalid_json(self):
        """Test executing with invalid JSON."""
        response = self.client.post(
            '/api/execute',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_execute_tool_non_json_content(self):
        """Test executing with non-JSON content type."""
        response = self.client.post(
            '/api/execute',
            data='some data',
            content_type='text/plain'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Content-Type', data.get('error', ''))
    
    def test_execute_tool_invalid_tool_name(self):
        """Test executing with invalid tool name."""
        payload = {
            "tool_name": "nonexistent_tool",
            "parameters": {}
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('not found', data['error'])
    
    def test_execute_tool_dangerous_tool_name(self):
        """Test executing with dangerous tool name patterns."""
        dangerous_names = [
            "tool; rm -rf /",
            "../../../etc/passwd",
            "tool$(whoami)",
            "eval(code)",
        ]
        
        for dangerous_name in dangerous_names:
            payload = {
                "tool_name": dangerous_name,
                "parameters": {}
            }
            
            response = self.client.post(
                '/api/execute',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Should return error
            data = json.loads(response.data)
            self.assertIn('error', data)
    
    def test_execute_tool_missing_required_params(self):
        """Test executing with missing required parameters."""
        payload = {
            "tool_name": "calculate",
            "parameters": {
                "operation": "add"
                # Missing 'a' and 'b'
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_execute_tool_invalid_enum_value(self):
        """Test executing with invalid enum value."""
        payload = {
            "tool_name": "calculate",
            "parameters": {
                "operation": "invalid_operation",
                "a": 10,
                "b": 5
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_execute_tool_text_analyzer_valid(self):
        """Test text analyzer tool with valid input."""
        payload = {
            "tool_name": "text_analyzer",
            "parameters": {
                "text": "Hello world! This is a test."
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('statistics', data)
    
    def test_execute_tool_dangerous_text_input(self):
        """Test text analyzer with dangerous input patterns."""
        dangerous_texts = [
            "test; rm -rf /",
            "$(whoami)",
            "test | cat /etc/passwd",
        ]
        
        for dangerous_text in dangerous_texts:
            payload = {
                "tool_name": "text_analyzer",
                "parameters": {
                    "text": dangerous_text
                }
            }
            
            response = self.client.post(
                '/api/execute',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Should return validation error
            data = json.loads(response.data)
            self.assertIn('error', data)
    
    def test_execute_tool_integer_bounds(self):
        """Test integer bounds validation."""
        payload = {
            "tool_name": "fibonacci",
            "parameters": {
                "n": 100  # Over the max of 50
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Should either be caught by validation or by tool itself
        self.assertIn('error', data)
    
    def test_execute_tool_string_transform_valid(self):
        """Test string transform with valid input."""
        payload = {
            "tool_name": "string_transform",
            "parameters": {
                "text": "Hello World",
                "transformation": "uppercase"
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('result'), 'HELLO WORLD')
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        response = self.client.get('/api/tools')
        
        # Check for security headers
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        
        self.assertIn('X-XSS-Protection', response.headers)
        self.assertIn('Content-Security-Policy', response.headers)
    
    def test_rate_limiting(self):
        """Test that rate limiting works."""
        # Clear rate limit storage
        rate_limit_storage.clear()
        
        # Make many requests to trigger rate limit
        for i in range(51):
            response = self.client.post(
                '/api/execute',
                data=json.dumps({
                    "tool_name": "timestamp",
                    "parameters": {}
                }),
                content_type='application/json'
            )
            
            if i < 50:
                # First 50 should succeed
                self.assertIn(response.status_code, [200, 429])
            else:
                # 51st should be rate limited
                self.assertEqual(response.status_code, 429)
                data = json.loads(response.data)
                self.assertIn('Rate limit', data.get('error', ''))
                break
    
    def test_deep_nested_json(self):
        """Test that deeply nested JSON is rejected."""
        # Create deeply nested structure
        nested = {"level": 1}
        current = nested
        for i in range(15):
            current["nested"] = {"level": i + 2}
            current = current["nested"]
        
        payload = {
            "tool_name": "calculate",
            "parameters": nested
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_large_payload_rejected(self):
        """Test that large payloads are rejected."""
        # Create a large payload (slightly over 1MB limit)
        # Using 1.1MB instead of 2MB for efficiency
        large_text = "x" * int(1.1 * 1024 * 1024)
        
        payload = {
            "tool_name": "text_analyzer",
            "parameters": {
                "text": large_text
            }
        }
        
        response = self.client.post(
            '/api/execute',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should be rejected (either 413 or 400)
        self.assertIn(response.status_code, [400, 413])


if __name__ == '__main__':
    unittest.main(verbosity=2)

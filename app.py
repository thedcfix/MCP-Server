"""
Flask web application for MCP Server GUI.
"""

from flask import Flask, render_template, request, jsonify
from mcp_server import mcp_server
from security import (
    rate_limit, 
    validate_request_json, 
    add_security_headers,
    SecurityValidator,
    ValidationError
)
import json
import os

app = Flask(__name__)

# Security configuration
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max request size

# Add security headers to all responses
@app.after_request
def apply_security_headers(response):
    return add_security_headers(response)


@app.route('/')
def index():
    """Main page showing the MCP server GUI."""
    server_info = mcp_server.get_server_info()
    tools = mcp_server.list_tools()
    return render_template('index.html', server_info=server_info, tools=tools)


@app.route('/api/tools', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
def get_tools():
    """API endpoint to get all available tools."""
    tools = mcp_server.list_tools()
    return jsonify(tools)


@app.route('/api/execute', methods=['POST'])
@rate_limit(max_requests=50, window_seconds=60)
@validate_request_json()
def execute_tool():
    """API endpoint to execute a tool with comprehensive input validation."""
    try:
        data = request.get_json()
        
        if not data or 'tool_name' not in data:
            return jsonify({"error": "tool_name is required"}), 400
        
        tool_name = data['tool_name']
        parameters = data.get('parameters', {})
        
        # Validate that tool_name is a string
        if not isinstance(tool_name, str):
            return jsonify({"error": "tool_name must be a string"}), 400
        
        # Validate that parameters is a dictionary
        if not isinstance(parameters, dict):
            return jsonify({"error": "parameters must be an object"}), 400
        
        # Execute tool with validation
        result = mcp_server.execute_tool(tool_name, parameters)
        return jsonify(result)
        
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        # Log the error but don't expose internal details
        app.logger.error(f"Error executing tool: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/server-info', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
def get_server_info():
    """API endpoint to get server information."""
    info = mcp_server.get_server_info()
    return jsonify(info)


if __name__ == '__main__':
    # Disable debug mode in production for security
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)

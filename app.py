"""
Flask web application for MCP Server GUI.
"""

from flask import Flask, render_template, request, jsonify
from mcp_server import mcp_server
import json

app = Flask(__name__)


@app.route('/')
def index():
    """Main page showing the MCP server GUI."""
    server_info = mcp_server.get_server_info()
    tools = mcp_server.list_tools()
    return render_template('index.html', server_info=server_info, tools=tools)


@app.route('/api/tools', methods=['GET'])
def get_tools():
    """API endpoint to get all available tools."""
    tools = mcp_server.list_tools()
    return jsonify(tools)


@app.route('/api/execute', methods=['POST'])
def execute_tool():
    """API endpoint to execute a tool."""
    data = request.get_json()
    
    if not data or 'tool_name' not in data:
        return jsonify({"error": "tool_name is required"}), 400
    
    tool_name = data['tool_name']
    parameters = data.get('parameters', {})
    
    result = mcp_server.execute_tool(tool_name, parameters)
    return jsonify(result)


@app.route('/api/server-info', methods=['GET'])
def get_server_info():
    """API endpoint to get server information."""
    info = mcp_server.get_server_info()
    return jsonify(info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

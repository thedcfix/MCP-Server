# MCP-Server
Simple MCP (Model Context Protocol) server with a Flask-based web GUI

## Overview

This is a simple MCP server implementation that exposes various tools through a web-based GUI. The server includes several example tools that demonstrate different functionalities:

- **calculate**: Perform basic mathematical operations (add, subtract, multiply, divide)
- **text_analyzer**: Analyze text and provide statistics (word count, character count, etc.)
- **timestamp**: Get current timestamp in various formats
- **string_transform**: Transform strings (uppercase, lowercase, reverse, title case)
- **fibonacci**: Generate Fibonacci sequence
- **execute_command**: Execute shell commands with security protections (timeout, output limits, concurrent execution limits)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/thedcfix/MCP-Server.git
cd MCP-Server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. The GUI will display:
   - Server information and statistics
   - List of all available tools with their descriptions and parameters
   - A test section where you can execute tools with custom parameters

## API Endpoints

The server exposes the following REST API endpoints:

- `GET /` - Web GUI interface
- `GET /api/tools` - List all available tools
- `GET /api/server-info` - Get server information
- `POST /api/execute` - Execute a tool with parameters

### Example API Usage

```bash
# List all tools
curl http://localhost:5000/api/tools

# Execute the calculate tool
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "calculate", "parameters": {"operation": "add", "a": 10, "b": 5}}'

# Analyze text
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "text_analyzer", "parameters": {"text": "Hello world!"}}'
```

## Project Structure

```
MCP-Server/
├── app.py              # Flask web application
├── mcp_server.py       # MCP server implementation with tools
├── templates/
│   └── index.html      # Web GUI template
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Adding New Tools

To add a new tool to the MCP server:

1. Open `mcp_server.py`
2. Add a new method to handle the tool (e.g., `_my_tool`)
3. Register the tool in the `_register_tools()` method with its metadata
4. The tool will automatically appear in the web GUI

## Security Features

This MCP server implements multiple security measures to prevent resource exhaustion attacks (CWE-400):

### Command Execution Security
- **Timeout Enforcement**: All shell commands have configurable timeouts (default: 30s, max: 300s)
- **Output Size Limits**: Command output is limited to 1 MB to prevent memory exhaustion
- **Concurrent Execution Limits**: Maximum of 5 concurrent shell commands
- **Process Cleanup**: Automatic cleanup of timed-out or failed processes
- **Input Sanitization**: Commands cannot read from stdin to prevent hanging

### Resource Limits
- **Text Input Limits**: Text analysis limited to 100 KB to prevent processing large inputs
- **Output Truncation**: Large outputs are automatically truncated with warnings
- **Fibonacci Limit**: Fibonacci sequence generation limited to 50 numbers

### Best Practices
When using the `execute_command` tool:
1. Always set appropriate timeout values for your use case
2. Be aware that output exceeding 1 MB will be truncated
3. Long-running processes will be terminated when they exceed the timeout
4. Commands that require user input will fail (stdin is disabled)

### Security Configuration
The following limits are enforced:
- `MAX_COMMAND_TIMEOUT`: 300 seconds (5 minutes)
- `DEFAULT_COMMAND_TIMEOUT`: 30 seconds
- `MAX_OUTPUT_SIZE`: 1 MB
- `MAX_TEXT_SIZE`: 100 KB
- `MAX_CONCURRENT_COMMANDS`: 5

## License

MIT License

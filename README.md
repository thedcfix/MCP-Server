# MCP-Server
Simple MCP (Model Context Protocol) server with a Flask-based web GUI

## Overview

This is a simple MCP server implementation that exposes various tools through a web-based GUI. The server includes several example tools that demonstrate different functionalities:

- **calculate**: Perform basic mathematical operations (add, subtract, multiply, divide)
- **text_analyzer**: Analyze text and provide statistics (word count, character count, etc.)
- **timestamp**: Get current timestamp in various formats
- **string_transform**: Transform strings (uppercase, lowercase, reverse, title case)
- **fibonacci**: Generate Fibonacci sequence

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

## License

MIT License

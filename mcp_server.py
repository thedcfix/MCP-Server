"""
MCP (Model Context Protocol) Server implementation with example tools.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import math


class MCPServer:
    """A simple MCP server that manages and exposes tools."""
    
    def __init__(self):
        self.tools = self._register_tools()
        self.server_info = {
            "name": "Example MCP Server",
            "version": "1.0.0",
            "description": "A simple MCP server with example tools"
        }
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools with their metadata."""
        return {
            "calculate": {
                "name": "calculate",
                "description": "Perform basic mathematical calculations (add, subtract, multiply, divide)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The mathematical operation to perform"
                        },
                        "a": {
                            "type": "number",
                            "description": "First operand"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second operand"
                        }
                    },
                    "required": ["operation", "a", "b"]
                },
                "handler": self._calculate
            },
            "text_analyzer": {
                "name": "text_analyzer",
                "description": "Analyze text and provide statistics (word count, character count, sentence count)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze"
                        }
                    },
                    "required": ["text"]
                },
                "handler": self._analyze_text
            },
            "timestamp": {
                "name": "timestamp",
                "description": "Get current timestamp in various formats",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["iso", "unix", "readable"],
                            "description": "The format for the timestamp",
                            "default": "iso"
                        }
                    },
                    "required": []
                },
                "handler": self._get_timestamp
            },
            "string_transform": {
                "name": "string_transform",
                "description": "Transform strings (uppercase, lowercase, reverse, title case)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to transform"
                        },
                        "transformation": {
                            "type": "string",
                            "enum": ["uppercase", "lowercase", "reverse", "title"],
                            "description": "The type of transformation to apply"
                        }
                    },
                    "required": ["text", "transformation"]
                },
                "handler": self._transform_string
            },
            "fibonacci": {
                "name": "fibonacci",
                "description": "Calculate Fibonacci sequence up to n numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "n": {
                            "type": "integer",
                            "description": "Number of Fibonacci numbers to generate (max 50)",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["n"]
                },
                "handler": self._fibonacci
            }
        }
    
    def _calculate(self, operation: str, a: float, b: float) -> Dict[str, Any]:
        """Perform mathematical calculations."""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {"error": "Division by zero is not allowed"}
                result = a / b
            else:
                return {"error": f"Unknown operation: {operation}"}
            
            return {
                "success": True,
                "operation": operation,
                "operands": {"a": a, "b": b},
                "result": result
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text and return statistics."""
        try:
            words = text.split()
            sentences = text.count('.') + text.count('!') + text.count('?')
            
            return {
                "success": True,
                "statistics": {
                    "character_count": len(text),
                    "word_count": len(words),
                    "sentence_count": max(sentences, 1),
                    "avg_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_timestamp(self, format: str = "iso") -> Dict[str, Any]:
        """Get current timestamp in specified format."""
        try:
            now = datetime.now()
            
            if format == "iso":
                timestamp = now.isoformat()
            elif format == "unix":
                timestamp = int(now.timestamp())
            elif format == "readable":
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return {"error": f"Unknown format: {format}"}
            
            return {
                "success": True,
                "format": format,
                "timestamp": timestamp
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _transform_string(self, text: str, transformation: str) -> Dict[str, Any]:
        """Transform string based on specified transformation."""
        try:
            if transformation == "uppercase":
                result = text.upper()
            elif transformation == "lowercase":
                result = text.lower()
            elif transformation == "reverse":
                result = text[::-1]
            elif transformation == "title":
                result = text.title()
            else:
                return {"error": f"Unknown transformation: {transformation}"}
            
            return {
                "success": True,
                "original": text,
                "transformation": transformation,
                "result": result
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _fibonacci(self, n: int) -> Dict[str, Any]:
        """Generate Fibonacci sequence."""
        try:
            if n < 1 or n > 50:
                return {"error": "n must be between 1 and 50"}
            
            sequence = []
            a, b = 0, 1
            for _ in range(n):
                sequence.append(a)
                a, b = b, a + b
            
            return {
                "success": True,
                "n": n,
                "sequence": sequence
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Return a list of all available tools with their metadata."""
        tools_list = []
        for tool_id, tool_data in self.tools.items():
            tools_list.append({
                "name": tool_data["name"],
                "description": tool_data["description"],
                "parameters": tool_data["parameters"]
            })
        return tools_list
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        if tool_name not in self.tools:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": [t["name"] for t in self.list_tools()]
            }
        
        tool = self.tools[tool_name]
        handler = tool["handler"]
        
        try:
            result = handler(**parameters)
            return result
        except TypeError as e:
            return {
                "error": f"Invalid parameters: {str(e)}",
                "expected_parameters": tool["parameters"]
            }
        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Return server information."""
        return {
            **self.server_info,
            "tool_count": len(self.tools),
            "tools": [t["name"] for t in self.list_tools()]
        }


# Global MCP server instance
mcp_server = MCPServer()

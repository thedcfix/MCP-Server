"""
MCP (Model Context Protocol) Server implementation with example tools.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import math
from security import SecurityValidator, ValidationError


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
        except Exception:
            return {"error": "Calculation failed"}
    
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
        except Exception:
            return {"error": "Text analysis failed"}
    
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
        except Exception:
            return {"error": "Timestamp generation failed"}
    
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
        except Exception:
            return {"error": "String transformation failed"}
    
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
        except Exception:
            return {"error": "Fibonacci generation failed"}
    
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
    
    def _validate_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters against a schema with comprehensive security checks."""
        try:
            # Check required parameters
            required = schema.get("required", [])
            for req_param in required:
                if req_param not in parameters:
                    return {
                        "valid": False,
                        "error": f"Missing required parameter: {req_param}"
                    }
            
            # Check for unexpected parameters
            allowed_params = set(schema.get("properties", {}).keys())
            provided_params = set(parameters.keys())
            unexpected = provided_params - allowed_params
            if unexpected:
                return {
                    "valid": False,
                    "error": f"Unexpected parameters: {', '.join(unexpected)}"
                }
            
            # Validate and sanitize each parameter based on type
            properties = schema.get("properties", {})
            for param_name, param_value in parameters.items():
                if param_name not in properties:
                    continue
                
                param_schema = properties[param_name]
                param_type = param_schema.get("type")
                
                # Type-specific validation
                if param_type == "string":
                    # Check for enum constraint
                    if "enum" in param_schema:
                        SecurityValidator.validate_enum(param_value, param_schema["enum"])
                    else:
                        # Determine max length based on context
                        max_length = 10000 if param_name != "text" else 100000
                        parameters[param_name] = SecurityValidator.sanitize_string(
                            param_value, max_length
                        )
                
                elif param_type == "integer":
                    minimum = param_schema.get("minimum", -1000000)
                    maximum = param_schema.get("maximum", 1000000)
                    parameters[param_name] = SecurityValidator.validate_integer(
                        param_value, minimum, maximum
                    )
                
                elif param_type == "number":
                    parameters[param_name] = SecurityValidator.validate_number(param_value)
                
                else:
                    # For other types, ensure basic type checking
                    if param_type == "boolean" and not isinstance(param_value, bool):
                        return {
                            "valid": False,
                            "error": f"Parameter '{param_name}' must be boolean"
                        }
            
            return {"valid": True, "sanitized_parameters": parameters}
            
        except ValidationError as e:
            # ValidationError only contains safe validation messages, not stack traces
            # lgtm[py/stack-trace-exposure] - ValidationError contains only controlled messages
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters after validation and sanitization."""
        try:
            # Validate tool name
            tool_name = SecurityValidator.validate_tool_name(tool_name)
        except ValidationError as e:
            # ValidationError only contains safe validation messages, not stack traces
            # lgtm[py/stack-trace-exposure] - ValidationError contains only controlled messages
            return {
                "error": f"Invalid tool name: {str(e)}"
            }
        
        if tool_name not in self.tools:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": [t["name"] for t in self.list_tools()]
            }
        
        tool = self.tools[tool_name]
        handler = tool["handler"]
        tool_schema = tool["parameters"]
        
        # Validate parameters against schema
        validation_result = self._validate_parameters(parameters, tool_schema)
        if not validation_result["valid"]:
            return {
                "error": validation_result["error"],
                "expected_parameters": tool_schema
            }
        
        # Use sanitized parameters from validation
        sanitized_params = validation_result.get("sanitized_parameters", parameters)
        
        try:
            # Only pass validated parameters that are defined in the schema
            validated_params = {k: v for k, v in sanitized_params.items() 
                              if k in tool_schema.get("properties", {})}
            result = handler(**validated_params)
            return result
        except TypeError:
            # Don't expose TypeError details which could reveal internal structure
            return {
                "error": "Invalid parameter types or missing required parameters",
                "expected_parameters": tool_schema
            }
        except Exception:
            # Don't expose internal exception details
            return {"error": "Tool execution failed"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Return server information."""
        return {
            **self.server_info,
            "tool_count": len(self.tools),
            "tools": [t["name"] for t in self.list_tools()]
        }


# Global MCP server instance
mcp_server = MCPServer()

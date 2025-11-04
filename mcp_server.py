"""
MCP (Model Context Protocol) Server implementation with example tools.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import math
import subprocess
import threading
import time


# Security Configuration Constants
MAX_COMMAND_TIMEOUT = 300  # Maximum 5 minutes
DEFAULT_COMMAND_TIMEOUT = 30  # Default 30 seconds
MAX_OUTPUT_SIZE = 1024 * 1024  # 1 MB max output
MAX_TEXT_SIZE = 100 * 1024  # 100 KB max text input
MAX_CONCURRENT_COMMANDS = 5  # Max concurrent shell commands


class MCPServer:
    """A simple MCP server that manages and exposes tools."""
    
    def __init__(self):
        self.tools = self._register_tools()
        self.server_info = {
            "name": "Example MCP Server",
            "version": "1.0.0",
            "description": "A simple MCP server with example tools"
        }
        self._command_semaphore = threading.Semaphore(MAX_CONCURRENT_COMMANDS)
        self._active_processes = []
        self._process_lock = threading.Lock()
    
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
            },
            "execute_command": {
                "name": "execute_command",
                "description": "Execute a shell command with timeout and output limits (SECURITY: Commands are limited to prevent resource exhaustion)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": f"Timeout in seconds (default: {DEFAULT_COMMAND_TIMEOUT}, max: {MAX_COMMAND_TIMEOUT})",
                            "minimum": 1,
                            "maximum": MAX_COMMAND_TIMEOUT,
                            "default": DEFAULT_COMMAND_TIMEOUT
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "Working directory for command execution (optional)"
                        }
                    },
                    "required": ["command"]
                },
                "handler": self._execute_command
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
            # Security: Prevent resource exhaustion with large text inputs
            if len(text) > MAX_TEXT_SIZE:
                return {
                    "error": f"Text too large. Maximum size is {MAX_TEXT_SIZE} bytes ({MAX_TEXT_SIZE // 1024} KB)"
                }
            
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
    
    def _execute_command(self, command: str, timeout: int = DEFAULT_COMMAND_TIMEOUT, 
                        working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a shell command with security controls.
        
        Security features:
        - Enforced timeout to prevent infinite execution
        - Output size limit to prevent memory exhaustion
        - Concurrent execution limit to prevent resource exhaustion
        - Process cleanup to prevent zombie processes
        """
        # Validate timeout
        if timeout > MAX_COMMAND_TIMEOUT:
            timeout = MAX_COMMAND_TIMEOUT
        elif timeout < 1:
            timeout = DEFAULT_COMMAND_TIMEOUT
        
        # Basic input validation
        if not command or not command.strip():
            return {"error": "Command cannot be empty"}
        
        # Check concurrent execution limit
        if not self._command_semaphore.acquire(blocking=False):
            return {
                "error": f"Maximum concurrent command limit reached ({MAX_CONCURRENT_COMMANDS}). Please try again later."
            }
        
        process = None
        try:
            # Start the process
            start_time = time.time()
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                text=True,
                # Security: Prevent shell from hanging on input
                stdin=subprocess.DEVNULL
            )
            
            with self._process_lock:
                self._active_processes.append(process)
            
            try:
                stdout_data, stderr_data = process.communicate(timeout=timeout)
                
                # Check output size limits
                if len(stdout_data) > MAX_OUTPUT_SIZE:
                    stdout_data = stdout_data[:MAX_OUTPUT_SIZE] + f"\n... (output truncated at {MAX_OUTPUT_SIZE} bytes)"
                if len(stderr_data) > MAX_OUTPUT_SIZE:
                    stderr_data = stderr_data[:MAX_OUTPUT_SIZE] + f"\n... (output truncated at {MAX_OUTPUT_SIZE} bytes)"
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "command": command,
                    "exit_code": process.returncode,
                    "stdout": stdout_data,
                    "stderr": stderr_data,
                    "execution_time": round(execution_time, 2),
                    "timeout": timeout,
                    "truncated": len(stdout_data) > MAX_OUTPUT_SIZE or len(stderr_data) > MAX_OUTPUT_SIZE
                }
                
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                process.kill()
                try:
                    stdout_data, stderr_data = process.communicate(timeout=5)
                except:
                    stdout_data, stderr_data = "", ""
                
                return {
                    "success": False,
                    "error": f"Command execution timed out after {timeout} seconds",
                    "command": command,
                    "timeout": timeout,
                    "stdout": stdout_data[:MAX_OUTPUT_SIZE] if stdout_data else "",
                    "stderr": stderr_data[:MAX_OUTPUT_SIZE] if stderr_data else ""
                }
                
        except Exception as e:
            # Clean up process if it exists
            if process and process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except:
                    pass
            
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "command": command
            }
        finally:
            # Always release the semaphore and clean up
            with self._process_lock:
                if process in self._active_processes:
                    self._active_processes.remove(process)
            self._command_semaphore.release()
    
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
        """Validate parameters against a schema."""
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
        
        return {"valid": True}
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
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
        
        try:
            # Only pass validated parameters that are defined in the schema
            validated_params = {k: v for k, v in parameters.items() 
                              if k in tool_schema.get("properties", {})}
            result = handler(**validated_params)
            return result
        except TypeError as e:
            return {
                "error": f"Invalid parameters: {str(e)}",
                "expected_parameters": tool_schema
            }
        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Return server information."""
        return {
            **self.server_info,
            "tool_count": len(self.tools),
            "tools": [t["name"] for t in self.list_tools()],
            "security": {
                "max_command_timeout": MAX_COMMAND_TIMEOUT,
                "default_command_timeout": DEFAULT_COMMAND_TIMEOUT,
                "max_output_size": MAX_OUTPUT_SIZE,
                "max_text_size": MAX_TEXT_SIZE,
                "max_concurrent_commands": MAX_CONCURRENT_COMMANDS
            }
        }
    
    def cleanup(self):
        """Clean up all active processes."""
        with self._process_lock:
            processes_to_clean = self._active_processes.copy()
            self._active_processes.clear()
        
        for process in processes_to_clean:
            if process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except:
                    pass


# Global MCP server instance
mcp_server = MCPServer()

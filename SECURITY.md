# Security Documentation

## Overview

This document describes the security measures implemented in the MCP-Server to protect against common vulnerabilities including command injection, XSS, path traversal, and other attack vectors.

## Security Features

### 1. Input Validation and Sanitization

All user inputs are validated and sanitized before processing using the `SecurityValidator` class in `security.py`.

#### String Validation
- **Maximum length enforcement**: Strings are limited to prevent memory exhaustion
  - Regular strings: 10,000 characters
  - Text fields: 100,000 characters
- **Dangerous pattern detection**: Automatically blocks inputs containing:
  - Shell metacharacters: `;`, `|`, `&`, `` ` ``, `$`, `(`, `)`, `{`, `}`
  - Path traversal patterns: `../`, `..\`
  - XSS patterns: `<script>`, `javascript:`, HTML event handlers
  - Code injection patterns: `eval()`, `exec()`, `__import__`, `subprocess`
- **HTML escaping**: All strings are HTML-escaped to prevent XSS attacks

#### Numeric Validation
- **Integer bounds**: -1,000,000 to 1,000,000 (configurable per parameter)
- **Float bounds**: -1e10 to 1e10 (configurable)
- **Special value protection**: NaN and Infinity values are rejected
- **Type enforcement**: Prevents implicit boolean-to-number conversions

#### Enum Validation
- **Whitelist approach**: Only explicitly allowed values are accepted
- **Case-sensitive matching**: Prevents case-based bypasses

#### Tool Name Validation
- **Alphanumeric only**: Tool names must match pattern `^[a-zA-Z_][a-zA-Z0-9_]*$`
- **Length limit**: Maximum 100 characters
- **Prevents injection**: Blocks special characters that could be used in attacks

### 2. Rate Limiting

Rate limiting is implemented to prevent abuse and DoS attacks.

#### Configuration
- **Execute endpoint**: 50 requests per minute per IP
- **Read-only endpoints**: 100 requests per minute per IP
- **Tracking**: By client IP address
- **Response**: HTTP 429 (Too Many Requests) when limit exceeded

#### Usage
```python
@app.route('/api/endpoint')
@rate_limit(max_requests=50, window_seconds=60)
def endpoint():
    # endpoint code
```

### 3. Security Headers

All HTTP responses include security headers to protect against common web vulnerabilities.

#### Headers Applied
- **X-Content-Type-Options: nosniff** - Prevents MIME type sniffing
- **X-Frame-Options: DENY** - Prevents clickjacking attacks
- **X-XSS-Protection: 1; mode=block** - Enables browser XSS protection
- **Content-Security-Policy** - Restricts resource loading
- **Strict-Transport-Security** - Forces HTTPS connections

### 4. Request Validation

#### JSON Validation
- **Content-Type enforcement**: Requests must use `application/json`
- **Size limits**: Maximum 1MB per request
- **Depth limits**: Maximum 10 levels of nesting
- **Format validation**: Malformed JSON is rejected

#### Parameter Validation
- **Schema enforcement**: Parameters are validated against tool schemas
- **Required parameter checking**: Missing required parameters are rejected
- **Unexpected parameter detection**: Extra parameters are rejected
- **Type checking**: Parameters must match expected types

### 5. Production Security

#### Debug Mode
- **Disabled by default**: Debug mode is off unless explicitly enabled
- **Environment variable**: Set `FLASK_DEBUG=true` only in development
- **Production usage**: Never enable debug mode in production

#### Error Handling
- **Generic error messages**: Internal errors don't expose implementation details
- **Logging**: Errors are logged for monitoring without exposing to users
- **Validation errors**: Provide helpful feedback without security information

## Attack Prevention

### Command Injection Prevention

**Risk**: Attackers could execute arbitrary system commands

**Mitigations**:
- All inputs are scanned for shell metacharacters
- Tool names are restricted to alphanumeric characters
- Parameters are validated before being passed to handlers
- No direct system command execution in tool handlers

**Example Blocked Inputs**:
```python
"test; rm -rf /"  # Blocked: semicolon
"$(whoami)"       # Blocked: command substitution
"test | cat /etc/passwd"  # Blocked: pipe character
```

### Path Traversal Prevention

**Risk**: Attackers could access files outside intended directories

**Mitigations**:
- Path traversal patterns (`../`, `..\`) are blocked
- Tool names cannot contain path separators
- No file system operations based on user input

**Example Blocked Inputs**:
```python
"../../../etc/passwd"  # Blocked: path traversal
"..\\windows\\system32"  # Blocked: Windows path traversal
```

### Cross-Site Scripting (XSS) Prevention

**Risk**: Attackers could inject malicious scripts

**Mitigations**:
- HTML escaping of all string inputs
- Script tags and JavaScript URLs are blocked
- Event handler attributes are blocked
- Content Security Policy headers restrict script execution

**Example Blocked Inputs**:
```python
"<script>alert('xss')</script>"  # Blocked: script tag
"javascript:alert(1)"  # Blocked: javascript URL
"<img src=x onerror=alert(1)>"  # Blocked: event handler
```

### Code Injection Prevention

**Risk**: Attackers could execute arbitrary Python code

**Mitigations**:
- `eval()` and `exec()` patterns are blocked
- Import statements are blocked in inputs
- No dynamic code execution based on user input
- Type validation prevents code injection through type confusion

**Example Blocked Inputs**:
```python
"eval(malicious_code)"  # Blocked: eval pattern
"__import__('os').system('ls')"  # Blocked: import pattern
"exec('print(secrets)')"  # Blocked: exec pattern
```

### Denial of Service (DoS) Prevention

**Risk**: Attackers could overwhelm the server

**Mitigations**:
- Request size limits (1MB maximum)
- Rate limiting (50-100 requests per minute)
- Object depth limits (10 levels maximum)
- String length limits (10,000-100,000 characters)
- Numeric bounds checking

## Testing

### Unit Tests (`test_security.py`)
- 34 comprehensive test cases
- Tests all validation functions
- Tests boundary conditions
- Tests attack vector prevention

### Integration Tests (`test_integration.py`)
- 19 end-to-end test cases
- Tests API endpoints with security
- Tests malicious input handling
- Tests rate limiting
- Tests security headers

### Running Tests
```bash
# Run security unit tests
python3 test_security.py

# Run integration tests
python3 test_integration.py

# Run all tests
python3 test_security.py && python3 test_integration.py
```

## Configuration

### Environment Variables

- `FLASK_DEBUG`: Set to `true` to enable debug mode (development only)

### Security Constants (in `security.py`)

```python
MAX_STRING_LENGTH = 10000      # Maximum string length
MAX_TEXT_LENGTH = 100000       # Maximum text field length
MAX_INTEGER_VALUE = 1000000    # Maximum integer value
MIN_INTEGER_VALUE = -1000000   # Minimum integer value
MAX_FLOAT_VALUE = 1e10         # Maximum float value
MIN_FLOAT_VALUE = -1e10        # Minimum float value
MAX_ARRAY_LENGTH = 1000        # Maximum array length
MAX_OBJECT_DEPTH = 10          # Maximum object nesting depth
```

## Best Practices

### For Developers

1. **Always validate inputs**: Use `SecurityValidator` for all user inputs
2. **Use type hints**: Specify expected types in function signatures
3. **Follow least privilege**: Only request permissions actually needed
4. **Log security events**: Record suspicious activity for monitoring
5. **Keep dependencies updated**: Regularly update Flask and other packages
6. **Review code**: Conduct security reviews before merging changes

### For Deployers

1. **Never enable debug mode in production**
2. **Use HTTPS**: Always use TLS/SSL in production
3. **Monitor logs**: Watch for attack patterns and suspicious activity
4. **Update regularly**: Apply security patches promptly
5. **Use environment variables**: Store configuration in environment, not code
6. **Limit network access**: Use firewalls to restrict access
7. **Regular backups**: Maintain backups of data and configuration

### For Users

1. **Use strong authentication**: If adding authentication, use strong credentials
2. **Keep client software updated**: Update browsers and API clients
3. **Report vulnerabilities**: Responsibly disclose security issues
4. **Monitor usage**: Watch for unexpected activity

## Security Checklist

- [x] Input validation on all endpoints
- [x] Input sanitization before processing
- [x] Rate limiting implemented
- [x] Security headers added
- [x] Debug mode disabled in production
- [x] Request size limits enforced
- [x] Type validation implemented
- [x] Bounds checking for numeric values
- [x] Path traversal protection
- [x] Command injection protection
- [x] XSS protection
- [x] Code injection protection
- [x] DoS prevention measures
- [x] Comprehensive test coverage
- [x] Security documentation

## Vulnerability Reporting

If you discover a security vulnerability, please report it responsibly:

1. **Do not** create a public GitHub issue
2. Contact the maintainers privately
3. Provide detailed information about the vulnerability
4. Allow time for a fix before public disclosure

## References

- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [CWE-20: Improper Input Validation](https://cwe.mitre.org/data/definitions/20.html)
- [CWE-77: Command Injection](https://cwe.mitre.org/data/definitions/77.html)
- [CWE-79: Cross-site Scripting](https://cwe.mitre.org/data/definitions/79.html)
- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)

## License

This security implementation is part of the MCP-Server project and follows the same license terms.

# Claude Connectors

A collection of Model Context Protocol (MCP) connectors for Claude Desktop, providing various tools and integrations to extend Claude's capabilities.

## What is MCP?

Model Context Protocol (MCP) is an open standard that enables AI assistants like Claude to securely connect to various data sources and tools. MCP connectors act as bridges between Claude and external systems, allowing Claude to interact with files, databases, APIs, and more.

## Available Connectors

### Filesystem Connector
Located in `connectors/filesystem/`, this connector provides basic file system operations:
- **list_directory**: Lists files and subdirectories in a directory
- **read_files**: Reads up to 8KB from a file
- **search_files**: Recursively searches for files by name containing a keyword

## How to Add a New Connector

Follow these steps to create a new MCP connector:

### 1. Create Connector Directory
```bash
mkdir connectors/your-connector-name
cd connectors/your-connector-name
```

### 2. Create server.py
Create a `server.py` file with the following structure:

```python
#!/usr/bin/env python
import sys
from mcp.server.fastmcp import FastMCP

# Helper for Claude Desktop logs
def log(msg: str):
    print(f"[YourConnectorName] {msg}", file=sys.stderr)

# Initialize the MCP server
mcp = FastMCP("your-connector-name", version="1.0.0")

# Define your tools
@mcp.tool(name="your_tool_name", description="Description of what your tool does")
async def your_tool_function(param1: str, param2: int = 0) -> dict:
    log(f"your_tool_function({param1}, {param2})")
    # Your tool logic here
    return {"result": "success", "data": "your response"}

# Entrypoint
if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        log("Server shutting down.")
```

### 3. Install Dependencies
Make sure you have the required packages:
```bash
pip install mcp
```

### 4. Test Your Connector
Test your connector using the MCP development tools:
```bash
mcp dev connectors/your-connector-name/server.py
```

This will start the MCP Inspector where you can test your tools interactively.

### 5. Integration with Claude Desktop
To use your connector with Claude Desktop, add it to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "your-connector-name": {
      "command": "python",
      "args": ["/path/to/your/connectors/your-connector-name/server.py"]
    }
  }
}
```

### 6. Best Practices
- Use descriptive tool names and descriptions
- Include proper error handling in your tools
- Add logging for debugging purposes
- Follow the existing code style and patterns
- Test thoroughly using `mcp dev` before deploying

## Development

### Prerequisites
- Python 3.7+
- MCP Python SDK (`pip install mcp`)

### Testing
Use the MCP development tools to test connectors:
```bash
mcp dev path/to/your/server.py
```

## Contributing

1. Fork the repository
2. Create a new connector following the steps above
3. Test your connector thoroughly
4. Submit a pull request with a clear description

## License

This project is open source. Please check individual connector directories for specific licensing information.
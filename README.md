# VibeCodeMCP

A Model Context Protocol (MCP) server for managing and creating other MCP servers.

## Dependency Issues Fix

The original server.py has some dependency issues with incorrect imports and missing functionality. To fix these issues:

1. Run the fix_dependencies.py script:

```bash
python fix_dependencies.py
```

This script will:
- Fix incorrect imports in the tools directory
- Create necessary utility modules in the utils directory
- Replace absolute imports with relative imports
- Provide simplified implementations of missing functions

2. After running the fix script, you can either use the original server.py or the modified_server.py:

```bash
# Using the fixed original server
python server.py

# Or using the simplified modified server
python modified_server.py
```

The modified_server.py contains simplified implementations of file operations that don't rely on the complex dependency chain of the original implementation.

## Features

- Create MCP servers with `create_server` tool
- List existing servers with `list_servers` tool
- Remove servers with `remove_server` tool
- File operations:
  - Read files with `read_file` tool
  - Write files with `write_file` tool
  - Edit files with `edit_file` tool

## Usage

1. Start the server:
```bash
python modified_server.py
```

2. Connect to the server with an MCP client.

3. Use the available tools to manage your MCP servers.

## Dependencies

Required Python packages:
- mcp[cli]>=1.6.0
- anyio
- editorconfig
- tomli

These dependencies are specified in the pyproject.toml file.
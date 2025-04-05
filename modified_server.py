#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, List, Optional, Any, Union
import logging
import os
import json
import uuid
import shutil
from pathlib import Path

# Constants
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servers_db.json")
SERVERS_DIR = "/Users/meet/Documents/python/projects/mcp/vibecodemcp/mcp-servers/"
CLAUDE_CONFIG_FILE = "/Users/meet/Library/Application Support/Claude/claude_desktop_config.json"

# Ensure servers directory exists
os.makedirs(SERVERS_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Database handling functions
def load_database() -> Dict[str, Any]:
    """Load the database from file or create a new one if it doesn't exist"""
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding database file {DATABASE_FILE}, creating new database")
            return {"servers": {}}
    else:
        return {"servers": {}}

def save_database(data: Dict[str, Any]) -> None:
    """Save the database to file"""
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_claude_config() -> Dict[str, Any]:
    """Load Claude Desktop configuration file"""
    if os.path.exists(CLAUDE_CONFIG_FILE):
        try:
            with open(CLAUDE_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding Claude config file {CLAUDE_CONFIG_FILE}")
            return {"mcpServers": {}}
    else:
        logger.warning(f"Claude config file {CLAUDE_CONFIG_FILE} not found, creating new config")
        return {"mcpServers": {}}

def save_claude_config(config: Dict[str, Any]) -> None:
    """Save Claude Desktop configuration file"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(CLAUDE_CONFIG_FILE), exist_ok=True)

    with open(CLAUDE_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


# Create an MCP server
mcp = FastMCP("VibeCodeMCP")


# Add create-server tool
@mcp.tool()
def create_server(project_name: str, description: str) -> Dict[str, Any]:
    """
    Create a new MCP server with the specified configuration

    Args:
        project_name: Name of the project
        description: Description of the server

    Returns:
        Server information including server ID and location
    """
    # Generate a unique server ID
    server_id = str(uuid.uuid4())

    # Define server location
    server_location = os.path.join(SERVERS_DIR, project_name)

    # Create server directory
    os.makedirs(server_location, exist_ok=True)

    # Create basic server template file
    server_file = os.path.join(server_location, "server.py")
    with open(server_file, "w") as f:
        f.write(f'''#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context

# Create an MCP server
mcp = FastMCP("{project_name}")
if __name__ == "__main__":
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        print("Server stopped by user")
''')

    # Make the file executable
    os.chmod(server_file, 0o755)

    # Create server entry
    server_entry = {
        "id": server_id,
        "name": project_name,
        "description": description,
        "location": server_location,
        "tool_count": 0,
        "tools": {}
    }

    # Update database
    db = load_database()
    db["servers"][server_id] = server_entry
    save_database(db)

    # Update Claude config
    claude_config = load_claude_config()
    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}

    # Add server to Claude config
    server_name = project_name.lower().replace(" ", "_")
    claude_config["mcpServers"][server_name] = {
        "command": "/Users/meet/.local/bin/uv",
        "args": [
            "run",
            "--directory",
            server_location,
            "server.py"
        ]
    }

    # Save Claude config
    save_claude_config(claude_config)

    logger.info(f"Created server '{project_name}' with ID {server_id} at {server_location}")
    logger.info(f"Added server to Claude Desktop configuration as '{server_name}'")
    return server_entry

# Add list-servers tool
@mcp.tool()
def list_servers() -> Dict[str, Any]:
    """
    List all managed MCP servers

    Returns:
        Information about all managed servers
    """
    db = load_database()
    servers_info = []

    for server_id, server_data in db["servers"].items():
        servers_info.append({
            "id": server_id,
            "name": server_data["name"],
            "description": server_data["description"],
            "location": server_data["location"],
            "tool_count": server_data["tool_count"]
        })

    logger.info(f"Listed {len(servers_info)} servers")
    return {"servers": servers_info}


# Add remove-server tool
@mcp.tool()
def remove_server(server_name: str) -> Dict[str, Any]:
    """
    Remove an MCP server by name

    Args:
        server_name: Name of the server to remove

    Returns:
        Information about the removed server
    """
    db = load_database()

    # Find server by name
    server_id = None
    server_data = None

    for sid, data in db["servers"].items():
        if data["name"] == server_name:
            server_id = sid
            server_data = data
            break

    if not server_id:
        raise ValueError(f"No server found with name '{server_name}'")

    # Remove server directory
    server_location = server_data["location"]
    if os.path.exists(server_location):
        shutil.rmtree(server_location)

    # Remove from database
    removed_server = db["servers"].pop(server_id)
    save_database(db)

    # Remove from Claude config
    claude_config = load_claude_config()
    if "mcpServers" in claude_config:
        # Look for the server in Claude config by matching the location path
        for config_name, config in list(claude_config["mcpServers"].items()):
            # Check if this config entry points to our server
            if "args" in config and len(config["args"]) >= 3:
                config_location = config["args"][-2]  # The directory argument
                if config_location == server_location:
                    del claude_config["mcpServers"][config_name]
                    logger.info(f"Removed server from Claude Desktop configuration: {config_name}")
                    break

        # Save updated config
        save_claude_config(claude_config)

    logger.info(f"Removed server '{server_name}' with ID {server_id}")
    return {"removed": removed_server}

# Simplified read_file tool
@mcp.tool()
async def read_file(file_path: str, offset: int = None, limit: int = None) -> str:
    """
    Read the contents of a file with optional offset and limit.

    Args:
        file_path: The path to the file to read.
        offset: The starting position to read from (optional).
        limit: The maximum number of bytes to read (optional).

    Returns:
        The contents of the file as a string.
    """
    if file_path is None:
        raise ValueError("path is required")

    # Make sure file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    if os.path.isdir(file_path):
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    # Apply offset and limit
    if offset is not None:
        offset = max(0, offset - 1)  # Convert to 0-indexed
    else:
        offset = 0
    
    if limit is not None:
        lines = lines[offset:offset + limit]
    else:
        lines = lines[offset:offset + 1000]  # Default limit
    
    # Add line numbers
    numbered_lines = []
    for i, line in enumerate(lines):
        line_number = offset + i + 1  # 1-indexed line number
        numbered_lines.append(f"{line_number:6}\t{line.rstrip()}")
    
    return "\n".join(numbered_lines)

# Simplified write_file tool
@mcp.tool()
async def write_file(file_path: str, description: str = None, content: object = None) -> str:
    """
    Write content to a specified file path with an optional description.
    
    Args:
        file_path: The path to the file where the content will be written.
        description: A description of the file or its purpose.
        content: The content to be written to the file.
    
    Returns:
        A confirmation message.
    """
    if file_path is None:
        raise ValueError("path is required")
    
    if description is None:
        raise ValueError("description is required")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    # Convert content to string if needed
    if content is not None and not isinstance(content, str):
        import json
        content_str = json.dumps(content)
    else:
        content_str = content or ""
    
    # Write content to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_str)
    
    return f"Successfully wrote to {file_path}"

# Simplified edit_file tool
@mcp.tool()
async def edit_file(file_path: str, description: str = None, old_string: str = None, new_string: str = None) -> str:
    """
    Edit the contents of a file by replacing old_string with new_string.
    
    Args:
        file_path: The path to the file to edit.
        description: A description of the edit operation.
        old_string: The string to be replaced in the file.
        new_string: The string to replace the old string with.
    
    Returns:
        A confirmation message.
    """
    if file_path is None:
        raise ValueError("path is required")
    
    if description is None:
        raise ValueError("description is required")
    
    if old_string is None:
        raise ValueError("old_string is required")
    
    # Make sure file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Check if old_string exists in the file
    if old_string not in content:
        raise ValueError("String to replace not found in file.")
    
    # Check for uniqueness of old_string
    if content.count(old_string) > 1:
        raise ValueError("Multiple matches found. Please provide more context.")
    
    # Replace old_string with new_string
    new_content = content.replace(old_string, new_string or "", 1)
    
    # Write updated content back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Generate a snippet of the edit
    before_lines = content.split(old_string)[0].split("\n")
    replacement_line = len(before_lines)
    edited_lines = new_content.split("\n")
    
    # Calculate start and end line numbers for the snippet
    start_line = max(0, replacement_line - 4)
    end_line = min(len(edited_lines), replacement_line + 4 + len(new_string.split("\n") if new_string else []))
    
    # Extract the snippet lines
    snippet_lines = edited_lines[start_line:end_line]
    
    # Format with line numbers
    result = []
    for i, line in enumerate(snippet_lines):
        line_num = start_line + i + 1
        result.append(f"{line_num:4d} | {line}")
    
    snippet = "\n".join(result)
    
    return f"Successfully edited {file_path}\n\nHere's a snippet of the edited file:\n{snippet}"

# Add create-tool tool
@mcp.tool()
async def create_tool(server_name: str, tool_name: str, tool_description: str, parameters: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a new tool in an existing MCP server
    
    Args:
        server_name: Name of the server to add the tool to
        tool_name: Name of the tool to create (snake_case)
        tool_description: Description of what the tool does
        parameters: List of parameter definitions, each with 'name', 'type', and 'description' keys
            Example: [{"name": "message", "type": "str", "description": "The message to process"}]
    
    Returns:
        Information about the created tool
    """
    # Find the server by name
    db = load_database()
    server_id = None
    server_data = None
    
    for sid, data in db["servers"].items():
        if data["name"] == server_name:
            server_id = sid
            server_data = data
            break
    
    if not server_id:
        raise ValueError(f"No server found with name '{server_name}'")
    
    # Check if tool name follows Python naming conventions (snake_case)
    if not all(c.islower() or c.isdigit() or c == '_' for c in tool_name):
        raise ValueError("Tool name must be in snake_case (lowercase with underscores)")
    
    # Initialize parameters list if not provided
    if parameters is None:
        parameters = []
    
    # Validate parameters format
    for param in parameters:
        if not all(key in param for key in ["name", "type", "description"]):
            raise ValueError("Each parameter must have 'name', 'type', and 'description' keys")
    
    # Read the server.py file
    server_file_path = os.path.join(server_data["location"], "server.py")
    if not os.path.exists(server_file_path):
        raise FileNotFoundError(f"Server file not found at {server_file_path}")
    
    with open(server_file_path, 'r', encoding='utf-8') as f:
        server_code = f.read()
    
    # Determine insertion point
    # Look for if __name__ == "__main__": to find where to insert the tool
    insertion_point = server_code.find('if __name__ == "__main__":')
    if insertion_point == -1:
        # Fallback: insert at the end
        insertion_point = len(server_code)
    
    # Generate parameter string
    param_strings = []
    typed_params = []
    
    for param in parameters:
        param_name = param["name"]
        param_type = param["type"]
        typed_params.append(f"{param_name}: {param_type}")
        param_strings.append(f"        {param_name}: {param['description']}")
    
    # Create the tool code with proper indentation
    tool_code = f"""
# {tool_name} tool
@mcp.tool()
def {tool_name}({', '.join(typed_params)}) -> Dict[str, Any]:
    \"\"\"
    {tool_description}
    
    Args:
{os.linesep.join(param_strings) if param_strings else '        None'}
    
    Returns:
        A dictionary containing the result
    \"\"\"
    # TODO: Implement the tool functionality
    result = {{
        "status": "success",
        "message": "Tool executed successfully"
    }}
    return result

"""

    # Insert the tool code
    new_server_code = server_code[:insertion_point] + tool_code + server_code[insertion_point:]
    
    # Write back the updated server code
    with open(server_file_path, 'w', encoding='utf-8') as f:
        f.write(new_server_code)
    
    # Update the database
    tool_entry = {
        "name": tool_name,
        "description": tool_description,
        "parameters": parameters
    }
    
    if "tools" not in server_data:
        server_data["tools"] = {}
    
    server_data["tools"][tool_name] = tool_entry
    server_data["tool_count"] = len(server_data["tools"])
    
    # Save the updated database
    db["servers"][server_id] = server_data
    save_database(db)
    
    logger.info(f"Created tool '{tool_name}' in server '{server_name}'")
    
    return {
        "server_name": server_name,
        "tool_name": tool_name,
        "description": tool_description,
        "parameters": parameters,
        "file_path": server_file_path
    }

# Add a sample prompt
@mcp.prompt()
def help_prompt() -> str:
    """Provide help information about this MCP server"""
    return """
    This is VibeCodeMCP, a Model Context Protocol server.

    Available resources:
    - greeting://{name} - Get a personalized greeting

    Available tools:
    - create_server - Create a new MCP server
    - list_servers - List all managed MCP servers
    - remove_server - Remove a server by name
    - create_tool - Add a new tool to an existing server
    - read_file - Read the contents of any file by path
    - write_file - Write content to a file
    - edit_file - Edit the contents of a file

    How can I assist you today?
    """


if __name__ == "__main__":
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context, Image
from typing import Dict, List, Optional, Any, Union
import logging
import os
import json
import uuid
import shutil
from pathlib import Path
from tools.read_file import read_file_content
from tools.write_file import write_file_content
from tools.edit_file import edit_file_content


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



# Type definitions for tool parameters
class ParameterDefinition:
    name: str
    type: str
    description: str
    required: bool


class ToolDefinition:
    name: str
    description: str
    parameters: List[ParameterDefinition]
    code: str


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


# add here a tool to create a tool for the server
# parameters : tool name, tool description, tool functionality, tool 





# Add read-file tool
@mcp.tool()
async def read_file(file_path: str, offset: int | None = None,
    limit: int | None = None) -> str:
    """
    Do not use this tool directly. Only call this tool from other tools.
    Read the contents of a file with optional offset and limit.
    
    Args:
        file_path: The path to the file to read.
        offset: The starting position to read from (optional).
        limit: The maximum number of bytes to read (optional).
    
    Returns:
        The contents of the file as a string.
    
    Raises:
        ValueError: If the file_path is not provided.
    """
    if file_path is None:
        raise ValueError("path is required for ReadFile subtool")

    return await read_file_content(file_path, offset, limit)

@mcp.tool()

async def write_file(file_path: str,
                    description: str | None = None,
                    content: object = None,  # Allow any type, will be serialized to string if needed
                        ) -> str:
    """
    Do not use this tool directly. Only call this tool from other tools.
    Writes content to a specified file path with an optional description.
    Args:
        file_path (str): The path to the file where the content will be written. 
                        This parameter is required.
        description (str | None): A description of the file or its purpose. 
                                This parameter is required.
        content (object): The content to be written to the file. If the content 
                        is not a string, it will be serialized to a string 
                        using `json.dumps`. Defaults to None.

    Returns:
        str: A confirmation or result string from the `write_file_content` function.

    Raises:
        ValueError: If `file_path` is None or `description` is None.

    Notes:
        - If `content` is None, an empty string will be written to the file.
        - The actual file writing is delegated to the `write_file_content` function.
    """
    if file_path is None:
        raise ValueError("path is required for WriteFile subtool")
    if description is None:
        raise ValueError("description is required for WriteFile subtool")
    import json
    # If content is not a string, serialize it to a string using json.dumps
    if content is not None and not isinstance(content, str):
        content_str = json.dumps(content)
    else:
        content_str = content or ""

    return await write_file_content(file_path, content_str, description)


@mcp.tool()

async def edit_file(file_path: str,
                    description: str | None = None,
                    old_string: str | None = None,
                    new_string: str | None = None,
                    content: object = None,  # Allow any type, will be serialized to string if needed
                        ) -> str:
    """
    Do not use this tool directly. Only call this tool from other tools.
    Edit the contents of a file.
    This function allows editing the contents of a file by replacing an old string 
    with a new string. It also supports adding a description for the edit operation.
        file_path (str): 
            The path to the file or directory to operate on. This is a required parameter.
        description (str | None): 
            A description of the edit operation. This is a required parameter.
        old_string (str | None): 
            The string to be replaced in the file. If not provided, an exception is raised.
            Use an empty string for creating a new file.
        new_string (str | None): 
            The string to replace the old string with. Defaults to an empty string if not provided.
        content (object): 
            The content to be serialized to a string if needed. This parameter is optional.
        str: 
            The file contents and metadata after the edit operation.
    Raises:
        ValueError: 
            If `file_path` is not provided.
        ValueError: 
            If `description` is not provided.
        ValueError: 
            If `old_string` is not provided.
    Notes:
        - Telemetry should be added to track cases where `old_string` is not provided.
        - The function prefers `old_string` over `old_str` and `new_string` over `new_str` 
        if both are provided.
    """
    if file_path is None:
        raise ValueError("path is required for EditFile subtool")
    if description is None:
        raise ValueError("description is required for EditFile subtool")
    if old_string is None:
        # TODO: I want telemetry to tell me when this occurs.
        raise ValueError(
            "Either old_string or old_str is required for EditFile subtool (use empty string for new file creation)"
        )
    # Accept either old_string or old_str (prefer old_string if both are provided)
    old_content = old_string or ""
    # Accept either new_string or new_str (prefer new_string if both are provided)
    new_content = new_string or ""

    return await edit_file_content(
        file_path, old_content, new_content, None, description
    )

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
    - read_file - Read the contents of any file by path
    - echo - Echo a message back
    - process_data - Process data with progress reporting
    
    How can I assist you today?
    """


if __name__ == "__main__":
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

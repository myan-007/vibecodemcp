#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context, Image
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


# Add read-file tool
@mcp.tool()
def read_file(file_path: str) -> Dict[str, Any]:
    """
    Read the contents of a file
    
    Args:
        file_path: Path to the file to read
    
    Returns:
        The file contents and metadata
    """
    # Validate path
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Not a file: {file_path}")
    
    try:
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Get file metadata
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        file_modified = file_stat.st_mtime
        
        # Get file extension
        _, file_extension = os.path.splitext(file_path)
        
        logger.info(f"Read file: {file_path} ({file_size} bytes)")
        return {
            "path": file_path,
            "content": content,
            "size": file_size,
            "modified": file_modified,
            "extension": file_extension,
            "is_binary": False
        }
    except UnicodeDecodeError:
        # Handle binary files
        logger.info(f"Binary file detected: {file_path}")
        with open(file_path, 'rb') as f:
            binary_content = f.read()
        
        file_stat = os.stat(file_path)
        return {
            "path": file_path,
            "content": "<binary data>",
            "size": file_stat.st_size,
            "modified": file_stat.st_mtime,
            "extension": os.path.splitext(file_path)[1],
            "is_binary": True
        }
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise ValueError(f"Error reading file: {str(e)}")



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

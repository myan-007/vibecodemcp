#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context, Image
from typing import Dict, List, Optional, Any, Union
import logging
import os
import json
import uuid
import shutil
import re
import subprocess
import sys
from importlib.util import find_spec
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



def extract_imports(code: str) -> list[str]:
    """
    Extract import statements from Python code
    
    Args:
        code: Python code to analyze
        
    Returns:
        List of import statements
    """
    import_pattern = re.compile(r'^(?:import\s+\w+(?:\s*,\s*\w+)*|from\s+[\w.]+\s+import\s+(?:\w+(?:\s*,\s*\w+)*|\*))(?:\s+as\s+\w+)?', re.MULTILINE)
    return import_pattern.findall(code)

def install_packages(packages: list[str]) -> None:
    """
    Install packages using pip
    
    Args:
        packages: List of package names to install
    """
    if not packages:
        return
    
    for package in packages:
        # Check if package is already installed
        if find_spec(package) is not None:
            logger.info(f"Package '{package}' is already installed")
            continue
            
        logger.info(f"Installing package: {package}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install package '{package}': {e}")

def extract_packages_from_imports(imports: list[str]) -> list[str]:
    """
    Extract package names from import statements
    
    Args:
        imports: List of import statements
        
    Returns:
        List of package names that might need to be installed
    """
    packages = []
    
    for import_stmt in imports:
        if import_stmt.startswith('from '):
            # Extract the package name from a 'from' import
            match = re.match(r'from\s+([\w.]+)', import_stmt)
            if match:
                # Get the top-level package name (before the first dot)
                package = match.group(1).split('.')[0]
                if package not in ['mcp', '__future__', 'typing', 'os', 'sys', 
                                  'json', 'uuid', 'shutil', 're', 'subprocess',
                                  'importlib', 'pathlib', 'collections', 'functools',
                                  'datetime', 'random', 'math', 'time', 'contextlib',
                                  'io', 'tempfile', 'unittest']:
                    packages.append(package)
        else:
            # Extract the package name from a direct import
            match = re.match(r'import\s+([\w.]+)', import_stmt)
            if match:
                # Get the top-level package name (before the first dot)
                package = match.group(1).split('.')[0]
                if package not in ['mcp', '__future__', 'typing', 'os', 'sys', 
                                  'json', 'uuid', 'shutil', 're', 'subprocess',
                                  'importlib', 'pathlib', 'collections', 'functools',
                                  'datetime', 'random', 'math', 'time', 'contextlib',
                                  'io', 'tempfile', 'unittest']:
                    packages.append(package)
    
    return list(set(packages))  # Remove duplicates


def organize_imports_and_code(server_code: str, tool_code: str) -> str:
    """
    Organizes imports and code by moving all imports to the top
    
    Args:
        server_code: Existing server code
        tool_code: New tool code to add
        
    Returns:
        Reorganized code with imports at the top
    """
    # Extract imports from both server code and tool code
    server_imports = extract_imports(server_code)
    tool_imports = extract_imports(tool_code)
    
    # Combine imports and remove duplicates
    all_imports = list(set(server_imports + tool_imports))
    
    # Remove import statements from the server code
    for imp in server_imports:
        server_code = server_code.replace(imp + '\n', '')
        server_code = server_code.replace(imp, '')
    
    # Check for shebang line
    has_shebang = server_code.startswith('#!/')
    shebang_line = ''
    
    if has_shebang:
        # Extract the shebang line
        shebang_end = server_code.find('\n')
        shebang_line = server_code[:shebang_end+1]
        server_code = server_code[shebang_end+1:]
    
    # Construct the new code with imports at the top
    if has_shebang:
        new_code = shebang_line
    else:
        new_code = ""
        
    for imp in sorted(all_imports):
        new_code += imp + '\n'
    
    # Add a blank line after imports if not already present
    if not new_code.endswith('\n\n'):
        new_code += '\n'
        
    # Add the server code (without its imports)
    new_code += server_code.lstrip()
    
    # Look for the main block to insert the tool code before it
    if "__name__ == \"__main__\"" in new_code:
        # Insert tool code before the main block
        main_pos = new_code.find('if __name__ == "__main__":') 
        # Remove any imports from the tool code
        for imp in tool_imports:
            tool_code = tool_code.replace(imp + '\n', '')
            tool_code = tool_code.replace(imp, '')
        
        new_code = new_code[:main_pos] + tool_code.strip() + '\n\n' + new_code[main_pos:]
    else:
        # Append to the end
        # Remove any imports from the tool code
        for imp in tool_imports:
            tool_code = tool_code.replace(imp + '\n', '')
            tool_code = tool_code.replace(imp, '')
            
        new_code += '\n' + tool_code.strip()
    
    return new_code

def find_server_by_name(server_name: str) -> Dict[str, Any]:
    """
    Helper function to find a server by name in our database
    
    Args:
        server_name: Name of the server to find
        
    Returns:
        Server data and ID
        
    Raises:
        ValueError: If server not found
    """
    db = load_database()
    
    for server_id, server_data in db["servers"].items():
        if server_data["name"] == server_name:
            return {"id": server_id, "data": server_data}
    
    raise ValueError(f"No server found with name '{server_name}'")


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


# Add tool-to-server tool
@mcp.tool()
def add_tool_to_server(server_name: str, tool_name: str, tool_description: str, tool_code: str, params: str, server_code: str = None) -> Dict[str, Any]:
    """
    Add a tool to an existing MCP server
    Only invoke this tool when specified server name. 
    
    Args:
        server_name: Name of the server to add the tool to
        tool_name: Name of the tool to add
        tool_description: Description of the tool's functionality
        tool_code: Function implementation code (should be valid Python)
        params: Parameters for the tool in format "param1:type1, param2:type2, ..."
        server_code: Optional complete server code to use (if not provided, existing code will be read)
    
    Returns:
        Information about the added tool
    """
    # 1. Find the server by name
    server_info = find_server_by_name(server_name)
    server_id = server_info["id"]
    server_data = server_info["data"]
    server_location = server_data["location"]
    
    # 2. Get the server code (either from parameter or by reading the file)
    server_file_path = os.path.join(server_location, "server.py")
    
    if server_code is None:
        # Read existing server code
        if not os.path.exists(server_file_path):
            raise ValueError(f"Server file not found: {server_file_path}")
        
        with open(server_file_path, 'r') as f:
            server_code = f.read()
    else:
        # Use the provided code directly
        logger.info(f"Using provided server code for server '{server_name}'")
    
    # 3. Parse and validate parameters
    parameters = []
    if params:
        for param in params.split(','):
            param = param.strip()
            if ':' not in param:
                raise ValueError(f"Parameter format must be 'name:type', got: {param}")
            
            param_name, param_type = param.split(':', 1)
            param_name = param_name.strip()
            param_type = param_type.strip()
            
            # Validate param_type (simple check)
            valid_types = ['str', 'int', 'float', 'bool', 'dict', 'list', 'Dict', 'List', 'Any']
            if param_type not in valid_types and not param_type.startswith('List[') and not param_type.startswith('Dict['):
                logger.warning(f"Parameter type '{param_type}' might not be valid Python")
            
            parameters.append({
                "name": param_name,
                "type": param_type
            })
    
    # 4. Format tool function signature
    params_str = ", ".join([f"{p['name']}: {p['type']}" for p in parameters])
    
    # Prepare the tool code to add
    tool_code_template = f"""
# Tool: {tool_name}
@mcp.tool()
def {tool_name}({params_str}) -> str:
    \"\"\"
    {tool_description}
    \"\"\"
    {tool_code}
"""
    
    # 5. Organize imports and code
    # Extract imports from the tool code to check for packages to install
    tool_imports = extract_imports(tool_code_template)
    packages_to_install = extract_packages_from_imports(tool_imports)
    
    # Install any required packages
    if packages_to_install:
        logger.info(f"Installing required packages: {packages_to_install}")
        install_packages(packages_to_install)
    
    # Organize the code with all imports at the top
    modified_code = organize_imports_and_code(server_code, tool_code_template)
    
    # 6. Write back the modified server code
    with open(server_file_path, 'w') as f:
        f.write(modified_code)
    
    # 7. Update the server data in our database
    db = load_database()
    
    # Add the tool to the server's list of tools
    tool_id = str(uuid.uuid4())
    if "tools" not in db["servers"][server_id]:
        db["servers"][server_id]["tools"] = {}
    
    db["servers"][server_id]["tools"][tool_id] = {
        "id": tool_id,
        "name": tool_name,
        "description": tool_description,
        "parameters": parameters
    }
    
    # Update tool count
    db["servers"][server_id]["tool_count"] = len(db["servers"][server_id]["tools"])
    
    # Save the database
    save_database(db)
    
    logger.info(f"Added tool '{tool_name}' to server '{server_name}'")
    return {
        "server": server_name,
        "tool": {
            "id": tool_id,
            "name": tool_name,
            "description": tool_description,
            "parameters": parameters
        }
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
    - add_tool_to_server - Add a tool to an existing server
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

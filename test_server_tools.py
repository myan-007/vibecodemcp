#!/usr/bin/env python3
import unittest
import os
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the server module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from server import (
    create_server, 
    list_servers, 
    remove_server,
    read_file,
    add_tool_to_server,
    find_server_by_name,
    DATABASE_FILE, 
    SERVERS_DIR, 
    load_database,
    save_database
)


class TestServerTools(unittest.TestCase):
    """Test cases for server management tools."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create test directories
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create an isolated test directory for servers
        self.test_servers_dir = os.path.join(self.test_data_dir, "test_servers")
        os.makedirs(self.test_servers_dir, exist_ok=True)
        
        # Create a test database file
        self.test_db_file = os.path.join(self.test_data_dir, "test_servers_db.json")
        with open(self.test_db_file, 'w') as f:
            json.dump({"servers": {}}, f)
        
        # Create patches for constants
        self.db_patcher = patch('server.DATABASE_FILE', self.test_db_file)
        self.servers_dir_patcher = patch('server.SERVERS_DIR', self.test_servers_dir)
        
        # Start the patches
        self.mock_db_file = self.db_patcher.start()
        self.mock_servers_dir = self.servers_dir_patcher.start()

    def tearDown(self):
        """Clean up test environment after each test."""
        # Stop the patches
        self.db_patcher.stop()
        self.servers_dir_patcher.stop()
        
        # Clean up test directories
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)

    @patch('uuid.uuid4')
    def test_create_server(self, mock_uuid):
        """Test server creation functionality."""
        # Set a fixed UUID for testing
        mock_uuid.return_value = "12345678-1234-5678-1234-567812345678"
        
        # Create a test server
        result = create_server("Test Server", "A test server for unit testing")
        
        # Check the result
        self.assertEqual(result["id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(result["name"], "Test Server")
        self.assertEqual(result["description"], "A test server for unit testing")
        self.assertEqual(result["tool_count"], 0)
        self.assertEqual(result["tools"], {})
        
        # Check that the server directory was created
        server_dir = os.path.join(self.test_servers_dir, "12345678-1234-5678-1234-567812345678")
        self.assertTrue(os.path.exists(server_dir))
        
        # Check that the server.py file was created
        server_file = os.path.join(server_dir, "server.py")
        self.assertTrue(os.path.exists(server_file))
        self.assertTrue(os.access(server_file, os.X_OK))
        
        # Check the database was updated
        with open(self.test_db_file, 'r') as f:
            db = json.load(f)
            self.assertIn("12345678-1234-5678-1234-567812345678", db["servers"])

    def test_list_servers_empty(self):
        """Test listing servers when none exist."""
        result = list_servers()
        self.assertEqual(result, {"servers": []})

    def test_list_servers(self):
        """Test listing servers when some exist."""
        # Create test servers
        server1 = create_server("Server One", "First test server")
        server2 = create_server("Server Two", "Second test server")
        
        # List the servers
        result = list_servers()
        
        # Check the result
        servers_list = result["servers"]
        self.assertEqual(len(servers_list), 2)
        
        # Check server details are correct (ignoring order)
        server_names = [s["name"] for s in servers_list]
        self.assertIn("Server One", server_names)
        self.assertIn("Server Two", server_names)
        
        # Get server details
        server1_info = next(s for s in servers_list if s["name"] == "Server One")
        server2_info = next(s for s in servers_list if s["name"] == "Server Two")
        
        # Verify server details
        self.assertEqual(server1_info["id"], server1["id"])
        self.assertEqual(server1_info["description"], "First test server")
        self.assertEqual(server2_info["id"], server2["id"])
        self.assertEqual(server2_info["description"], "Second test server")

    def test_remove_server(self):
        """Test removing a server."""
        # Create test server
        server = create_server("Remove Test", "Server to be removed")
        server_id = server["id"]
        server_location = server["location"]
        
        # Verify server exists
        self.assertTrue(os.path.exists(server_location))
        db = load_database()
        self.assertIn(server_id, db["servers"])
        
        # Remove the server
        result = remove_server("Remove Test")
        
        # Check the result
        self.assertEqual(result["removed"]["id"], server_id)
        self.assertEqual(result["removed"]["name"], "Remove Test")
        
        # Verify server directory is gone
        self.assertFalse(os.path.exists(server_location))
        
        # Verify server is removed from database
        db = load_database()
        self.assertNotIn(server_id, db["servers"])

    def test_remove_nonexistent_server(self):
        """Test removing a server that doesn't exist."""
        with self.assertRaises(ValueError) as context:
            remove_server("Nonexistent Server")
        
        self.assertIn("No server found with name", str(context.exception))

    def test_full_workflow(self):
        """Test a complete workflow of creating, listing, and removing servers."""
        # Start with empty list
        initial_list = list_servers()
        self.assertEqual(len(initial_list["servers"]), 0)
        
        # Create servers
        server1 = create_server("Workflow Test 1", "First workflow server")
        server2 = create_server("Workflow Test 2", "Second workflow server")
        
        # List servers
        mid_list = list_servers()
        self.assertEqual(len(mid_list["servers"]), 2)
        
        # Remove first server
        remove_server("Workflow Test 1")
        
        # List again
        final_list = list_servers()
        self.assertEqual(len(final_list["servers"]), 1)
        self.assertEqual(final_list["servers"][0]["name"], "Workflow Test 2")
        
        # Clean up
        remove_server("Workflow Test 2")
        empty_list = list_servers()
        self.assertEqual(len(empty_list["servers"]), 0)
        
    def test_read_file_text(self):
        """Test reading a text file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp:
            temp.write("This is a test file.\nIt has multiple lines.\n123456")
            temp_path = temp.name
        
        try:
            # Read the file
            result = read_file(temp_path)
            
            # Check the result
            self.assertEqual(result["path"], temp_path)
            self.assertEqual(result["content"], "This is a test file.\nIt has multiple lines.\n123456")
            self.assertEqual(result["extension"], ".txt")
            self.assertFalse(result["is_binary"])
            self.assertIn("size", result)
            self.assertIn("modified", result)
        finally:
            # Clean up
            os.unlink(temp_path)
            
    def test_read_file_nonexistent(self):
        """Test reading a file that doesn't exist."""
        with self.assertRaises(ValueError) as context:
            read_file("/path/to/nonexistent/file.txt")
        
        self.assertIn("File not found", str(context.exception))
        
    def test_read_file_directory(self):
        """Test reading a directory as a file."""
        with self.assertRaises(ValueError) as context:
            read_file(self.test_data_dir)
        
        self.assertIn("Not a file", str(context.exception))
        
    def test_add_tool_to_server(self):
        """Test adding a tool to a server."""
        # Create a test server
        server = create_server("Tool Test Server", "Server for testing tool addition")
        server_id = server["id"]
        server_location = server["location"]
        
        # Tool parameters
        tool_name = "hello_world"
        tool_description = "A simple hello world tool"
        tool_code = "return f\"Hello, {name}!\""
        params = "name:str"
        
        # Add the tool
        result = add_tool_to_server("Tool Test Server", tool_name, tool_description, tool_code, params)
        
        # Check the result
        self.assertEqual(result["server"], "Tool Test Server")
        self.assertEqual(result["tool"]["name"], "hello_world")
        self.assertEqual(result["tool"]["description"], "A simple hello world tool")
        self.assertEqual(len(result["tool"]["parameters"]), 1)
        self.assertEqual(result["tool"]["parameters"][0]["name"], "name")
        self.assertEqual(result["tool"]["parameters"][0]["type"], "str")
        
        # Check that the server.py file was modified
        server_file = os.path.join(server_location, "server.py")
        with open(server_file, 'r') as f:
            content = f.read()
            self.assertIn("@mcp.tool()", content)
            self.assertIn("def hello_world(name: str)", content)
            self.assertIn("A simple hello world tool", content)
            self.assertIn("return f\"Hello, {name}!\"", content)
        
        # Check that the tool was added to the database
        db = load_database()
        self.assertIn(server_id, db["servers"])
        self.assertIn("tools", db["servers"][server_id])
        self.assertEqual(db["servers"][server_id]["tool_count"], 1)
        
        # Get the tool from the database
        tool_id = None
        for tid, tool_data in db["servers"][server_id]["tools"].items():
            if tool_data["name"] == "hello_world":
                tool_id = tid
                break
        
        self.assertIsNotNone(tool_id, "Tool not found in database")
        tool_data = db["servers"][server_id]["tools"][tool_id]
        self.assertEqual(tool_data["name"], "hello_world")
        self.assertEqual(tool_data["description"], "A simple hello world tool")
        
        # Clean up
        remove_server("Tool Test Server")
        
    def test_add_tool_to_server_with_code(self):
        """Test adding a tool to a server with provided server code."""
        # Create a test server
        server = create_server("Code Test Server", "Server for testing tool addition with code")
        server_id = server["id"]
        server_location = server["location"]
        
        # Create custom server code
        custom_server_code = """#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context

# Create an MCP server
mcp = FastMCP("Code Test Server")

# This is a custom server file
# with special formatting

if __name__ == "__main__":
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        print("Server stopped by user")
"""
        
        # Tool parameters
        tool_name = "custom_hello"
        tool_description = "A custom hello world tool"
        tool_code = "return f\"Custom hello, {name}!\""
        params = "name:str"
        
        # Add the tool with custom code
        result = add_tool_to_server(
            "Code Test Server", 
            tool_name, 
            tool_description, 
            tool_code, 
            params,
            custom_server_code
        )
        
        # Check the result
        self.assertEqual(result["server"], "Code Test Server")
        self.assertEqual(result["tool"]["name"], "custom_hello")
        
        # Check that the server file was completely rewritten
        server_file = os.path.join(server_location, "server.py")
        with open(server_file, 'r') as f:
            content = f.read()
            self.assertIn("# This is a custom server file", content)
            self.assertIn("def custom_hello(name: str)", content)
            self.assertIn("Custom hello, {name}", content)
        
        # Check that the database was updated
        db = load_database()
        self.assertEqual(db["servers"][server_id]["tool_count"], 1)
        
        # Clean up
        remove_server("Code Test Server")



if __name__ == "__main__":
    unittest.main()

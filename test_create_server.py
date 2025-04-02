#!/usr/bin/env python3
import unittest
import os
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the server module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from server import create_server, DATABASE_FILE, SERVERS_DIR, load_database


class TestCreateServer(unittest.TestCase):
    """Test cases for the create_server function."""

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
    def test_create_server_basic(self, mock_uuid):
        """Test basic server creation functionality."""
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
        
        # Check the content of the server.py file
        with open(server_file, 'r') as f:
            content = f.read()
            self.assertIn("Test Server", content)
            self.assertIn("FastMCP", content)
        
        # Check that the database was updated
        with open(self.test_db_file, 'r') as f:
            db = json.load(f)
            self.assertIn("12345678-1234-5678-1234-567812345678", db["servers"])
            
            server_data = db["servers"]["12345678-1234-5678-1234-567812345678"]
            self.assertEqual(server_data["name"], "Test Server")
            self.assertEqual(server_data["description"], "A test server for unit testing")
            self.assertEqual(server_data["tool_count"], 0)

    def test_create_multiple_servers(self):
        """Test creating multiple servers."""
        # Create first server
        result1 = create_server("Server 1", "First test server")
        server_id1 = result1["id"]
        
        # Create second server
        result2 = create_server("Server 2", "Second test server")
        server_id2 = result2["id"]
        
        # Verify unique IDs
        self.assertNotEqual(server_id1, server_id2)
        
        # Check both servers in database
        db = load_database()
        self.assertIn(server_id1, db["servers"])
        self.assertIn(server_id2, db["servers"])
        
        # Check both server directories
        self.assertTrue(os.path.exists(os.path.join(self.test_servers_dir, server_id1)))
        self.assertTrue(os.path.exists(os.path.join(self.test_servers_dir, server_id2)))

    def test_server_file_permissions(self):
        """Test that the server.py file has executable permissions."""
        result = create_server("Exec Test", "Testing file permissions")
        server_id = result["id"]
        
        server_file = os.path.join(self.test_servers_dir, server_id, "server.py")
        self.assertTrue(os.path.exists(server_file))
        
        # Check file permissions (executable)
        self.assertTrue(os.access(server_file, os.X_OK))


if __name__ == "__main__":
    unittest.main()

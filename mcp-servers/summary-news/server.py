#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context

# Create an MCP server
mcp = FastMCP("summary-news")
if __name__ == "__main__":
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        print("Server stopped by user")

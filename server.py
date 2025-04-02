#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context, Image
from typing import Dict, List, Optional, Any, Union
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("VibeCodeMCP")


# Add a sample resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    logger.info(f"Generating greeting for {name}")
    return f"Hello, {name}! Welcome to VibeCodeMCP."


# Add a sample tool
@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back to the client"""
    logger.info(f"Echoing message: {message}")
    return f"You said: {message}"


# Add a tool that uses context
@mcp.tool()
async def process_data(data_type: str, ctx: Context) -> str:
    """Process data with progress reporting"""
    logger.info(f"Processing data of type: {data_type}")
    
    # Example of using context for progress reporting
    total_steps = 5
    for i in range(total_steps):
        # Report progress to the client
        await ctx.report_progress(i, total_steps)
        ctx.info(f"Processing step {i+1}/{total_steps}")
    
    return f"Processed {data_type} data successfully"


# Add a sample prompt
@mcp.prompt()
def help_prompt() -> str:
    """Provide help information about this MCP server"""
    return """
    This is VibeCodeMCP, a Model Context Protocol server.
    
    Available resources:
    - greeting://{name} - Get a personalized greeting
    
    Available tools:
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

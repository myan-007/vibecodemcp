#!/usr/bin/env python3
"""
Server templates for MCP tool creation
"""

# Basic tool template with name, description, and no parameters
BASIC_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}() -> str:
    \"\"\"
    {tool_description}
    \"\"\"
    # Tool implementation
    return "Tool {tool_name} executed successfully"
"""

# String tool template with a single string parameter
STRING_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}(message: str) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        message: Input string message
    \"\"\"
    # Tool implementation
    return f"Tool {tool_name} processed: {{message}}"
"""

# Number tool template with numeric parameters
NUMBER_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}(a: float, b: float) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        a: First number
        b: Second number
    \"\"\"
    # Tool implementation
    result = a + b
    return f"Result: {{result}}"
"""

# List tool template with list parameter
LIST_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}(items: List[str]) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        items: List of items to process
    \"\"\"
    # Tool implementation
    item_count = len(items)
    return f"Processed {{item_count}} items"
"""

# Dict tool template with dictionary parameter
DICT_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}(data: Dict[str, Any]) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        data: Dictionary of data to process
    \"\"\"
    # Tool implementation
    keys = list(data.keys())
    return f"Processed data with keys: {{', '.join(keys)}}"
"""

# Async tool template
ASYNC_TOOL_TEMPLATE = """
@mcp.tool()
async def {tool_name}(query: str) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        query: Query string to process asynchronously
    \"\"\"
    # Async tool implementation
    await asyncio.sleep(1)  # Simulate async operation
    return f"Processed query: {{query}}"
"""

# Context tool template with progress reporting
CONTEXT_TOOL_TEMPLATE = """
@mcp.tool()
async def {tool_name}(data_type: str, ctx: Context) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        data_type: Type of data to process
        ctx: Context object for reporting progress
    \"\"\"
    # Tool implementation with progress reporting
    total_steps = 5
    for i in range(total_steps):
        # Report progress to the client
        await ctx.report_progress(i, total_steps)
        ctx.info(f"Processing step {{i+1}}/{{total_steps}}")
        await asyncio.sleep(0.5)  # Simulate work
    
    return f"Processed {{data_type}} data successfully"
"""

# Tool with file handling capabilities
FILE_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}(file_path: str) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        file_path: Path to the file to process
    \"\"\"
    # File handling implementation
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            line_count = len(content.splitlines())
        return f"File processed successfully. Contains {{line_count}} lines."
    except Exception as e:
        return f"Error processing file: {{str(e)}}"
"""

# Web API tool template
WEB_API_TOOL_TEMPLATE = """
@mcp.tool()
async def {tool_name}(query: str) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        query: Query string for the API
    \"\"\"
    # Web API implementation
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/search?q={{query}}")
            if response.status_code == 200:
                return f"API request successful: {{response.text[:100]}}..."
            else:
                return f"API error: {{response.status_code}}"
    except Exception as e:
        return f"Error calling API: {{str(e)}}"
"""

# Database tool template
DATABASE_TOOL_TEMPLATE = """
@mcp.tool()
def {tool_name}(query: str) -> str:
    \"\"\"
    {tool_description}
    
    Args:
        query: SQL-like query string
    \"\"\"
    # Database implementation (placeholder)
    # In a real implementation, you would connect to a database
    # and execute the query
    return f"Database query executed: {{query}}"
"""

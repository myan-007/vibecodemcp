#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context
import requests
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

# Create an MCP server
mcp = FastMCP("news-finder")

@mcp.tool("keyword_news")
def keyword_news(context: Context, keyword: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch top 10 news articles for a specific keyword and date using the GNEWS API.
    
    Args:
        context: The MCP context
        keyword: The keyword or phrase to search for
        date: The date to search for in YYYY-MM-DD format. If not provided, defaults to today.
    
    Returns:
        Dictionary containing top 10 news articles with title, source, description, and URL.
    """
    # Using GNEWS API which has a free tier
    API_KEY = "d1c8073e9b14c826955ae770e89a2333"  # Replace with your actual API key
    
    # Base URL for GNEWS API
    BASE_URL = "https://gnews.io/api/v4/search"
    
    # Parse date
    if date:
        try:
            search_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"error": f"Invalid date format. Please use YYYY-MM-DD format."}
    else:
        search_date = datetime.now()
    
    # Format date for the API (GNEWS uses a from parameter)
    from_date = search_date.strftime("%Y-%m-%d")
    
    # Set up the request parameters
    params = {
        "q": keyword,
        "from": from_date,
        "lang": "en",
        "token": API_KEY,
        "max": 10  # Limit to top 10 articles
    }
    
    try:
        # Make the request to the GNEWS API
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad responses
        
        # Parse the JSON response
        data = response.json()
        
        # Check if articles were found
        if len(data.get("articles", [])) == 0:
            return {"message": f"No articles found for keyword '{keyword}' on {from_date}."}
        
        # Format the articles for display
        articles = []
        for i, article in enumerate(data.get("articles", [])[:10], 1):
            articles.append({
                "number": i,
                "title": article.get("title", "No title"),
                "source": article.get("source", {}).get("name", "Unknown source"),
                "published_at": article.get("publishedAt", ""),
                "description": article.get("description", "No description"),
                "content": article.get("content", "No content available"),
                "url": article.get("url", ""),
                "image_url": article.get("image", "")
            })
        
        return {
            "message": f"Top {len(articles)} news articles for '{keyword}' on {from_date}:",
            "articles": articles
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching news: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Error parsing API response"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        print("Server stopped by user")

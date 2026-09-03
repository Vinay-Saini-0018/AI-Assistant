from config.settings import TAVILY_API_KEY
import requests
from tavily import TavilyClient
from langchain_core.tools import tool

@tool
def web_search(query : str):
    """Search the internet for current information."""
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)

        response = tavily.search(query,max_results=3)
        return response['results']
    except Exception as e:
        return f"web search failed : {str(e)}"

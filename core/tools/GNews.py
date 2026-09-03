from config.settings import GNews_API_KEY
from langchain_core.tools import tool
import requests

@tool
def get_news(query : str):
    """Get the latest news about a topic."""

    try: 
        url = "https://gnews.io/api/v4/search"

        para = {
            'q' : query,
            'lang' : 'en',
            'max' : 3,
            'apikey' : GNews_API_KEY
        }

        response = requests.get(url,params=para)
        return response.json()['articles']
    except Exception as e:
        return f"Cannot fetch new : {str(e)}"
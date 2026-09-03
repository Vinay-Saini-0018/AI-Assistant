from langchain_core.tools import tool
import requests 

@tool
def wikipedia_search(query : str):
    """Search Wikipedia for factual information."""

    try:
        url = "https://en.wikipedia.org/w/rest.php/v1/search/page"

        para = {
            'query' : query,
            'max' : 5
        }

        response = requests.get(url, params = para)
        return response.json()['pages']
    except Exception as e:
        return f"Unable to search on Wikipedia : {str(e)}"
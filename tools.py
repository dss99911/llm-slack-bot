from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool


@tool
def python_tool(code: str):
    """Execute python code."""
    return PythonREPLTool().invoke(code)

search_tool = TavilySearchResults(name="Search", max_results=2)

def get_tools():
    return [python_tool, search_tool]








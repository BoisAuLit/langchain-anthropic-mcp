"""
mcp_servers.py
==============
Defines and starts the MCP servers used by the wedding planner system.

LESSON RECAP — TWO WAYS TO CONNECT TO MCP
------------------------------------------
1. stdio (local)
   - Spawns a subprocess running a Python MCP server
   - Transport: "stdio"
   - Used for: local tools you control (e.g. Tavily search wrapper)
   - Config: {"command": "python", "args": ["path/to/server.py"]}

2. Streamable HTTP (remote)
   - Connects to a remote MCP server over HTTP
   - Transport: "streamable_http"
   - Used for: third-party hosted MCP servers (e.g. Kiwi flights API)
   - Config: {"url": "https://mcp.example.com"}

Both are loaded via MultiServerMCPClient, which gives you a unified list of
LangChain-compatible tools regardless of transport type.

WHAT'S IN THIS FILE
-------------------
- wedding_mcp_server(): FastMCP server with Tavily web search (run via stdio)
- get_mcp_tools(): async helper that connects to both MCP servers and returns tools
"""

from typing import Any, Dict

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

load_dotenv()

# ---------------------------------------------------------------------------
# LOCAL MCP SERVER (stdio transport)
# This server is launched as a subprocess by MultiServerMCPClient.
# It exposes a Tavily web search tool to any agent that connects to it.
# ---------------------------------------------------------------------------

mcp = FastMCP("wedding_search_server")
tavily_client = TavilyClient()


@mcp.tool()
def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web for up-to-date information using Tavily.
    Use this for venue research, catering options, DJ services, etc.

    Args:
        query: The search query string
    """
    return tavily_client.search(query)


@mcp.prompt()
def wedding_search_prompt() -> str:
    """System prompt for agents using this MCP server."""
    return (
        "You are a wedding planning assistant with access to web search. "
        "Use search_web to find real, current information. "
        "Always cite sources and provide actionable recommendations."
    )


# ---------------------------------------------------------------------------
# REMOTE MCP SERVER (streamable_http transport)
# The Kiwi.com MCP server provides live flight search — no local setup needed.
# MultiServerMCPClient connects to it over HTTP at invocation time.
# ---------------------------------------------------------------------------

KIWI_MCP_URL = "https://mcp.kiwi.com"


# ---------------------------------------------------------------------------
# HELPER: build the MultiServerMCPClient config and return tools
# ---------------------------------------------------------------------------

async def get_mcp_tools():
    """
    Connect to both MCP servers and return a combined list of LangChain tools.

    - local_search: stdio server (this file) → provides search_web
    - kiwi_flights: streamable_http server  → provides search-flight

    IMPORTANT: This is an async function because MCP connections are async.
    Call it with: tools = await get_mcp_tools()
    """
    import os
    from langchain_mcp_adapters.client import MultiServerMCPClient

    # Resolve absolute path to this file so stdio subprocess finds it
    # regardless of what directory the caller runs from
    this_file = os.path.abspath(__file__)

    client = MultiServerMCPClient(
        {
            # ── stdio: local Tavily search server ──────────────────────────
            # MultiServerMCPClient spawns `python mcp_servers.py` as a subprocess.
            # The server runs until the client disconnects.
            "local_search": {
                "transport": "stdio",
                "command": "python",
                "args": [this_file],
            },

            # ── streamable_http: remote Kiwi flights MCP server ────────────
            # No subprocess needed — just an HTTP connection to the remote URL.
            "kiwi_flights": {
                "transport": "streamable_http",
                "url": KIWI_MCP_URL,
            },
        }
    )

    tools = await client.get_tools()
    return tools, client   # return client too so caller can keep it alive


async def get_mcp_resources_and_prompts(client):
    """
    LESSON (from 2.1_mcp.ipynb): MCP servers can also expose resources and prompts,
    not just tools. This helper shows how to fetch them.

    Resources = static data the server provides (e.g. a README file)
    Prompts   = reusable prompt templates the server defines

    Usage:
        tools, client = await get_mcp_tools()
        resources, prompt = await get_mcp_resources_and_prompts(client)
    """
    # get_resources() returns resources from a specific server by name
    resources = await client.get_resources("local_search")

    # get_prompt() returns a prompt template from a specific server
    prompt_messages = await client.get_prompt("local_search", "wedding_search_prompt")
    prompt_text = prompt_messages[0].content if prompt_messages else ""

    return resources, prompt_text


# ---------------------------------------------------------------------------
# Entry point: run this file directly to start the stdio MCP server
# (MultiServerMCPClient will do this automatically via subprocess)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")

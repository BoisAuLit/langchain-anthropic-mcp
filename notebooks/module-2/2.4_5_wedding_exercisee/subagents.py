"""
subagents.py
============
Defines the 4 specialist subagents for the wedding planner system.

LESSON RECAP — MULTI-AGENT PATTERN
------------------------------------
From 2.3_multi_agent.ipynb:
  - Each subagent is a standalone create_agent() with its own tools
  - The coordinator calls subagents by wrapping them in @tool functions
  - The coordinator never calls subagent tools directly — it calls the wrapper
  - Subagents return their last message content as a string back to the coordinator

WHAT EACH SUBAGENT USES
------------------------
Venue Agent      → MCP (stdio: search_web via Tavily) + runtime context
Catering Agent   → regular @tool (no MCP needed) + runtime context
Transport Agent  → MCP (streamable_http: search-flight via Kiwi) + runtime context
DJ/Playlist Agent→ regular @tool + runtime context + state (writes playlist to state)

RUNTIME CONTEXT USAGE
----------------------
All subagents receive WeddingContext via context= at invoke time.
They expose context fields through @tool functions using ToolRuntime,
so the LLM never sees the raw context object — only what tools surface.

STATE USAGE
-----------
The DJ agent writes its playlist result into WeddingPlanState via Command(update={}).
This demonstrates how state can be updated mid-session by a subagent tool.
"""

from langchain.agents import create_agent
from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from context_and_state import WeddingContext, WeddingPlanState


# ===========================================================================
# 1. VENUE AGENT
#    Uses: MCP stdio (search_web) + runtime context
#    Context fields used: wedding_location, guest_count, budget_usd, wedding_date
# ===========================================================================

def create_venue_agent(mcp_tools: list):
    """
    The venue agent searches the web for wedding venues.

    It receives the couple's location, guest count, and budget via runtime context,
    accessed through tools — NOT injected directly into the prompt.

    mcp_tools: list of tools from MultiServerMCPClient (includes search_web)
    """

    # Context-reading tools — the LLM calls these to learn about the wedding
    @tool
    def get_venue_requirements(runtime: ToolRuntime) -> str:
        """Get the venue requirements: location, guest count, date, and budget."""
        ctx: WeddingContext = runtime.context
        return (
            f"Location: {ctx.wedding_location}\n"
            f"Date: {ctx.wedding_date}\n"
            f"Guests: {ctx.guest_count}\n"
            f"Budget: ${ctx.budget_usd:,} USD total"
        )

    # Wrap the MCP search tool so the LLM calls our clean interface
    # instead of the raw MCP tool (avoids parameter-wrapping issues)
    _search_mcp = next((t for t in mcp_tools if t.name == "search_web"), None)

    @tool
    async def search_venues(query: str) -> str:
        """
        Search the web for wedding venues using Tavily.

        Args:
            query: Search query, e.g. 'romantic wedding venues Paris 80 guests'
        """
        if _search_mcp is None:
            return "search_web MCP tool not available"
        result = await _search_mcp.ainvoke({"query": query})
        return str(result)

    all_tools = [get_venue_requirements, search_venues]

    agent = create_agent(
        model="gpt-5-nano",
        tools=all_tools,
        context_schema=WeddingContext,
        system_prompt=(
            "You are a wedding venue specialist. "
            "Use get_venue_requirements to understand the couple's needs, "
            "then use search_venues to find 2-3 real venue options. "
            "Return a concise recommendation with venue name, capacity, price range, and why it fits."
        ),
    )
    return agent


# ===========================================================================
# 2. CATERING AGENT
#    Uses: regular @tool (no MCP) + runtime context
#    Context fields used: guest_count, dietary_restrictions, budget_usd, wedding_location
# ===========================================================================

def create_catering_agent():
    """
    The catering agent recommends catering options based on the couple's context.

    This agent uses only regular @tool functions (no MCP) to demonstrate that
    not every agent needs MCP — sometimes simple tools are enough.
    """

    @tool
    def get_catering_requirements(runtime: ToolRuntime) -> str:
        """Get catering requirements: guest count, dietary needs, location, and budget."""
        ctx: WeddingContext = runtime.context
        return (
            f"Guests: {ctx.guest_count}\n"
            f"Dietary restrictions: {ctx.dietary_restrictions}\n"
            f"Location: {ctx.wedding_location}\n"
            f"Total budget: ${ctx.budget_usd:,} USD (catering is typically 30-40% of total)"
        )

    @tool
    def estimate_catering_cost(guests: int, style: str) -> str:
        """
        Estimate catering cost based on guest count and service style.

        Args:
            guests: Number of guests
            style: One of 'buffet', 'plated', 'cocktail'
        """
        rates = {"buffet": 85, "plated": 130, "cocktail": 65}
        rate = rates.get(style.lower(), 100)
        total = guests * rate
        return f"{style.title()} service for {guests} guests: ~${total:,} USD (${rate}/person)"

    @tool
    def suggest_menu(dietary_restrictions: str, style: str) -> str:
        """
        Suggest a wedding menu based on dietary restrictions and service style.

        Args:
            dietary_restrictions: e.g. 'vegan options required', 'nut-free'
            style: 'buffet', 'plated', or 'cocktail'
        """
        menus = {
            "buffet": "Roasted salmon, herb chicken, seasonal vegetables, artisan bread station",
            "plated": "Amuse-bouche, soup, choice of beef tenderloin or pan-seared halibut, dessert",
            "cocktail": "Passed canapés, charcuterie stations, mini desserts",
        }
        base = menus.get(style.lower(), "Custom menu")
        return f"{base}. Dietary note: {dietary_restrictions} — chef will prepare dedicated options."

    agent = create_agent(
        model="gpt-5-nano",
        tools=[get_catering_requirements, estimate_catering_cost, suggest_menu],
        context_schema=WeddingContext,
        system_prompt=(
            "You are a wedding catering specialist. "
            "Use get_catering_requirements first, then estimate costs and suggest a menu. "
            "Provide a clear recommendation with style, estimated cost, and sample menu."
        ),
    )
    return agent


# ===========================================================================
# 3. TRANSPORT AGENT
#    Uses: MCP streamable_http (search-flight via Kiwi) + runtime context
#    Context fields used: home_city, wedding_location, wedding_date, couple_names
# ===========================================================================

def create_transport_agent(mcp_tools: list):
    """
    The transport agent finds flights for the couple and key guests.

    Uses the Kiwi MCP server (streamable_http) for live flight search,
    and runtime context to know where the couple is flying from/to.
    """

    @tool
    def get_transport_requirements(runtime: ToolRuntime) -> str:
        """Get transport requirements: origin city, destination, and travel date."""
        ctx: WeddingContext = runtime.context
        return (
            f"Couple: {ctx.couple_names}\n"
            f"Flying from: {ctx.home_city}\n"
            f"Wedding location: {ctx.wedding_location}\n"
            f"Wedding date: {ctx.wedding_date}\n"
            f"Guests to consider: {ctx.guest_count}"
        )

    # Wrap the MCP flight search tool with a clean interface
    _flight_mcp = next((t for t in mcp_tools if "flight" in t.name.lower()), None)

    @tool
    async def search_flights(
        fly_from: str, fly_to: str, departure_date: str
    ) -> str:
        """
        Search for flights using the Kiwi MCP server.

        Args:
            fly_from: Departure city, e.g. 'New York'
            fly_to: Arrival city, e.g. 'Paris'
            departure_date: Date in DD/MM/YYYY format, e.g. '13/09/2026'
        """
        if _flight_mcp is None:
            return "search-flight MCP tool not available"
        result = await _flight_mcp.ainvoke({
            "flyFrom": fly_from,
            "flyTo": fly_to,
            "departureDate": departure_date,
            "passengers": {"adults": 1},
            "cabinClass": "M",
            "sort": "price",
            "curr": "USD",
            "locale": "en",
        })
        return str(result)

    all_tools = [get_transport_requirements, search_flights]

    agent = create_agent(
        model="gpt-5-nano",
        tools=all_tools,
        context_schema=WeddingContext,
        system_prompt=(
            "You are a wedding travel coordinator. "
            "Use get_transport_requirements to understand the travel needs, "
            "then use search_flights to find the best flight options. "
            "Recommend 1-2 flights with price, duration, and booking link. "
            "Use DD/MM/YYYY format for dates."
        ),
    )
    return agent


# ===========================================================================
# 4. DJ / PLAYLIST AGENT
#    Uses: regular @tool + runtime context + STATE (writes playlist to state)
#    Context fields used: music_style, couple_names
#    State: writes playlist_result via Command(update={...})
# ===========================================================================

def create_dj_agent():
    """
    The DJ agent curates a wedding playlist and writes it into state.

    This agent demonstrates BOTH runtime context (read music preferences)
    AND state mutation (write the final playlist back into WeddingPlanState).

    The playlist_result field in state persists across turns — if the coordinator
    asks a follow-up question, the DJ agent can read back what it already wrote.
    """

    @tool
    def get_music_preferences(runtime: ToolRuntime) -> str:
        """Get the couple's music style and names for personalisation."""
        ctx: WeddingContext = runtime.context
        return f"Couple: {ctx.couple_names}\nMusic style: {ctx.music_style}"

    @tool
    def read_current_playlist(runtime: ToolRuntime) -> str:
        """Read the current playlist from state (if one has already been set)."""
        try:
            playlist = runtime.state.get("playlist_result", "")
            return playlist if playlist else "No playlist set yet."
        except Exception:
            return "No playlist set yet."

    @tool
    def save_playlist_to_state(playlist: str, runtime: ToolRuntime) -> Command:
        """
        Save the final curated playlist into the agent state.

        This uses Command(update={...}) — the LangGraph way to mutate state
        from inside a tool. The update is applied atomically after the tool returns.

        Args:
            playlist: The formatted playlist string to save
        """
        return Command(
            update={
                "playlist_result": playlist,
                "messages": [
                    ToolMessage(
                        content=f"Playlist saved to state: {playlist[:80]}...",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    @tool
    def curate_playlist(music_style: str, couple_names: str) -> str:
        """
        Curate a wedding playlist based on music style.

        Args:
            music_style: e.g. 'jazz and soul', 'pop', 'classical'
            couple_names: e.g. 'Alice & Bob'
        """
        playlists = {
            "jazz": [
                "At Last – Etta James",
                "La Vie en Rose – Édith Piaf",
                "Fly Me to the Moon – Frank Sinatra",
                "The Way You Look Tonight – Tony Bennett",
                "Feeling Good – Nina Simone",
            ],
            "pop": [
                "Perfect – Ed Sheeran",
                "Thinking Out Loud – Ed Sheeran",
                "A Thousand Years – Christina Perri",
                "Can't Help Falling in Love – Elvis Presley",
                "All of Me – John Legend",
            ],
            "classical": [
                "Canon in D – Pachelbel",
                "Air on the G String – Bach",
                "Clair de Lune – Debussy",
                "Moonlight Sonata – Beethoven",
                "Gymnopédie No.1 – Satie",
            ],
        }

        # Match by keyword
        style_lower = music_style.lower()
        matched = []
        for key, songs in playlists.items():
            if key in style_lower:
                matched.extend(songs)

        if not matched:
            matched = playlists["pop"]  # default fallback

        songs_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(matched))
        return (
            f"🎵 Wedding Playlist for {couple_names}\n"
            f"Style: {music_style}\n\n"
            f"Ceremony & Reception:\n{songs_str}"
        )

    agent = create_agent(
        model="gpt-5-nano",
        tools=[get_music_preferences, curate_playlist, save_playlist_to_state, read_current_playlist],
        context_schema=WeddingContext,
        state_schema=WeddingPlanState,
        checkpointer=InMemorySaver(),
        system_prompt=(
            "You are a wedding DJ and music curator. "
            "Use get_music_preferences to learn the couple's style, "
            "then curate_playlist to build the setlist, "
            "then save_playlist_to_state to persist it. "
            "Return a warm, personalised playlist summary."
        ),
    )
    return agent

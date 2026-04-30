"""
wedding_planner.py
==================
The main coordinator agent that orchestrates the 4 specialist subagents.

LESSON RECAP — COORDINATOR + SUBAGENT PATTERN
----------------------------------------------
From 2.3_multi_agent.ipynb:

  Step 1: Create subagents (each is a standalone create_agent())
  Step 2: Wrap each subagent in a @tool function
          → The coordinator calls the wrapper tool, not the subagent directly
          → The wrapper invokes the subagent and returns its last message as a string
  Step 3: Create the coordinator with those wrapper tools
  Step 4: The coordinator decides which subagents to call and in what order

WHAT THIS FILE DEMONSTRATES
-----------------------------
✅ MCP (stdio)           — venue agent uses Tavily search via local MCP server
✅ MCP (streamable_http) — transport agent uses Kiwi flights via remote MCP server
✅ Runtime context       — all subagents read WeddingContext via ToolRuntime
✅ State (read)          — coordinator reads subagent results from WeddingPlanState
✅ State (write)         — DJ agent writes playlist into state via Command(update={})
✅ Multi-agent           — coordinator delegates to 4 specialist subagents
✅ Checkpointer          — coordinator uses InMemorySaver for multi-turn conversations

EXTRA CONCEPT: STRUCTURED STATE ACCUMULATION
---------------------------------------------
The coordinator writes each subagent's result into state as it comes in.
This means if the conversation spans multiple turns, results are never lost.
The final_plan field is only written once all 4 subagents have reported back.

HOW TO RUN
----------
    python wedding_planner.py

Or import and call plan_wedding() from a notebook.
"""

import asyncio
import logging
import os
import warnings

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from context_and_state import WeddingContext, WeddingPlanState
from mcp_servers import get_mcp_tools
from subagents import (
    create_catering_agent,
    create_dj_agent,
    create_transport_agent,
    create_venue_agent,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Colorized, categorized logging for readable iTerm2 output
# ---------------------------------------------------------------------------
# Suppress Pydantic serializer warnings (known issue with context_schema)
warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*")

# ANSI color codes for iTerm2
_RESET = "\033[0m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_BLUE = "\033[34m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_MAGENTA = "\033[35m"
_RED = "\033[31m"


class _ColorLogFormatter(logging.Formatter):
    """
    Custom formatter that categorizes and colorizes log lines by source.

    Categories:
      🌐 MCP     — MCP server connections, tool calls, session negotiation
      🔗 HTTP    — raw HTTP requests (dimmed, less important)
      🤖 LLM    — OpenAI API calls
      📋 SYSTEM  — everything else
    """

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        name = record.name.lower()

        # Categorize by logger name + message content
        if "mcp" in name or "streamable_http" in name:
            if "session ID" in msg or "protocol version" in msg:
                return f"  {_DIM}{_CYAN}🌐 MCP    {msg}{_RESET}"
            if "CallToolRequest" in msg:
                return f"  {_GREEN}🔨 MCP    Tool call executing{_RESET}"
            if "ListToolsRequest" in msg:
                return f"  {_CYAN}🔌 MCP    Listing available tools{_RESET}"
            if "disconnected" in msg:
                return f"  {_DIM}{_YELLOW}🌐 MCP    {msg}{_RESET}"
            return f"  {_DIM}{_CYAN}🌐 MCP    {msg}{_RESET}"

        if "httpx" in name or "httpcore" in name or "HTTP Request" in msg:
            if "openai.com" in msg:
                return f"  {_MAGENTA}🤖 LLM    {msg}{_RESET}"
            if "mcp.kiwi.com" in msg:
                return f"  {_DIM}{_BLUE}✈️  KIWI   {msg}{_RESET}"
            if "tavily" in msg.lower():
                return f"  {_DIM}{_GREEN}🔍 TAVILY {msg}{_RESET}"
            # Generic HTTP — dim it
            return f"  {_DIM}🔗 HTTP   {msg}{_RESET}"

        # FastMCP server-side logs
        if "server" in name:
            return f"  {_GREEN}⚙️  SERVER {msg}{_RESET}"

        # Fallback
        return f"  {_DIM}📋 SYSTEM {msg}{_RESET}"


def _setup_logging():
    """Replace the root handler with our colorized formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(_ColorLogFormatter())

    # Apply to root logger so all libraries get formatted
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Keep httpx at INFO so we see the requests (but formatted nicely)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


_setup_logging()


# ===========================================================================
# COORDINATOR SETUP
# ===========================================================================


async def build_coordinator(wedding_context: WeddingContext):
    """
    Build the coordinator agent with all 4 subagent wrapper tools.

    This is async because we need to connect to MCP servers first.
    The MCP client must stay alive for the duration of the session,
    so we return it alongside the coordinator.
    """

    # ── Step 1: Connect to MCP servers and get tools ──────────────────────
    # get_mcp_tools() connects to both the local stdio server (Tavily search)
    # and the remote streamable_http server (Kiwi flights).
    print("🔌 Connecting to MCP servers...")
    mcp_tools, mcp_client = await get_mcp_tools()

    # Separate tools by server so we give each subagent only what it needs
    search_tools = [t for t in mcp_tools if t.name == "search_web"]
    flight_tools = [t for t in mcp_tools if "flight" in t.name.lower()]

    print(f"   ✅ MCP tools loaded: {[t.name for t in mcp_tools]}")

    # ── Step 2: Create the 4 specialist subagents ─────────────────────────
    venue_agent = create_venue_agent(search_tools)
    catering_agent = create_catering_agent()
    transport_agent = create_transport_agent(flight_tools)
    dj_agent = create_dj_agent()

    # ── Step 3: Wrap each subagent in a @tool for the coordinator ─────────
    # The coordinator calls these tools. Each wrapper:
    #   1. Invokes the subagent with a task description
    #   2. Passes the WeddingContext so the subagent can read it via ToolRuntime
    #   3. Returns the subagent's final message as a string
    #   4. Also writes the result into coordinator state via Command(update={})

    @tool
    async def call_venue_agent(task: str, runtime: ToolRuntime) -> Command:
        """
        Delegate venue research to the venue specialist agent.
        The agent will search for real venues matching the couple's requirements.

        Args:
            task: Description of what to find (e.g. 'Find a romantic venue in Paris for 80 guests')
        """
        print(f"\n🏛️  Venue agent called with: {task}")
        response = await venue_agent.ainvoke(
            {"messages": [HumanMessage(content=task)]},
            context=wedding_context,  # ← runtime context passed here
        )
        result = response["messages"][-1].content
        print("   ✅ Venue agent done.")

        # Write result into coordinator state
        return Command(
            update={
                "venue_result": result,
                "messages": [
                    ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
                ],
            }
        )

    @tool
    async def call_catering_agent(task: str, runtime: ToolRuntime) -> Command:
        """
        Delegate catering planning to the catering specialist agent.
        The agent will recommend a catering style, menu, and cost estimate.

        Args:
            task: Description of what to plan (e.g. 'Plan catering for 80 guests with vegan options')
        """
        print(f"\n🍽️  Catering agent called with: {task}")
        response = await catering_agent.ainvoke(
            {"messages": [HumanMessage(content=task)]},
            context=wedding_context,
        )
        result = response["messages"][-1].content
        print("   ✅ Catering agent done.")

        return Command(
            update={
                "catering_result": result,
                "messages": [
                    ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
                ],
            }
        )

    @tool
    async def call_transport_agent(task: str, runtime: ToolRuntime) -> Command:
        """
        Delegate flight search to the transport specialist agent.
        The agent will find real flights using the Kiwi MCP server.

        Args:
            task: Description of what to find (e.g. 'Find flights from New York to Paris for the wedding')
        """
        print(f"\n✈️  Transport agent called with: {task}")
        response = await transport_agent.ainvoke(
            {"messages": [HumanMessage(content=task)]},
            context=wedding_context,
        )
        result = response["messages"][-1].content
        print("   ✅ Transport agent done.")

        return Command(
            update={
                "transport_result": result,
                "messages": [
                    ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
                ],
            }
        )

    @tool
    async def call_dj_agent(task: str, runtime: ToolRuntime) -> Command:
        """
        Delegate playlist curation to the DJ specialist agent.
        The agent will curate a personalised playlist and save it to state.

        Args:
            task: Description of what to create (e.g. 'Create a jazz wedding playlist for Alice & Bob')
        """
        print(f"\n🎵  DJ agent called with: {task}")
        response = await dj_agent.ainvoke(
            {"messages": [HumanMessage(content=task)]},
            {"configurable": {"thread_id": "dj-session-1"}},
            context=wedding_context,
        )
        result = response["messages"][-1].content
        # Also grab playlist from state if the DJ agent wrote it there
        playlist_from_state = response.get("playlist_result", result)
        print("   ✅ DJ agent done.")

        return Command(
            update={
                "playlist_result": playlist_from_state,
                "messages": [
                    ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
                ],
            }
        )

    # ── State-reading tool: lets coordinator check what's been collected ──
    @tool
    def read_planning_progress(runtime: ToolRuntime) -> str:
        """
        Read the current state of the wedding plan.
        Use this to check which subagents have reported back before writing the final plan.
        """
        state = runtime.state
        sections = []
        for field, label in [
            ("venue_result", "🏛️  Venue"),
            ("catering_result", "🍽️  Catering"),
            ("transport_result", "✈️  Transport"),
            ("playlist_result", "🎵  Playlist"),
        ]:
            value = state.get(field, "")
            status = "✅ Done" if value else "⏳ Pending"
            sections.append(f"{label}: {status}")
        return "\n".join(sections)

    # ── Final plan tool: writes the assembled plan into state ─────────────
    @tool
    def write_final_plan(plan: str, runtime: ToolRuntime) -> Command:
        """
        Write the final assembled wedding plan into state.
        Call this only after all 4 subagents have reported back.

        Args:
            plan: The complete formatted wedding plan
        """
        return Command(
            update={
                "final_plan": plan,
                "messages": [
                    ToolMessage(
                        content="Final plan saved.", tool_call_id=runtime.tool_call_id
                    )
                ],
            }
        )

    # ── Step 4: Create the coordinator ────────────────────────────────────
    coordinator = create_agent(
        model="gpt-5-nano",
        tools=[
            call_venue_agent,
            call_catering_agent,
            call_transport_agent,
            call_dj_agent,
            read_planning_progress,
            write_final_plan,
        ],
        context_schema=WeddingContext,
        state_schema=WeddingPlanState,
        checkpointer=InMemorySaver(),  # enables multi-turn conversation
        system_prompt=(
            "You are the main wedding planning coordinator. "
            "Your job is to delegate to 4 specialist subagents and compile their results.\n\n"
            "WORKFLOW:\n"
            "1. Call all 4 subagents (venue, catering, transport, DJ) with clear task descriptions\n"
            "2. Use read_planning_progress to verify all results are in\n"
            "3. Call write_final_plan with a beautifully formatted complete wedding plan\n"
            "4. Present the final plan to the couple\n\n"
            "Be warm, organised, and thorough. The couple is counting on you!"
        ),
    )

    return coordinator, mcp_client


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================


async def plan_wedding(
    couple_names: str = "Alice & Bob",
    wedding_date: str = "2026-09-15",
    wedding_location: str = "Paris, France",
    guest_count: int = 80,
    budget_usd: int = 50_000,
    music_style: str = "jazz and soul",
    dietary_restrictions: str = "vegan options required",
    home_city: str = "New York",
):
    """
    Run the full wedding planning system.

    This function demonstrates the complete flow:
    - Runtime context is built from the couple's details
    - The coordinator is created with all subagent tools
    - A single ainvoke call kicks off the full multi-agent workflow
    - State accumulates results as each subagent reports back
    """

    # Build the runtime context instance
    # This is what gets passed as context= at invoke time
    context = WeddingContext(
        couple_names=couple_names,
        wedding_date=wedding_date,
        wedding_location=wedding_location,
        guest_count=guest_count,
        budget_usd=budget_usd,
        music_style=music_style,
        dietary_restrictions=dietary_restrictions,
        home_city=home_city,
    )

    print(f"\n💍 Starting wedding planner for {couple_names}")
    print(f"   📅 Date: {wedding_date} | 📍 Location: {wedding_location}")
    print(f"   👥 Guests: {guest_count} | 💰 Budget: ${budget_usd:,}\n")

    # Build coordinator (connects to MCP servers, creates subagents)
    coordinator, mcp_client = await build_coordinator(context)

    # The initial request to the coordinator
    user_request = (
        f"Please plan our complete wedding! "
        f"We are {couple_names}, getting married on {wedding_date} in {wedding_location}. "
        f"We have {guest_count} guests and a budget of ${budget_usd:,}. "
        f"We love {music_style} music and need {dietary_restrictions}. "
        f"We're flying from {home_city}. Please coordinate everything!"
    )

    config = {"configurable": {"thread_id": "wedding-plan-1"}}

    print("🚀 Coordinator starting...\n")
    print("=" * 60)

    response = await coordinator.ainvoke(
        {
            "messages": [HumanMessage(content=user_request)],
        },
        config=config,
        context=context,  # ← runtime context passed to coordinator
    )

    print("\n" + "=" * 60)
    print("\n📋 FINAL WEDDING PLAN\n")

    final_content = response["messages"][-1].content
    print(final_content)

    # Show what ended up in state
    print("\n\n📊 STATE SUMMARY (what was persisted)")
    print("-" * 40)
    for field in [
        "venue_result",
        "catering_result",
        "transport_result",
        "playlist_result",
        "final_plan",
    ]:
        value = response.get(field, "")
        if value:
            preview = value[:100].replace("\n", " ")
            print(f"  {field}: {preview}...")

    # ── Write the final plan to plan.md ───────────────────────────────────
    output_dir = os.path.dirname(os.path.abspath(__file__))
    plan_path = os.path.join(output_dir, "plan.md")

    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(f"# 💍 Wedding Plan for {couple_names}\n\n")
        f.write(f"**Date:** {wedding_date}  \n")
        f.write(f"**Location:** {wedding_location}  \n")
        f.write(f"**Guests:** {guest_count}  \n")
        f.write(f"**Budget:** ${budget_usd:,}  \n")
        f.write(f"**Music:** {music_style}  \n")
        f.write(f"**Dietary:** {dietary_restrictions}  \n\n")
        f.write("---\n\n")
        f.write("## 📋 Coordinator's Final Plan\n\n")
        f.write(final_content + "\n\n")
        f.write("---\n\n")

        # Write each subagent's detailed result as its own section
        section_labels = {
            "venue_result": "🏛️ Venue Research",
            "catering_result": "🍽️ Catering Plan",
            "transport_result": "✈️ Transport & Flights",
            "playlist_result": "🎵 DJ & Playlist",
        }
        for field, label in section_labels.items():
            value = response.get(field, "")
            if value:
                f.write(f"## {label}\n\n")
                f.write(value + "\n\n")
                f.write("---\n\n")

    print(f"\n📝 Plan saved to: {plan_path}")

    return response


# ===========================================================================
# MULTI-TURN EXAMPLE
# Demonstrates that state persists across multiple invocations (same thread_id)
# ===========================================================================


async def follow_up_example(coordinator, context: WeddingContext):
    """
    Shows how the coordinator can answer follow-up questions using persisted state.

    Because we use InMemorySaver with the same thread_id, the coordinator
    remembers everything from the first invocation.
    """
    config = {"configurable": {"thread_id": "wedding-plan-1"}}

    follow_up = "Can you give me just the playlist again? And what was the venue recommendation?"

    print("\n\n💬 FOLLOW-UP QUESTION (multi-turn demo)")
    print(f"User: {follow_up}\n")

    response = await coordinator.ainvoke(
        {"messages": [HumanMessage(content=follow_up)]},
        config=config,
        context=context,
    )

    print("Coordinator:", response["messages"][-1].content)
    return response


if __name__ == "__main__":
    asyncio.run(plan_wedding())

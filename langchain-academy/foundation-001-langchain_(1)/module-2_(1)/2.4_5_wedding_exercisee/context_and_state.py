"""
context_and_state.py
====================
Defines the shared Context and State schemas for the wedding planner system.

LESSON RECAP
------------
context_schema  → type declaration passed to create_agent(); tells the framework
                  what shape the runtime context will have. No data here.
context=        → the actual instance passed at invoke/ainvoke time. This is the
                  live data injected into ToolRuntime for tools to read.

state_schema    → type declaration passed to create_agent(); extends AgentState
                  with extra fields the agent can read AND write during a session.
State           → mutable, persisted across turns (with a checkpointer), written
                  by tools via Command(update={...}).

KEY DIFFERENCE
--------------
Context  = what YOU already know before the conversation (read-only, per-call)
State    = what the AGENT discovers/builds during the conversation (mutable, persisted)
"""

from dataclasses import dataclass
from langchain.agents import AgentState


# ---------------------------------------------------------------------------
# RUNTIME CONTEXT
# Injected by the caller at invoke time. Read-only from the agent's perspective.
# Think: user profile, preferences, budget — things your backend already has.
# ---------------------------------------------------------------------------

@dataclass
class WeddingContext:
    """
    Passed as context_schema= when creating agents, and as context= when invoking.

    Because this is a dataclass with defaults, the agent framework can validate
    the shape. In a real app you'd omit defaults and always supply real values.
    """
    couple_names: str = "Alice & Bob"
    wedding_date: str = "2026-09-15"
    wedding_location: str = "Paris, France"
    guest_count: int = 80
    budget_usd: int = 50_000
    music_style: str = "jazz and soul"          # used by DJ agent
    dietary_restrictions: str = "vegan options required"  # used by catering agent
    home_city: str = "New York"                 # used by transport agent


# ---------------------------------------------------------------------------
# STATE SCHEMA
# Extends AgentState so the coordinator can accumulate results from subagents
# across multiple turns. Written by tools via Command(update={...}).
# ---------------------------------------------------------------------------

class WeddingPlanState(AgentState):
    """
    Mutable state that grows as the coordinator collects results.

    Fields start empty/None and get filled in as each subagent reports back.
    Unlike context, state has NO default values — it must be written explicitly.

    NOTE: AgentState already includes a `messages` field (the conversation history).
    We only add the extra fields we need.
    """
    venue_result: str           # filled by venue subagent
    catering_result: str        # filled by catering subagent
    transport_result: str       # filled by transport subagent
    playlist_result: str        # filled by DJ subagent
    final_plan: str             # filled by coordinator once all results are in

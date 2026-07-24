from typing import Any

import anthropic

from console import ConsoleView
from tools import tools, execute_tool
from tracer import save_messages_json, MESSAGES_DIR

SYSTEM_PROMPT = """
You are a research assistant.

Rules:
1. If the user asks to search papers, call search_papers first.
2. Do not call extract_info until you have received actual paper IDs from search_papers.
3. After search_papers returns paper IDs, you may call extract_info for those actual paper IDs.
4. If there are multiple tool calls in one assistant message, the user will return all tool results together.
"""


def process_query(client: anthropic.Anthropic, query: str) -> None:
    """
    Core agent loop:

    1. Save + print messages before API call
    2. Send messages to Claude
    3. Append Claude response to messages
    4. Save + print messages after assistant response
    5. Execute every tool_use Claude requested
    6. Append all tool_results together
    7. Save + print messages after user tool_results
    8. Repeat until Claude returns no tool_use
    """
    messages = [{"role": "user", "content": query}]
    round_number = 1

    while True:
        ConsoleView.round_header(round_number, len(messages))

        _trace(messages, round_number, "before_api_call", query)

        response = client.messages.create(
            max_tokens=2024,
            model="claude-sonnet-4-6",
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        ConsoleView.response_snapshot(response, round_number)

        messages.append({"role": "assistant", "content": response.content})

        _trace(messages, round_number, "after_assistant_response", query)

        tool_results = _collect_tool_results(response)

        ConsoleView.info("tool_results this round", len(tool_results), icon="🧺")

        if not tool_results:
            ConsoleView.success("No tool calls. Agent loop finished.")
            break

        messages.append({"role": "user", "content": tool_results})

        _trace(messages, round_number, "after_user_tool_results", query)

        round_number += 1


def _trace(
    messages: list[dict[str, Any]],
    round_number: int,
    stage: str,
    query: str,
) -> None:
    ConsoleView.messages_snapshot(messages=messages, round_number=round_number, stage=stage)
    save_messages_json(messages=messages, round_number=round_number, stage=stage, query=query)


def _collect_tool_results(response) -> list[dict[str, str]]:
    tool_results = []

    for content in response.content:
        if content.type == "text":
            ConsoleView.assistant_text(content.text)
            continue

        if content.type == "tool_use":
            result = execute_tool(content.name, content.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": result,
            })

    return tool_results


def chat_loop(client: anthropic.Anthropic) -> None:
    ConsoleView.title("Anthropic Tool Calling Debug Console")
    print("Type your queries or 'quit' to exit.")
    print(f"Messages JSON traces will be saved under: {MESSAGES_DIR}/")

    while True:
        try:
            query = input("\nQuery: ").strip()
            if query.lower() == "quit":
                break
            process_query(client, query)
            print()
        except Exception as e:
            ConsoleView.error(f"{type(e).__name__}: {str(e)}")

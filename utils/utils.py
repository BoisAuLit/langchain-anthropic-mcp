import json


def ppm(message):
    """Pretty print all details of a LangChain message."""
    data = {
        "type": message.__class__.__name__,
        "content": message.content,
        "additional_kwargs": message.additional_kwargs,
        "response_metadata": message.response_metadata,
        "id": message.id,
        "tool_calls": message.tool_calls if hasattr(message, "tool_calls") else [],
        "invalid_tool_calls": message.invalid_tool_calls
        if hasattr(message, "invalid_tool_calls")
        else [],
        "usage_metadata": dict(message.usage_metadata)
        if message.usage_metadata
        else None,
    }
    print(json.dumps(data, indent=2, default=str))


def ppms(messages):
    """Pretty print messages from LangChain (list) or LangGraph (dict with 'messages' key)."""
    # Handle LangGraph state dict
    if isinstance(messages, dict):
        messages = messages["messages"]

    # Handle single message object (not a list)
    if not isinstance(messages, list):
        messages = [messages]

    for i, msg in enumerate(messages):
        print(f"\n--- Message {i + 1} ---")

        # Handle plain strings (e.g. raw prompt strings in a message list)
        if isinstance(msg, str):
            print(f"Type: str")
            print(f"Content: {msg}")
            continue

        print(f"Type: {msg.__class__.__name__}")
        print(f"ID: {msg.id}")

        if hasattr(msg, "content") and msg.content:
            print(f"Content: {msg.content}")

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("Tool Calls:")
            for tc in msg.tool_calls:
                print(f"  - name: {tc['name']}")
                print(f"    args: {tc['args']}")

        if hasattr(msg, "name"):
            print(f"Tool Name: {msg.name}")

        if hasattr(msg, "usage_metadata") and msg.usage_metadata:
            print("Usage:")
            print(msg.usage_metadata)

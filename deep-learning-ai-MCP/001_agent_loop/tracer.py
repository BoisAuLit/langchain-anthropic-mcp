import json
import os
import re
import shutil
from datetime import datetime
from typing import Any

from console import ConsoleView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_DIR = os.path.join(BASE_DIR, "messages")


def reset_messages_dir() -> None:
    """Clear old messages/ folder so each run starts fresh."""
    if os.path.exists(MESSAGES_DIR):
        shutil.rmtree(MESSAGES_DIR)
    os.makedirs(MESSAGES_DIR, exist_ok=True)
    ConsoleView.success(f"Reset messages directory: {MESSAGES_DIR}")


def block_to_plain_json(block: Any) -> Any:
    if isinstance(block, dict):
        return block

    block_type = getattr(block, "type", None)

    if block_type == "text":
        return {"type": "text", "text": getattr(block, "text", "")}

    if block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": getattr(block, "id", None),
            "name": getattr(block, "name", None),
            "input": getattr(block, "input", None),
        }

    return {"type": block_type or type(block).__name__, "raw": str(block)}


def messages_to_plain_json(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plain = []
    for msg in messages:
        content = msg.get("content")
        plain_content = (
            [block_to_plain_json(b) for b in content]
            if isinstance(content, list)
            else content
        )
        plain.append({"role": msg.get("role"), "content": plain_content})
    return plain


def stage_order(stage: str) -> int:
    return {"before_api_call": 1, "after_assistant_response": 2, "after_user_tool_results": 3}.get(stage, 99)


def stage_to_filename(stage: str) -> str:
    stage = stage.lower()
    stage = re.sub(r"[^a-z0-9]+", "_", stage)
    return stage.strip("_")


def save_messages_json(
    messages: list[dict[str, Any]],
    round_number: int,
    stage: str,
    query: str,
) -> str:
    os.makedirs(MESSAGES_DIR, exist_ok=True)

    filename = (
        f"round_{round_number:02d}_"
        f"{stage_order(stage):02d}_"
        f"{stage_to_filename(stage)}.json"
    )
    path = os.path.join(MESSAGES_DIR, filename)

    payload = {
        "metadata": {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "round": round_number,
            "stage_order": stage_order(stage),
            "stage": stage,
            "query": query,
            "messages_length": len(messages),
        },
        "messages": messages_to_plain_json(messages),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    ConsoleView.file_saved(path)
    return path

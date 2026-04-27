import arxiv
import json
import os
import re
import shutil
from datetime import datetime
from typing import Any, List
from dotenv import load_dotenv
import anthropic


PAPER_DIR = "papers"

# Make messages/ relative to this Python file, not relative to where uv run is executed.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_DIR = os.path.join(BASE_DIR, "messages")


# =============================================================================
# Pretty terminal output helpers
# =============================================================================

class ConsoleView:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    GRAY = "\033[90m"

    @classmethod
    def line(cls, char: str = "─", width: int = 96, color: str | None = None) -> None:
        text = char * width
        print(f"{color or ''}{text}{cls.RESET if color else ''}")

    @classmethod
    def title(cls, text: str) -> None:
        print()
        cls.line("═", color=cls.CYAN)
        print(f"{cls.BOLD}{cls.CYAN}🚀 {text}{cls.RESET}")
        cls.line("═", color=cls.CYAN)

    @classmethod
    def round_header(cls, round_number: int, messages_len: int) -> None:
        print()
        cls.line("═", color=cls.BLUE)
        print(
            f"{cls.BOLD}{cls.BLUE}🔁 ROUND {round_number}{cls.RESET}  "
            f"{cls.GRAY}| messages length = {messages_len}{cls.RESET}"
        )
        cls.line("═", color=cls.BLUE)

    @classmethod
    def section(cls, icon: str, title: str, color: str | None = None) -> None:
        print()
        cls.line("─", color=color or cls.GRAY)
        print(f"{color or ''}{cls.BOLD}{icon} {title}{cls.RESET}")
        cls.line("─", color=color or cls.GRAY)

    @classmethod
    def info(cls, label: str, value: Any, icon: str = "•") -> None:
        print(f"  {icon} {cls.BOLD}{label}:{cls.RESET} {value}")

    @classmethod
    def success(cls, text: str) -> None:
        print(f"{cls.GREEN}✅ {text}{cls.RESET}")

    @classmethod
    def warn(cls, text: str) -> None:
        print(f"{cls.YELLOW}⚠️  {text}{cls.RESET}")

    @classmethod
    def error(cls, text: str) -> None:
        print(f"{cls.RED}❌ {text}{cls.RESET}")

    @classmethod
    def file_saved(cls, path: str) -> None:
        print(f"{cls.CYAN}💾 saved messages JSON:{cls.RESET} {path}")

    @classmethod
    def assistant_text(cls, text: str) -> None:
        cls.section("💬", "Assistant text", cls.MAGENTA)
        print(indent_text(text, spaces=2))

    @classmethod
    def tool_call(cls, tool_name: str, tool_args: dict[str, Any]) -> None:
        print(f"\n  {cls.GREEN}🛠️  Calling tool:{cls.RESET} {cls.BOLD}{tool_name}{cls.RESET}")
        print(f"  {cls.GRAY}args = {json.dumps(tool_args, ensure_ascii=False)}{cls.RESET}")

    @classmethod
    def tool_result(cls, result: str, max_chars: int = 700) -> None:
        preview = truncate(result, max_chars)
        print(f"  {cls.GREEN}↳ tool result preview:{cls.RESET}")
        print(indent_text(preview, spaces=4))

    @classmethod
    def messages_snapshot(cls, messages: list[dict[str, Any]], round_number: int, stage: str) -> None:
        cls.section("🧾", f"FULL MESSAGES SNAPSHOT — Round {round_number} — {stage}", cls.YELLOW)
        print(f"  {cls.BOLD}Total messages:{cls.RESET} {len(messages)}")

        for i, msg in enumerate(messages, start=1):
            role = msg.get("role")
            role_icon = "👤" if role == "user" else "🤖"
            role_color = cls.YELLOW if role == "user" else cls.MAGENTA

            print()
            print(f"  {role_color}{cls.BOLD}{role_icon} Message #{i} | role = {role}{cls.RESET}")

            content = msg.get("content")

            if isinstance(content, str):
                print(f"    {cls.GRAY}content type: str{cls.RESET}")
                print(f"    {truncate(content, 500)}")
                continue

            if isinstance(content, list):
                print(f"    {cls.GRAY}content type: list | blocks = {len(content)}{cls.RESET}")

                for j, block in enumerate(content, start=1):
                    print(f"    {cls.GRAY}├─ block #{j}{cls.RESET}")

                    if isinstance(block, dict):
                        cls._print_dict_block(block)
                    else:
                        cls._print_sdk_block(block)

                continue

            print(f"    {cls.GRAY}content type: {type(content).__name__}{cls.RESET}")
            print(f"    {truncate(str(content), 500)}")

    @classmethod
    def response_snapshot(cls, response, round_number: int) -> None:
        cls.section("🤖", f"CLAUDE RESPONSE ONLY — Round {round_number}", cls.MAGENTA)

        text_blocks = 0
        tool_blocks = 0

        print(f"  {cls.BOLD}content blocks:{cls.RESET} {len(response.content)}")

        for i, block in enumerate(response.content, start=1):
            block_type = getattr(block, "type", None)

            print()
            print(f"  {cls.GRAY}├─ response block #{i}{cls.RESET}")
            print(f"  {cls.GRAY}│  type = {block_type}{cls.RESET}")

            if block_type == "text":
                text_blocks += 1
                text = getattr(block, "text", "")
                print(f"  {cls.GRAY}│  text preview:{cls.RESET}")
                print(indent_text(truncate(text, 600), spaces=5))

            elif block_type == "tool_use":
                tool_blocks += 1
                print(f"  {cls.GRAY}│  tool_use id:{cls.RESET} {getattr(block, 'id', None)}")
                print(f"  {cls.GRAY}│  tool name:{cls.RESET} {cls.GREEN}{getattr(block, 'name', None)}{cls.RESET}")
                print(f"  {cls.GRAY}│  input:{cls.RESET} {getattr(block, 'input', None)}")

            else:
                print(f"  {cls.GRAY}│  raw:{cls.RESET} {truncate(str(block), 600)}")

        print()
        print(f"  {cls.BOLD}summary:{cls.RESET} text blocks = {text_blocks}, tool_use blocks = {tool_blocks}")

    @classmethod
    def _print_dict_block(cls, block: dict[str, Any]) -> None:
        block_type = block.get("type")
        print(f"    {cls.GRAY}│  python type = dict{cls.RESET}")
        print(f"    {cls.GRAY}│  type = {block_type}{cls.RESET}")

        if block_type == "tool_result":
            print(f"    {cls.GRAY}│  tool_use_id = {block.get('tool_use_id')}{cls.RESET}")
            result_content = str(block.get("content", ""))
            print(f"    {cls.GRAY}│  content preview:{cls.RESET}")
            print(indent_text(truncate(result_content, 700), spaces=7))
        else:
            print(f"    {cls.GRAY}│  raw dict:{cls.RESET} {truncate(str(block), 500)}")

    @classmethod
    def _print_sdk_block(cls, block: Any) -> None:
        block_type = getattr(block, "type", None)
        print(f"    {cls.GRAY}│  python type = {type(block).__name__}{cls.RESET}")
        print(f"    {cls.GRAY}│  type = {block_type}{cls.RESET}")

        if block_type == "text":
            text = getattr(block, "text", "")
            print(f"    {cls.GRAY}│  text preview:{cls.RESET}")
            print(indent_text(truncate(text, 700), spaces=7))

        elif block_type == "tool_use":
            print(f"    {cls.GRAY}│  tool_use id = {getattr(block, 'id', None)}{cls.RESET}")
            print(f"    {cls.GRAY}│  tool name = {cls.GREEN}{getattr(block, 'name', None)}{cls.RESET}")
            print(f"    {cls.GRAY}│  input = {getattr(block, 'input', None)}{cls.RESET}")

        else:
            print(f"    {cls.GRAY}│  raw block:{cls.RESET} {truncate(str(block), 500)}")


def truncate(text: str, max_chars: int = 500) -> str:
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def indent_text(text: str, spaces: int = 2) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line for line in str(text).splitlines())


# =============================================================================
# JSON trace helpers
# =============================================================================

def reset_messages_dir() -> None:
    """
    Clear old messages/ folder so each run starts fresh.

    messages/ is relative to this Python file.
    """
    if os.path.exists(MESSAGES_DIR):
        shutil.rmtree(MESSAGES_DIR)

    os.makedirs(MESSAGES_DIR, exist_ok=True)
    ConsoleView.success(f"Reset messages directory: {MESSAGES_DIR}")


def block_to_plain_json(block: Any) -> Any:
    if isinstance(block, dict):
        return block

    block_type = getattr(block, "type", None)

    if block_type == "text":
        return {
            "type": "text",
            "text": getattr(block, "text", ""),
        }

    if block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": getattr(block, "id", None),
            "name": getattr(block, "name", None),
            "input": getattr(block, "input", None),
        }

    return {
        "type": block_type or type(block).__name__,
        "raw": str(block),
    }


def messages_to_plain_json(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plain_messages = []

    for msg in messages:
        content = msg.get("content")

        if isinstance(content, list):
            plain_content = [block_to_plain_json(block) for block in content]
        else:
            plain_content = content

        plain_messages.append(
            {
                "role": msg.get("role"),
                "content": plain_content,
            }
        )

    return plain_messages


def save_messages_json(
    messages: list[dict[str, Any]],
    round_number: int,
    stage: str,
    query: str,
) -> str:
    """
    Save messages state as pure JSON.

    File order is intentionally encoded in filename:

    round_01_01_before_api_call.json
    round_01_02_after_assistant_response.json
    round_01_03_after_user_tool_results.json

    This makes normal alphabetical sorting match the real timeline.
    """
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


def stage_order(stage: str) -> int:
    """
    The number controls alphabetical file order inside messages/.

    01 = before API call
    02 = after assistant response
    03 = after user tool results
    """
    order_map = {
        "before_api_call": 1,
        "after_assistant_response": 2,
        "after_user_tool_results": 3,
    }

    return order_map.get(stage, 99)


def stage_to_filename(stage: str) -> str:
    stage = stage.lower()
    stage = re.sub(r"[^a-z0-9]+", "_", stage)
    stage = stage.strip("_")
    return stage


# =============================================================================
# Tools
# =============================================================================

def search_papers(topic: str, max_results: int = 5) -> List[str]:
    client = arxiv.Client()

    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = client.results(search)

    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids = []

    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)

        papers_info[paper_id] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2, ensure_ascii=False)

    ConsoleView.success(f"search_papers saved results to: {file_path}")
    ConsoleView.info("returned paper_ids", paper_ids, icon="📄")

    return paper_ids


def extract_info(paper_id: str) -> str:
    if not os.path.exists(PAPER_DIR):
        return f"Paper directory '{PAPER_DIR}' does not exist yet."

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)

        if not os.path.isdir(item_path):
            continue

        file_path = os.path.join(item_path, "papers_info.json")

        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
                papers_info = json.load(json_file)

            if paper_id in papers_info:
                return json.dumps(
                    papers_info[paper_id],
                    indent=2,
                    ensure_ascii=False,
                )

        except (FileNotFoundError, json.JSONDecodeError) as e:
            ConsoleView.warn(f"Error reading {file_path}: {str(e)}")
            continue

    return f"There's no saved information related to paper {paper_id}."


tools = [
    {
        "name": "search_papers",
        "description": (
            "Search for papers on arXiv based on a topic and store their information. "
            "Returns a list of paper IDs. If the user asks to search papers, call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to search for",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to retrieve",
                    "default": 5,
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "extract_info",
        "description": (
            "Search for information about a specific paper using a paper ID. "
            "Only call this after you have received actual paper IDs from search_papers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "The ID of the paper to look for",
                }
            },
            "required": ["paper_id"],
        },
    },
]

mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info,
}


def execute_tool(tool_name: str, tool_args: dict[str, Any]) -> str:
    ConsoleView.tool_call(tool_name, tool_args)

    if tool_name not in mapping_tool_function:
        return f"Unknown tool: {tool_name}"

    try:
        result = mapping_tool_function[tool_name](**tool_args)
    except Exception as e:
        return f"Tool execution error: {type(e).__name__}: {str(e)}"

    if result is None:
        result = "The operation completed but didn't return any results."
    elif isinstance(result, list):
        result = ", ".join(result)
    elif isinstance(result, dict):
        result = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        result = str(result)

    ConsoleView.tool_result(result)
    return result


# =============================================================================
# System prompt
# =============================================================================

SYSTEM_PROMPT = """
You are a research assistant.

Rules:
1. If the user asks to search papers, call search_papers first.
2. Do not call extract_info until you have received actual paper IDs from search_papers.
3. After search_papers returns paper IDs, you may call extract_info for those actual paper IDs.
4. If there are multiple tool calls in one assistant message, the user will return all tool results together.
"""


# =============================================================================
# Core agent loop
# =============================================================================

def process_query(query: str) -> None:
    """
    Core idea:

    messages = full conversation state
    response.content = Claude's current output only

    Loop:
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

        trace_messages(
            messages=messages,
            round_number=round_number,
            stage="before_api_call",
            query=query,
        )

        response = client.messages.create(
            max_tokens=2024,
            model="claude-sonnet-4-6",
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        ConsoleView.response_snapshot(response, round_number)

        messages.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        trace_messages(
            messages=messages,
            round_number=round_number,
            stage="after_assistant_response",
            query=query,
        )

        tool_results = collect_tool_results(response)

        ConsoleView.info("tool_results this round", len(tool_results), icon="🧺")

        if not tool_results:
            ConsoleView.success("No tool calls. Agent loop finished.")
            break

        messages.append(
            {
                "role": "user",
                "content": tool_results,
            }
        )

        trace_messages(
            messages=messages,
            round_number=round_number,
            stage="after_user_tool_results",
            query=query,
        )

        round_number += 1


def trace_messages(
    messages: list[dict[str, Any]],
    round_number: int,
    stage: str,
    query: str,
) -> None:
    ConsoleView.messages_snapshot(
        messages=messages,
        round_number=round_number,
        stage=stage,
    )

    save_messages_json(
        messages=messages,
        round_number=round_number,
        stage=stage,
        query=query,
    )


def collect_tool_results(response) -> list[dict[str, str]]:
    tool_results = []

    for content in response.content:
        if content.type == "text":
            ConsoleView.assistant_text(content.text)
            continue

        if content.type == "tool_use":
            result = execute_tool(content.name, content.input)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": result,
                }
            )

    return tool_results


def chat_loop() -> None:
    ConsoleView.title("Anthropic Tool Calling Debug Console")
    print("Type your queries or 'quit' to exit.")
    print(f"Messages JSON traces will be saved under: {MESSAGES_DIR}/")

    while True:
        try:
            query = input("\nQuery: ").strip()

            if query.lower() == "quit":
                break

            process_query(query)
            print()

        except Exception as e:
            ConsoleView.error(f"{type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    load_dotenv()
    client = anthropic.Anthropic()

    # Start fresh each run so the messages/ folder only contains current trace files.
    reset_messages_dir()

    chat_loop()

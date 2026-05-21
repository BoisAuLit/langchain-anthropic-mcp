from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json

console = Console()

def format_message_content(message):
    """Convert message content to displayable string"""
    parts = []
    tool_calls_processed = False
    
    # Handle main content
    if isinstance(message.content, str):
        parts.append(message.content)
    elif isinstance(message.content, list):
        # Handle complex content like tool calls (Anthropic format)
        for item in message.content:
            if item.get('type') == 'text':
                parts.append(item['text'])
            elif item.get('type') == 'tool_use':
                parts.append(f"\n🔧 Tool Call: {item['name']}")
                parts.append(f"   Args: {json.dumps(item['input'], indent=2)}")
                parts.append(f"   ID: {item.get('id', 'N/A')}")
                tool_calls_processed = True
    else:
        parts.append(str(message.content))
    
    # Handle tool calls attached to the message (OpenAI format) - only if not already processed
    if not tool_calls_processed and hasattr(message, 'tool_calls') and message.tool_calls:
        for tool_call in message.tool_calls:
            parts.append(f"\n🔧 Tool Call: {tool_call['name']}")
            parts.append(f"   Args: {json.dumps(tool_call['args'], indent=2)}")
            parts.append(f"   ID: {tool_call['id']}")
    
    return "\n".join(parts)


def format_messages(messages):
    """Format and display a list of messages with Rich formatting"""
    for m in messages:
        msg_type = m.__class__.__name__.replace('Message', '')
        content = format_message_content(m)

        if msg_type == 'Human':
            console.print(Panel(content, title="🧑 Human", border_style="blue"))
        elif msg_type == 'Ai':
            console.print(Panel(content, title="🤖 Assistant", border_style="green"))
        elif msg_type == 'Tool':
            console.print(Panel(content, title="🔧 Tool Output", border_style="yellow"))
        else:
            console.print(Panel(content, title=f"📝 {msg_type}", border_style="white"))


def format_message(messages):
    """Alias for format_messages for backward compatibility"""
    return format_messages(messages)



from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console(width=None)

def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "yellow"):
    formatted_text = Text(prompt_text)

    formatted_text.highlight_regex(r'<[^>]+>', style="bold yellow")
    formatted_text.highlight_regex(r'^###[^\n]+', style="bold cyan")
    formatted_text.highlight_regex(r'^##[^\n]+', style="bold magenta")

    panel = Panel(
        formatted_text,
        title=Text(title, style="bold green"),
        border_style=border_style,
        padding=(1, 2),
        expand=True,
        width=900
    )

    console.print(
        panel,
        width=None,
        overflow="fold",
        crop=False,
        soft_wrap=False,
    )

# def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
#     formatted_text = Text(prompt_text)

#     # XML tags
#     formatted_text.highlight_regex(r'<[^>]+>', style="bold yellow")

#     # Headers: more specific first
#     formatted_text.highlight_regex(r'^###[^\n]+', style="bold cyan")
#     formatted_text.highlight_regex(r'^##[^\n]+', style="bold magenta")

#     console.print(
#         Panel(
#             formatted_text,
#             title=Text(title, style="bold green"),
#             border_style=border_style,
#             padding=(1, 2),
#         )
#     )

# def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
#     """
#     Display a prompt with rich formatting and XML tag highlighting.
    
#     Args:
#         prompt_text: The prompt string to display
#         title: Title for the panel (default: "Prompt")
#         border_style: Border color style (default: "blue")
#     """
#     # Create a formatted display of the prompt
#     formatted_text = Text(prompt_text)
#     formatted_text.highlight_regex(r'<[^>]+>', style="bold blue")  # Highlight XML tags
#     formatted_text.highlight_regex(r'##[^#\n]+', style="bold magenta")  # Highlight headers
#     formatted_text.highlight_regex(r'###[^#\n]+', style="bold cyan")  # Highlight sub-headers

#     # Display in a panel for better presentation
#     console.print(Panel(
#         formatted_text,
#         title=f"[bold green]{title}[/bold green]",
#         border_style=border_style,
#         padding=(1, 2)
#     ))


# ============================================================
# 从 utils_bohao/utils.py 合并过来的函数(避免 sys.path 冲突)
# ============================================================
from rich.theme import Theme
from rich.json import JSON


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


# 全局 console(只初始化一次)
_custom_theme = Theme({
    "json.key": "bold bright_white",
    "json.str": "bold bright_yellow",
    "json.string": "bold bright_yellow",
    "json.number": "bright_cyan",
    "json.bool": "bright_magenta",
    "json.true": "bright_magenta",
    "json.false": "bright_magenta",
    "json.null": "bold bright_red",
})

_console = Console(theme=_custom_theme)


def debug(obj, title="🧠 Debug"):
    """
    Pretty print any object (Item, dict, state, etc.) in a readable JSON format.

    Args:
        obj: Any object (Item, dict, list, etc.)
        title: Optional title for the output panel
    """

    # 1. 优先用 .dict()
    if hasattr(obj, "dict"):
        try:
            data = obj.dict()
        except Exception:
            data = str(obj)
    # 2. 如果已经是 dict / list
    elif isinstance(obj, (dict, list)):
        data = obj
    # 3. fallback
    else:
        data = str(obj)

    _console.print(
        Panel(
            JSON.from_data(data),
            title=title,
            border_style="cyan",
        )
    )


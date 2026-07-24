import json
from typing import Any


def truncate(text: str, max_chars: int = 500) -> str:
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def indent_text(text: str, spaces: int = 2) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line for line in str(text).splitlines())


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
    def response_snapshot(cls, response: Any, round_number: int) -> None:
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

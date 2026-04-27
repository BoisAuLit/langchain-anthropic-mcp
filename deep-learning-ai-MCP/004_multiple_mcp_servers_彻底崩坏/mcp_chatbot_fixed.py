from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict, Any
from contextlib import AsyncExitStack
from datetime import datetime
import json
import os
import asyncio

load_dotenv()


class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCP_ChatBot:
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()

        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

        # Safety limits
        self.max_agent_turns = 8
        self.max_total_tool_calls = 16
        self.max_same_invalid_tool_calls = 2

        # Debug log directory: relative to this Python file
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.debug_dir = os.path.join(self.base_dir, "debug_logs")

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            await session.initialize()
            self.sessions.append(session)

            response = await session.list_tools()
            tools = response.tools

            print(f"\nConnected to {server_name}: {[t.name for t in tools]}")

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )

        except Exception as e:
            print(f"Failed to connect to {server_name}: {type(e).__name__}: {e}")

    async def connect_to_servers(self) -> None:
        """Connect to all configured MCP servers."""
        config_path = os.path.join(self.base_dir, "server_config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for name, config in data.get("mcpServers", {}).items():
            await self.connect_to_server(name, config)

    # -------------------------------------------------------------------------
    # Core agent loop
    # -------------------------------------------------------------------------

    async def process_query(self, query: str) -> None:
        """
        Diagnostic MCP + Anthropic agent loop.

        This version is designed for debugging:
        - Saves every Claude response
        - Saves every messages state
        - Saves every tool call
        - Validates write_file arguments
        - Stops repeated invalid write_file calls
        """
        self.reset_debug_dir()

        messages = [
            {
                "role": "user",
                "content": query,
            }
        ]

        agent_turn = 0
        total_tool_calls = 0
        invalid_tool_call_counts: Dict[str, int] = {}

        self.save_json(
            filename="000_initial_messages.json",
            data={
                "query": query,
                "messages": self.messages_to_json(messages),
            },
        )

        while True:
            agent_turn += 1

            if agent_turn > self.max_agent_turns:
                print(f"\n🛑 Stopped: reached max_agent_turns={self.max_agent_turns}.")
                self.save_json(
                    filename=f"turn_{agent_turn:02d}_STOP_max_agent_turns.json",
                    data={
                        "reason": "max_agent_turns reached",
                        "max_agent_turns": self.max_agent_turns,
                        "messages": self.messages_to_json(messages),
                    },
                )
                break

            print("\n" + "=" * 90)
            print(f"🔁 AGENT TURN {agent_turn}")
            print(f"messages length before API call = {len(messages)}")
            print("=" * 90)

            self.save_json(
                filename=f"turn_{agent_turn:02d}_01_before_api_messages.json",
                data={
                    "turn": agent_turn,
                    "stage": "before_api_call",
                    "messages": self.messages_to_json(messages),
                },
            )

            response = self.anthropic.messages.create(
                max_tokens=2024,
                model="claude-sonnet-4-6",
                system=self.system_prompt(),
                tools=self.available_tools,
                messages=messages,
            )

            response_json = self.response_to_json(response)

            self.save_json(
                filename=f"turn_{agent_turn:02d}_02_claude_response.json",
                data={
                    "turn": agent_turn,
                    "response_content": response_json,
                },
            )

            print(f"Claude response blocks = {len(response.content)}")

            for i, block in enumerate(response.content, start=1):
                block_type = getattr(block, "type", None)
                if block_type == "text":
                    print(f"  block #{i}: text")
                elif block_type == "tool_use":
                    print(
                        f"  block #{i}: tool_use | "
                        f"name={block.name} | id={block.id} | input={block.input}"
                    )
                else:
                    print(f"  block #{i}: {block_type}")

            # IMPORTANT:
            # Append Claude's entire response as ONE assistant message.
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                }
            )

            self.save_json(
                filename=f"turn_{agent_turn:02d}_03_after_assistant_messages.json",
                data={
                    "turn": agent_turn,
                    "stage": "after_assistant_response",
                    "messages": self.messages_to_json(messages),
                },
            )

            tool_results = []

            for content in response.content:
                if content.type == "text":
                    print("\n💬 Assistant text:")
                    print(content.text)
                    continue

                if content.type != "tool_use":
                    continue

                total_tool_calls += 1

                tool_name = content.name
                tool_args = content.input
                tool_id = content.id

                print(
                    f"\n🛠️ Tool call #{total_tool_calls}: "
                    f"{tool_name} with args {tool_args}"
                )

                self.save_json(
                    filename=(
                        f"turn_{agent_turn:02d}_tool_{total_tool_calls:02d}_"
                        f"request_{tool_name}.json"
                    ),
                    data={
                        "turn": agent_turn,
                        "tool_call_number": total_tool_calls,
                        "tool_use_id": tool_id,
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                    },
                )

                if total_tool_calls > self.max_total_tool_calls:
                    result_text = (
                        f"Stopped: reached max_total_tool_calls="
                        f"{self.max_total_tool_calls}. "
                        "The agent is likely stuck in a retry loop."
                    )
                    print(f"🛑 {result_text}")

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_text,
                        }
                    )
                    continue

                validation_error = self.validate_tool_call(tool_name, tool_args)

                if validation_error:
                    key = f"{tool_name}:{validation_error}"
                    invalid_tool_call_counts[key] = (
                        invalid_tool_call_counts.get(key, 0) + 1
                    )

                    result_text = (
                        f"Tool call rejected by client-side validation.\n"
                        f"Tool: {tool_name}\n"
                        f"Reason: {validation_error}\n"
                        f"Invalid attempt count for this error: "
                        f"{invalid_tool_call_counts[key]}\n\n"
                        "Do not retry the same invalid call. "
                        "Fix the arguments before calling the tool again."
                    )

                    print(f"🚫 Invalid tool call: {validation_error}")
                    print(f"invalid attempt count = {invalid_tool_call_counts[key]}")

                    self.save_json(
                        filename=(
                            f"turn_{agent_turn:02d}_tool_{total_tool_calls:02d}_"
                            f"REJECTED_{tool_name}.json"
                        ),
                        data={
                            "turn": agent_turn,
                            "tool_call_number": total_tool_calls,
                            "tool_use_id": tool_id,
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "validation_error": validation_error,
                            "invalid_attempt_count": invalid_tool_call_counts[key],
                        },
                    )

                    if (
                        invalid_tool_call_counts[key]
                        >= self.max_same_invalid_tool_calls
                    ):
                        result_text += (
                            "\n\nHard stop instruction: This exact invalid tool call "
                            "has happened too many times. Stop using this tool for this "
                            "task and explain the failure to the user."
                        )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_text,
                        }
                    )
                    continue

                session = self.tool_to_session.get(tool_name)

                if session is None:
                    result_text = f"Error: no MCP session found for tool {tool_name}"
                    print(f"❌ {result_text}")

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_text,
                        }
                    )
                    continue

                try:
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    result_text = self.mcp_result_to_text(result.content)

                    print("✅ Tool call completed")
                    print(f"result preview: {result_text[:500]}")

                except Exception as e:
                    result_text = (
                        f"Tool execution failed.\n"
                        f"Tool: {tool_name}\n"
                        f"Error type: {type(e).__name__}\n"
                        f"Error message: {str(e)}\n\n"
                        "Do not blindly retry the exact same tool call. "
                        "If arguments are missing or invalid, fix them once. "
                        "If it fails again, stop and explain."
                    )

                    print(f"❌ Tool failed: {type(e).__name__}: {e}")

                self.save_json(
                    filename=(
                        f"turn_{agent_turn:02d}_tool_{total_tool_calls:02d}_"
                        f"result_{tool_name}.json"
                    ),
                    data={
                        "turn": agent_turn,
                        "tool_call_number": total_tool_calls,
                        "tool_use_id": tool_id,
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "tool_result_preview": result_text[:3000],
                    },
                )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_text,
                    }
                )

            if not tool_results:
                print("\n✅ No tool calls requested. Agent loop finished.")
                self.save_json(
                    filename=f"turn_{agent_turn:02d}_04_final_messages.json",
                    data={
                        "turn": agent_turn,
                        "stage": "final_no_tool_results",
                        "messages": self.messages_to_json(messages),
                    },
                )
                break

            # CRITICAL:
            # Return all tool results from this Claude response together.
            messages.append(
                {
                    "role": "user",
                    "content": tool_results,
                }
            )

            self.save_json(
                filename=f"turn_{agent_turn:02d}_04_after_tool_results_messages.json",
                data={
                    "turn": agent_turn,
                    "stage": "after_user_tool_results",
                    "tool_results_count": len(tool_results),
                    "messages": self.messages_to_json(messages),
                },
            )

    # -------------------------------------------------------------------------
    # Tool validation
    # -------------------------------------------------------------------------

    def validate_tool_call(
        self, tool_name: str, tool_args: dict[str, Any]
    ) -> str | None:
        """
        Client-side guardrails.

        This is where we prevent obviously invalid tool calls from reaching MCP.
        """
        if not isinstance(tool_args, dict):
            return "tool_args must be a dictionary"

        if tool_name == "write_file":
            if "path" not in tool_args or not tool_args.get("path"):
                return "write_file requires a non-empty 'path' argument"

            if "content" not in tool_args:
                return "write_file requires a 'content' argument"

            if not isinstance(tool_args.get("content"), str):
                return "write_file 'content' must be a string"

            if tool_args.get("content") == "":
                return "write_file 'content' cannot be empty"

        if tool_name == "edit_file":
            if "path" not in tool_args or not tool_args.get("path"):
                return "edit_file requires a non-empty 'path' argument"

            # Different filesystem MCP versions may use edits/dryRun/etc.
            # We do not over-validate edit_file here, but we log all args.

        return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def system_prompt(self) -> str:
        return """
You are an MCP tool-using assistant.

Important tool-use rules:
1. If you use write_file, you MUST provide both:
   - path
   - content
2. NEVER call write_file with only path.
3. If file content is long, create a shorter version instead of retrying empty write_file calls.
4. If a tool call fails twice, stop retrying and explain the failure.
5. When multiple tool_use blocks are returned in one response, the client will return all tool_results together.
"""

    def mcp_result_to_text(self, content_blocks: Any) -> str:
        if content_blocks is None:
            return ""

        if isinstance(content_blocks, str):
            return content_blocks

        if isinstance(content_blocks, list):
            parts = []

            for block in content_blocks:
                text = getattr(block, "text", None)
                if text is not None:
                    parts.append(text)
                    continue

                if isinstance(block, dict):
                    if "text" in block:
                        parts.append(str(block["text"]))
                    else:
                        parts.append(json.dumps(block, ensure_ascii=False))
                    continue

                parts.append(str(block))

            return "\n".join(parts)

        return str(content_blocks)

    def response_to_json(self, response) -> list[dict[str, Any]]:
        blocks = []

        for block in response.content:
            block_type = getattr(block, "type", None)

            if block_type == "text":
                blocks.append(
                    {
                        "type": "text",
                        "text": getattr(block, "text", ""),
                    }
                )

            elif block_type == "tool_use":
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": getattr(block, "id", None),
                        "name": getattr(block, "name", None),
                        "input": getattr(block, "input", None),
                    }
                )

            else:
                blocks.append(
                    {
                        "type": block_type or type(block).__name__,
                        "raw": str(block),
                    }
                )

        return blocks

    def messages_to_json(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        plain_messages = []

        for msg in messages:
            content = msg.get("content")

            if isinstance(content, list):
                plain_content = []

                for block in content:
                    if isinstance(block, dict):
                        plain_content.append(block)
                    else:
                        block_type = getattr(block, "type", None)

                        if block_type == "text":
                            plain_content.append(
                                {
                                    "type": "text",
                                    "text": getattr(block, "text", ""),
                                }
                            )
                        elif block_type == "tool_use":
                            plain_content.append(
                                {
                                    "type": "tool_use",
                                    "id": getattr(block, "id", None),
                                    "name": getattr(block, "name", None),
                                    "input": getattr(block, "input", None),
                                }
                            )
                        else:
                            plain_content.append(
                                {
                                    "type": block_type or type(block).__name__,
                                    "raw": str(block),
                                }
                            )

                plain_messages.append(
                    {
                        "role": msg.get("role"),
                        "content": plain_content,
                    }
                )
            else:
                plain_messages.append(
                    {
                        "role": msg.get("role"),
                        "content": content,
                    }
                )

        return plain_messages

    def reset_debug_dir(self) -> None:
        os.makedirs(self.debug_dir, exist_ok=True)

        for name in os.listdir(self.debug_dir):
            path = os.path.join(self.debug_dir, name)
            if os.path.isfile(path):
                os.remove(path)

        print(f"🧾 Debug logs will be saved to: {self.debug_dir}")

    def save_json(self, filename: str, data: Any) -> None:
        os.makedirs(self.debug_dir, exist_ok=True)
        path = os.path.join(self.debug_dir, filename)

        payload = {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "data": data,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # Chat loop
    # -------------------------------------------------------------------------

    async def chat_loop(self) -> None:
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print(f"Safety: max_agent_turns={self.max_agent_turns}")
        print(f"Safety: max_total_tool_calls={self.max_total_tool_calls}")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {type(e).__name__}: {str(e)}")

    async def cleanup(self) -> None:
        await self.exit_stack.aclose()


async def main() -> None:
    bot = MCP_ChatBot()

    try:
        await bot.connect_to_servers()
        await bot.chat_loop()
    finally:
        await bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

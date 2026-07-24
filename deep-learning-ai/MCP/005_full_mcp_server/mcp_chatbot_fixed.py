from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from typing import Any
import json
import os
import asyncio
import nest_asyncio

nest_asyncio.apply()
load_dotenv()


class MCP_ChatBot:
    def __init__(self):
        # ! handling of dynamic number of "async with"
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

        self.available_tools = []
        self.available_prompts = []
        self.sessions = {}

        self.max_agent_turns = 8
        self.max_total_tool_calls = 16
        self.max_same_invalid_tool_calls = 2

    async def connect_to_server(self, server_name, server_config):
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

            try:
                # ! Show the tools of the mcp server and add the globally
                response = await session.list_tools()
                for tool in response.tools:
                    self.sessions[tool.name] = session
                    self.available_tools.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                    )

                print(
                    f"\nConnected to {server_name} with tools:",
                    [tool.name for tool in response.tools],
                )

                # ! Show the prompts of the mcp server and add them globally
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append(
                            {
                                "name": prompt.name,
                                "description": prompt.description,
                                "arguments": prompt.arguments,
                            }
                        )

                # ! Show the tools of the mcp server and add them globally
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        self.sessions[str(resource.uri)] = session

            except Exception as e:
                print(f"Error listing capabilities from {server_name}: {type(e).__name__}: {e}")

        except Exception as e:
            print(f"Error connecting to {server_name}: {type(e).__name__}: {e}")

    async def connect_to_servers(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "server_config.json")

            with open(config_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})

            for server_name, server_config in servers.items():
                # Resolve any relative paths in args to absolute paths
                if "args" in server_config:
                    server_config["args"] = [
                        os.path.join(base_dir, arg) if arg.startswith("./") or arg.startswith("../") else arg
                        for arg in server_config["args"]
                    ]

                await self.connect_to_server(server_name, server_config)

        except Exception as e:
            print(f"Error loading server config: {type(e).__name__}: {e}")
            raise

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]

        agent_turn = 0
        total_tool_calls = 0
        invalid_tool_call_counts = {}

        while True:
            agent_turn += 1

            if agent_turn > self.max_agent_turns:
                print(
                    f"\nStopped: reached max_agent_turns={self.max_agent_turns}. "
                    "This prevents infinite tool retry loops."
                )
                break

            response = self.anthropic.messages.create(
                max_tokens=2024,
                model="claude-sonnet-4-6",
                system=self.system_prompt(),
                tools=self.available_tools,
                messages=messages,
            )

            # Append Claude's full response as ONE assistant message.
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []

            for content in response.content:
                if content.type == "text":
                    print(content.text)
                    continue

                if content.type != "tool_use":
                    continue

                total_tool_calls += 1

                tool_name = content.name
                tool_args = content.input
                tool_id = content.id

                print(
                    f"Calling tool {tool_name} with args {tool_args} "
                    f"(tool call #{total_tool_calls})"
                )

                if total_tool_calls > self.max_total_tool_calls:
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": (
                                f"Stopped: reached max_total_tool_calls="
                                f"{self.max_total_tool_calls}. "
                                "The agent appears to be retrying tools too many times."
                            ),
                        }
                    )
                    continue

                validation_error = self.validate_tool_call(tool_name, tool_args)

                if validation_error:
                    key = f"{tool_name}:{validation_error}"
                    invalid_tool_call_counts[key] = invalid_tool_call_counts.get(key, 0) + 1

                    result_text = (
                        "Tool call rejected by client-side validation.\n"
                        f"Tool: {tool_name}\n"
                        f"Reason: {validation_error}\n"
                        f"Invalid attempt count: {invalid_tool_call_counts[key]}\n\n"
                        "Fix the arguments before calling this tool again. "
                        "Do not retry the exact same invalid call."
                    )

                    if invalid_tool_call_counts[key] >= self.max_same_invalid_tool_calls:
                        result_text += (
                            "\n\nHard stop instruction: This exact invalid tool call "
                            "has happened too many times. Stop using this tool for "
                            "this task and explain the failure to the user."
                        )

                    print(f"Rejected invalid tool call: {validation_error}")

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_text,
                        }
                    )
                    continue

                session = self.sessions.get(tool_name)

                if not session:
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error: tool '{tool_name}' not found.",
                        }
                    )
                    continue

                try:
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    result_text = self.mcp_result_to_text(result.content)

                except Exception as e:
                    result_text = (
                        f"Tool execution failed.\n"
                        f"Tool: {tool_name}\n"
                        f"Error type: {type(e).__name__}\n"
                        f"Error message: {str(e)}\n\n"
                        "Do not blindly retry the same tool call. "
                        "If arguments are invalid, fix them once. "
                        "If it fails again, stop and explain."
                    )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_text,
                    }
                )

            if not tool_results:
                break

            # Return all tool results together in ONE user message.
            messages.append({"role": "user", "content": tool_results})

    def validate_tool_call(self, tool_name: str, tool_args: dict[str, Any]) -> str | None:
        if not isinstance(tool_args, dict):
            return "tool arguments must be a dictionary"

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

            if "edits" not in tool_args:
                return "edit_file requires an 'edits' argument"

            if not isinstance(tool_args.get("edits"), list):
                return "edit_file 'edits' must be a list"

            if len(tool_args.get("edits")) == 0:
                return "edit_file 'edits' cannot be empty"

        return None

    def system_prompt(self) -> str:
        return '''
You are an MCP tool-using assistant.

Important tool-use rules:
1. If you use write_file, you MUST provide both path and content.
2. NEVER call write_file with only path.
3. If you use edit_file, you MUST provide both path and edits.
4. NEVER call edit_file with only path.
5. If file content is long, make it shorter instead of retrying empty writes.
6. If a tool call fails twice, stop retrying and explain the failure.
7. When multiple tool_use blocks are returned in one response, the client will return all tool_results together.
'''

    def mcp_result_to_text(self, content_blocks):
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

    async def get_resource(self, resource_uri):
        session = self.sessions.get(resource_uri)

        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break

        if not session:
            print(f"Resource '{resource_uri}' not found.")
            return

        try:
            result = await session.read_resource(uri=resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("Content:")
                print(result.contents[0].text)
            else:
                print("No content available.")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

    async def list_prompts(self):
        if not self.available_prompts:
            print("No prompts available.")
            return

        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt["arguments"]:
                print("  Arguments:")
                for arg in prompt["arguments"]:
                    arg_name = arg.name if hasattr(arg, "name") else arg.get("name", "")
                    print(f"    - {arg_name}")

    async def execute_prompt(self, prompt_name, args):
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return

        try:
            result = await session.get_prompt(prompt_name, arguments=args)

            if result and result.messages:
                prompt_content = result.messages[0].content

                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, "text"):
                    text = prompt_content.text
                else:
                    text = " ".join(
                        item.text if hasattr(item, "text") else str(item)
                        for item in prompt_content
                    )

                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

    async def chat_loop(self):
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Use @folders to see available topics")
        print("Use @<topic> to search papers in that topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <name> <arg1=value1> to execute a prompt")
        print(
            f"Safety limits: max_agent_turns={self.max_agent_turns}, "
            f"max_total_tool_calls={self.max_total_tool_calls}"
        )

        while True:
            try:
                query = input("\nQuery: ").strip()
                if not query:
                    continue

                if query.lower() == "quit":
                    break

                if query.startswith("@"):
                    topic = query[1:]

                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"

                    await self.get_resource(resource_uri)
                    continue

                if query.startswith("/"):
                    parts = query.split()
                    command = parts[0].lower()

                    if command == "/prompts":
                        await self.list_prompts()

                    elif command == "/prompt":
                        if len(parts) < 2:
                            print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                            continue

                        prompt_name = parts[1]
                        args = {}

                        for arg in parts[2:]:
                            if "=" in arg:
                                key, value = arg.split("=", 1)
                                args[key] = value

                        await self.execute_prompt(prompt_name, args)

                    else:
                        print(f"Unknown command: {command}")

                    continue

                await self.process_query(query)

            except Exception as e:
                print(f"\nError: {type(e).__name__}: {e}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()

    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

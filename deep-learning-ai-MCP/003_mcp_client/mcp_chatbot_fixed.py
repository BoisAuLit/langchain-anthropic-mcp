from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Any
import asyncio
import os
import nest_asyncio

nest_asyncio.apply()
load_dotenv()


class MCP_ChatBot:
    def __init__(self):
        self.session: ClientSession | None = None
        self.anthropic = Anthropic()
        self.available_tools: List[dict[str, Any]] = []

    async def process_query(self, query: str) -> None:
        """
        Correct MCP + Anthropic agent loop.

        Key rule:
        If Claude returns multiple tool_use blocks in one response,
        execute ALL of them first, then send ALL tool_result blocks back
        together in ONE user message.
        """
        messages = [{"role": "user", "content": query}]

        while True:
            response = self.anthropic.messages.create(
                max_tokens=2024,
                model="claude-sonnet-4-6",
                tools=self.available_tools,
                messages=messages,
            )

            # Add Claude's full response to conversation history.
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                }
            )

            tool_results = []

            for content in response.content:
                if content.type == "text":
                    print(content.text)

                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input
                    tool_id = content.id

                    print(f"Calling tool {tool_name} with args {tool_args}")

                    result = await self.session.call_tool(
                        tool_name,
                        arguments=tool_args,
                    )

                    result_text = self._mcp_result_to_text(result.content)

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_text,
                        }
                    )

            # If Claude did not request tools, this is the final answer.
            if not tool_results:
                break

            # IMPORTANT:
            # Return all tool_results from this Claude response together.
            messages.append(
                {
                    "role": "user",
                    "content": tool_results,
                }
            )

    def _mcp_result_to_text(self, content_blocks: Any) -> str:
        """
        Convert MCP tool result content into a plain string.

        MCP result.content is often:
        [
            TextContent(type='text', text='...')
        ]
        """
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
                        parts.append(str(block))
                    continue

                parts.append(str(block))

            return "\n".join(parts)

        return str(content_blocks)

    async def chat_loop(self) -> None:
        """Run an interactive chat loop."""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {type(e).__name__}: {str(e)}")

    async def connect_to_server_and_run(self) -> None:
        """
        Connect to MCP server over stdio, list tools, then start chat loop.
        """
        server_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "research_server.py",
        )

        server_params = StdioServerParameters(
            command="uv",
            args=["run", server_script],
            env=None,
        )

        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            self.session = session

            await session.initialize()

            response = await session.list_tools()
            tools = response.tools

            print("\nConnected to server with tools:", [tool.name for tool in tools])

            self.available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools
            ]

            await self.chat_loop()


async def main() -> None:
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())

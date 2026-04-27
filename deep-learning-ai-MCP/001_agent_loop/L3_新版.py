import anthropic
from dotenv import load_dotenv

from agent import chat_loop
from tracer import reset_messages_dir

if __name__ == "__main__":
    load_dotenv()
    client = anthropic.Anthropic()

    # Start fresh each run so messages/ only contains the current trace.
    reset_messages_dir()

    chat_loop(client)

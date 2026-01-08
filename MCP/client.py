#openrouiter key  = "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"
import asyncio
from temprl_mcp_client.client import initialize_mcp, run_interaction

async def main():
    # Initialize MCP with a new chat memory
    mcp_manager = await initialize_mcp(config_path="mcp_config.json")

    available_servers = mcp_manager.get_available_servers()
    print(f"Available servers: {available_servers}")  # e.g., ['zoom', 'gmail', 'business']

    # Get the chat ID for later use
    chat_id = mcp_manager.chat_memory.chat_id
    print(f"New chat created with ID: {chat_id}")

    # Run interactions
    print("\nStarting chat session. Type 'quit' or 'exit' to end.")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if not user_input:
                continue

            response = await run_interaction(
                user_query=user_input,
                mcp_manager=mcp_manager,
                server_names=["weather","desktop-commander"]
            )
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
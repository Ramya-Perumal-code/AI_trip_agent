import asyncio
from temprl_mcp_client.client import initialize_mcp

async def main():
    try:
        print("Initializing MCP...")
        mcp_manager = await initialize_mcp(config_path="mcp_config.json")
        print("MCP Initialized.")
        
        servers = mcp_manager.get_available_servers()
        print(f"Connected Servers: {servers}")
        
        if "weather" in servers:
            print("Checking tools for 'weather' server...")
            # Access the server client directly if possible, or list tools via manager
            # The mcp_manager likely has a way to list tools. 
            # If not, we can infer from the internal state.
            # Looking at client.py, it uses mcp_manager.
            
            # Assuming mcp_manager has a .clients attribute or similar
            weather_client = mcp_manager.clients.get("weather")
            if weather_client:
                tools_result = await weather_client.session.list_tools()
                print(f"Tools available from weather server: {tools_result.tools}")
            else:
                print("Could not get weather client from manager.")
        else:
            print("Weather server not found in connected servers.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

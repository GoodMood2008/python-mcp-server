import os

os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)


import aiohttp
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

class CmdMcpClient:
    def __init__(self, remote_ip: str, port: int = 9202):
        self.server_url = f"http://{remote_ip}:{port}/sse"

    async def execute_command(self, command: str) -> str:       
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'execute_command',  arguments = {'command':command})
                return response
        
if __name__ == "__main__":
    client = CmdMcpClient('127.0.0.1')
    result = asyncio.run(client.execute_command(command='pwd'))
    print(result)

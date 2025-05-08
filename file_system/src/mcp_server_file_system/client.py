import os

os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)


import aiohttp
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

class FileSystemMcpClient:
    def __init__(self, remote_ip: str, port: int = 9200):
        self.server_url = f"http://{remote_ip}:{port}/sse"

    # 读文件
    async def read_file(self, path: str) -> str:  
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'read_file',  arguments = {'path':path})
                return response
    
    # 写文件
    async def write_file(self, path: str, content: str) -> str:  
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'write_file',  arguments = {'path':path, 'content':content})
                return response
                
    # 创建目录
    async def create_directory(self, path: str) -> str:  
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'create_directory',  arguments = {'path':path})
                return response
                
    # 创建目录
    async def list_directory(self, path: str) -> str:  
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'list_directory',  arguments = {'path':path})
                return response
        
if __name__ == "__main__":
    client = FileSystemMcpClient('127.0.0.1')
    #result = asyncio.run(client.execute_command(comand='pwd'))
    #print(result)
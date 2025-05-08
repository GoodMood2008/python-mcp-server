import os

os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)


import aiohttp
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

class GitMcpClient:
    def __init__(self, remote_ip: str, port: int = 9201):
        self.server_url = f"http://{remote_ip}:{port}/sse"

    async def git_pull(self, repo_path: str) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'git_pull',  arguments = {'repo_path': repo_path, 'remote_name':'origin', 'branch_name':'master'})
                return response
                
    async def git_push(self, repo_path: str) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'git_push',  arguments = {'repo_path': repo_path, 'remote_name':'origin', 'branch_name':'master'})
                return response
                
    async def git_add(self, repo_path: str, files: list[str]) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'git_add',  arguments = {'repo_path': repo_path, 'files':files})
                return response
                
    async def git_status(self, repo_path: str) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'git_status', arguments = {'repo_path': repo_path})
                return response
                
    async def git_commit(self, repo_path: str, message: str) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'git_commit',  arguments = {'repo_path': repo_path, 'message': message})
                return response
        
if __name__ == "__main__":
    client = GitMcpClient('127.0.0.1')
    result = asyncio.run(client.git_status(repo_path='xx'))
    print(result)

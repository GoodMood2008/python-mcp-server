import os

os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)


import aiohttp
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

class KnowledgeServiceClient:
    def __init__(self, remote_ip: str, port: int = 9203):
        self.server_url = f"http://{remote_ip}:{port}/sse"

    async def get_interface_define(self, inf_type, func_name, is_need_recursive=False) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'get_ops_inf',  arguments = {'inf_type': inf_type, 'func_name': func_name, 'is_need_recursive':is_need_recursive})
                result = ''
                if response.content:
                    result = response.content[0].text
                return not response.isError, result
                
    async def get_anwser_by_question(self, question, account, token, kbaseName, kbaseid, tag_names = []) -> str:
        async with sse_client(self.server_url) as streams:
            async with ClientSession(*streams) as session:
                # Test initialization
                await session.initialize()
                response = await session.call_tool(name = 'get_ops_qa',  arguments = {'question': question, 'account': account, 'token': token, 'kbaseName': kbaseName, 'kbaseid': kbaseid, 'tag_names': tag_names})
                result = ''
                if response.content:
                    result = response.content[0].text
                return not response.isError, result
                
if __name__ == "__main__":
    client = KnowledgeServiceClient('127.0.0.1')
    #result = asyncio.run(client.get_interface_define('YAML', 'getOspfByFitler'))
    result = asyncio.run(client.get_anwser_by_question('北向接口领域_BNC全量资产AI方案', '10041713', '06404bdef391f9e36579f994cc07d82c', '北向接口领域设计Agent模版私域知识库', '2df598d63032431ca93a172183be6d53'))
    print(result)

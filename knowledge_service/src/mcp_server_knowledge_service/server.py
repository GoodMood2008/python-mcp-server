import os
os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)


from pathlib import Path
from typing import Sequence
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    ClientCapabilities,
    TextContent,
    Tool,
    ListRootsResult,
    RootsCapability,
)
from enum import Enum
from pydantic import BaseModel
from pydantic import ValidationError
from typing import List
from knowledge_service_api import get_ops_inf
from knowledge_base_api import query_kbase_and_return_one

import logging


class OpsInfFetchParas(BaseModel):
    inf_type : str
    func_name : str
    is_need_recursive: bool = False

class KnowledgeBaseParas(BaseModel):
    question: str
    account: str
    token: str 
    kbaseName: str 
    kbaseid: str 
    tag_names: List[str] = []



class KonwledgeServiceTools(str, Enum):
    OPS_INF = "get_ops_inf"
    OPS_QA = "get_ops_qa"


class KownledgeService:
    # return
    # True, method
    # False, error
    def get_interface_define(inf_type, func_name, is_need_recursive=False, logger = None) -> str:
        return get_ops_inf(inf_type=inf_type, func_name=func_name, logger=logger, is_need_recursive=is_need_recursive)

    def get_anwser_by_question(question, account, token, kbaseName, kbaseid, tag_names = [], logger = None) -> str:
        return query_kbase_and_return_one(question=question, account=account, token=token, kbaseName=kbaseName, kbaseid=kbaseid, tag_names=tag_names, logger = logger)
    
def set_logger(log_name, file):
        logger = logging.getLogger(log_name)
        logger.propagate = False
        logger.setLevel(logging.DEBUG) 
        if not logger.handlers:
            #设置将日志输出到文件中，并且定义文件内容
            fileinfo = logging.FileHandler(file)
            fileinfo.setLevel(logging.DEBUG) 
            #设置将日志输出到控制台
            controlshow = logging.StreamHandler()
            controlshow.setLevel(logging.INFO)
            #设置日志的格式
            formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
            fileinfo.setFormatter(formatter)
            controlshow.setFormatter(formatter)
            logger.addHandler(fileinfo)
            logger.addHandler(controlshow)
        return logger


class Server:
    mcp: FastMCP = FastMCP("mcp-knowledge-service")
    logger = set_logger("./log", f'./log/knowledge-service.log')

    def __init__(self, port):
        Server.mcp.settings.port = port

    # run
    def run(self):
        self.mcp.run('sse')

    @mcp._mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name = KonwledgeServiceTools.OPS_INF,
                description = "Get method or data definiton with name from knowledge service",
                inputSchema = OpsInfFetchParas.model_json_schema(),
            ),
            Tool(
                name = KonwledgeServiceTools.OPS_QA,
                description = "Get answser with question from qa database",
                inputSchema = KonwledgeServiceTools.model_json_schema(),
            ),
        ]

    @mcp._mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        match name:
            case KonwledgeServiceTools.OPS_INF:
                try:
                    schema = OpsInfFetchParas.model_validate(arguments)  
                    statu, result = KownledgeService.get_interface_define(schema.inf_type, schema.func_name, schema.is_need_recursive, Server.logger)
                    if statu:
                        return [TextContent(
                            type="text",
                            text=result
                        )]
                    else:
                        error = f"Process error : {result}"
                        Server.logger.error(error)
                        raise ValueError(error)
                except ValidationError as e:
                    error = f"Invalid arguments for {name}: {e}"
                    Server.logger.error(error)
                    raise ValueError(error)
                    
            case KonwledgeServiceTools.OPS_QA:
                try:
                    schema = KnowledgeBaseParas.model_validate(arguments)  # Validate GitPull schema
                    statu, result = KownledgeService.get_anwser_by_question(schema.question, schema.account, schema.token, schema.kbaseName, schema.kbaseid, schema.tag_names, Server.logger)
                    if statu:
                        return [TextContent(
                            type="text",
                            text=result
                        )]
                    else:
                        error = f"Process error : {result}"
                        Server.logger.error(error)
                        raise ValueError(error)
                except ValidationError as e:
                    error = f"Invalid arguments for {name}: {e}"
                    Server.logger.error(error)
                    raise ValueError(error)
                except Exception as e:
                    error = f'error {e}'
                    Server.logger.error(error)
                    raise ValueError(error)
            case _:
                error = f"Unknown tool: {name}"
                Server.logger.error(error)
                raise ValueError(error)

# 运行服务器
def main(port: int = 9203):
    server = Server(port)
    server.run()

if __name__ == "__main__":
    import argparse
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9203)
    args = parser.parse_args()

    # 调用主函数
    main(port=args.port)

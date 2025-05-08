import os
import subprocess
import logging
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
from typing import List
from enum import Enum
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
import mcp.types as types


# 环境设置（如清除代理设置）
os.environ.pop("http_proxy", None)
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)

# 工具定义
class ExecuteCommandArgs(BaseModel):
    command: str
    newSession: bool = False

class SSHConnectionArgs(BaseModel):
    host: str
    port: int = 22
    username: str
    password: str = None
    privateKey: str = None
    command: str
    newSession: bool = False

# 使用 paramiko 处理 SSH 连接
class SSHOperation:
    @staticmethod
    def execute_ssh_command(config: SSHConnectionArgs) -> str:
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())  # 自动接受未知主机的密钥
            if config.privateKey:
                client.load_system_host_keys()
                client.connect(config.host, port=config.port, username=config.username, key_filename=config.privateKey)
            else:
                client.connect(config.host, port=config.port, username=config.username, password=config.password)

            stdin, stdout, stderr = client.exec_command(config.command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            client.close()

            if error:
                return f"Error: {error}"
            return output
        except Exception as e:
            return f"SSH Connection Error: {str(e)}"


# MCP 服务器设置
class CommandExecutionServer:
    mcp: FastMCP = FastMCP("cmd-server")

    def __init__(self, port: int = 9202):
        self.mcp.settings.port = port

    def run(self):
        self.mcp.run('sse')

    @mcp._mcp_server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="execute_command",
                description="Execute a command on the local machine",
                inputSchema=ExecuteCommandArgs.model_json_schema(),
            ),
            types.Tool(
                name="execute_ssh_command",
                description="Execute a command on a remote server via SSH",
                inputSchema=SSHConnectionArgs.model_json_schema(),
            )
        ]


    @mcp._mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
        if name == "execute_command":
            parsed = ExecuteCommandArgs.model_validate(arguments)
            result = subprocess.run(parsed.command, shell=True, capture_output=True, text=True)
            return [types.TextContent(type="text", text=result.stdout or f"Error: {result.stderr}")]
        
        if name == "execute_ssh_command":
            parsed = SSHConnectionArgs.model_validate(arguments)
            result = SSHOperation.execute_ssh_command(parsed)
            return [types.TextContent(type="text", text=result)]

        raise ValueError(f"Unknown tool: {name}")


# 运行服务器
def main(port: int = 9202):
    server = CommandExecutionServer(port)
    server.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9202)
    args = parser.parse_args()
    main(port=args.port)

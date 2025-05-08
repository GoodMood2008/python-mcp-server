import os
os.environ.pop("http_proxy", None)  # 解决云桌面代理的问题，服务器或非外网代理可以不用
os.environ.pop("all_proxy", None)
os.environ.pop("https_proxy", None)
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
sys.path.insert(0, parent_dir)

import logging
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
import git
from pydantic import BaseModel
from pydantic import ValidationError

class GitStatus(BaseModel):
    repo_path: str

class GitPull(BaseModel):
    repo_path: str
    remote_name: str
    branch_name: str

class GitPush(BaseModel):
    repo_path: str
    remote_name: str
    branch_name: str

class GitDiffUnstaged(BaseModel):
    repo_path: str

class GitDiffStaged(BaseModel):
    repo_path: str

class GitDiff(BaseModel):
    repo_path: str
    target: str

class GitCommit(BaseModel):
    repo_path: str
    message: str

class GitAdd(BaseModel):
    repo_path: str
    files: list[str]

class GitReset(BaseModel):
    repo_path: str

class GitLog(BaseModel):
    repo_path: str
    max_count: int = 10

class GitCreateBranch(BaseModel):
    repo_path: str
    branch_name: str
    base_branch: str | None = None

class GitCheckout(BaseModel):
    repo_path: str
    branch_name: str

class GitShow(BaseModel):
    repo_path: str
    revision: str

class GitInit(BaseModel):
    repo_path: str

class GitTools(str, Enum):
    STATUS = "git_status"
    PULL = "git_pull"
    PUSH = "git_push"
    DIFF_UNSTAGED = "git_diff_unstaged"
    DIFF_STAGED = "git_diff_staged"
    DIFF = "git_diff"
    COMMIT = "git_commit"
    ADD = "git_add"
    RESET = "git_reset"
    LOG = "git_log"
    CREATE_BRANCH = "git_create_branch"
    CHECKOUT = "git_checkout"
    SHOW = "git_show"
    INIT = "git_init"

class GitOperation:
    def git_status(repo: git.Repo) -> str:
        return repo.git.status()
    
    def git_pull(repo: git.Repo, remote='origin', branch='master') -> str:
        # 检查当前分支
        current_branch = repo.active_branch.name

        # 如果当前分支不是目标分支，切换到目标分支
        if current_branch != branch:
            repo.git.checkout(branch)        
  
        # 如果当前分支没有设置上游分支，则设置上游分支
        if not current_branch in repo.git.branch('-r'):
            repo.git.push('--set-upstream', remote, branch)

        # 拉取远程仓库更新
        return repo.remotes.origin.pull(branch)

    def git_push(repo: git.Repo, remote='origin', branch='master') -> str:
        # 检查当前分支
        current_branch = repo.active_branch.name

        # 如果当前分支不是目标分支，切换到目标分支
        if current_branch != branch:
            repo.git.checkout(branch)        
  
        # 如果当前分支没有设置上游分支，则设置上游分支
        if not current_branch in repo.git.branch('-r'):
            repo.git.push('--set-upstream', remote, branch)

        # 拉取远程仓库更新
        return repo.remotes.origin.push(branch)
        

  
    def git_diff_unstaged(repo: git.Repo) -> str:
        return repo.git.diff()

    def git_diff_staged(repo: git.Repo) -> str:
        return repo.git.diff("--cached")

    def git_diff(repo: git.Repo, target: str) -> str:
        return repo.git.diff(target)

    def git_commit(repo: git.Repo, message: str) -> str:
        commit = repo.index.commit(message)
        return f"Changes committed successfully with hash {commit.hexsha}"

    def git_add(repo: git.Repo, files: list[str]) -> str:
        repo.index.add(files)
        return "Files staged successfully"

    def git_reset(repo: git.Repo) -> str:
        repo.index.reset()
        return "All staged changes reset"

    def git_log(repo: git.Repo, max_count: int = 10) -> list[str]:
        commits = list(repo.iter_commits(max_count=max_count))
        log = []
        for commit in commits:
            log.append(
                f"Commit: {commit.hexsha}\n"
                f"Author: {commit.author}\n"
                f"Date: {commit.authored_datetime}\n"
                f"Message: {commit.message}\n"
            )
        return log

    def git_create_branch(repo: git.Repo, branch_name: str, base_branch: str | None = None) -> str:
        if base_branch:
            base = repo.refs[base_branch]
        else:
            base = repo.active_branch

        repo.create_head(branch_name, base)
        return f"Created branch '{branch_name}' from '{base.name}'"

    def git_checkout(repo: git.Repo, branch_name: str) -> str:
        repo.git.checkout(branch_name)
        return f"Switched to branch '{branch_name}'"

    def git_init(repo_path: str) -> str:
        try:
            repo = git.Repo.init(path=repo_path, mkdir=True)
            return f"Initialized empty Git repository in {repo.git_dir}"
        except Exception as e:
            return f"Error initializing repository: {str(e)}"

    def git_show(repo: git.Repo, revision: str) -> str:
        commit = repo.commit(revision)
        output = [
            f"Commit: {commit.hexsha}\n"
            f"Author: {commit.author}\n"
            f"Date: {commit.authored_datetime}\n"
            f"Message: {commit.message}\n"
        ]
        if commit.parents:
            parent = commit.parents[0]
            diff = parent.diff(commit, create_patch=True)
        else:
            diff = commit.diff(git.NULL_TREE, create_patch=True)
        for d in diff:
            output.append(f"\n--- {d.a_path}\n+++ {d.b_path}\n")
            output.append(d.diff.decode('utf-8'))
        return "".join(output)

class Server:
    mcp: FastMCP = FastMCP("mcp-git")

    def __init__(self, port):
        Server.mcp.settings.port = port

    # run
    def run(self):
        self.mcp.run('sse')

    @mcp._mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=GitTools.STATUS,
                description="Shows the working tree status",
                inputSchema=GitStatus.model_json_schema(),
            ),
            Tool(
                name=GitTools.PULL,
                description="Pull changes from remote origin",
                inputSchema=GitPull.model_json_schema(),
            ),
            Tool(
                name=GitTools.PUSH,
                description="Push changes to remote origin",
                inputSchema=GitPush.model_json_schema(),
            ),            
            Tool(
                name=GitTools.DIFF_UNSTAGED,
                description="Shows changes in the working directory that are not yet staged",
                inputSchema=GitDiffUnstaged.model_json_schema(),
            ),
            Tool(
                name=GitTools.DIFF_STAGED,
                description="Shows changes that are staged for commit",
                inputSchema=GitDiffStaged.model_json_schema(),
            ),
            Tool(
                name=GitTools.DIFF,
                description="Shows differences between branches or commits",
                inputSchema=GitDiff.model_json_schema(),
            ),
            Tool(
                name=GitTools.COMMIT,
                description="Records changes to the repository",
                inputSchema=GitCommit.model_json_schema(),
            ),
            Tool(
                name=GitTools.ADD,
                description="Adds file contents to the staging area",
                inputSchema=GitAdd.model_json_schema(),
            ),
            Tool(
                name=GitTools.RESET,
                description="Unstages all staged changes",
                inputSchema=GitReset.model_json_schema(),
            ),
            Tool(
                name=GitTools.LOG,
                description="Shows the commit logs",
                inputSchema=GitLog.model_json_schema(),
            ),
            Tool(
                name=GitTools.CREATE_BRANCH,
                description="Creates a new branch from an optional base branch",
                inputSchema=GitCreateBranch.model_json_schema(),
            ),
            Tool(
                name=GitTools.CHECKOUT,
                description="Switches branches",
                inputSchema=GitCheckout.model_json_schema(),
            ),
            Tool(
                name=GitTools.SHOW,
                description="Shows the contents of a commit",
                inputSchema=GitShow.model_json_schema(),
            ),
            Tool(
                name=GitTools.INIT,
                description="Initialize a new Git repository",
                inputSchema=GitInit.model_json_schema(),
            )
        ]

    @mcp._mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        repo_path = Path(arguments["repo_path"])
        
        # Handle git init separately since it doesn't require an existing repo
        if name == GitTools.INIT:
            try:
                schema = GitInit.model_validate(arguments)  # Validate the GitInit schema
                result = GitOperation.git_init(str(repo_path))
                return [TextContent(
                    type="text",
                    text=result
                )]
            except ValidationError as e:
                raise ValueError(f"Invalid arguments for {name}: {e}")
            
        # For all other commands, we need an existing repo
        try:
            repo = git.Repo(repo_path)
        except git.exc.InvalidGitRepositoryError:
            raise ValueError(f"The path {repo_path} is not a valid Git repository.")
        
        match name:
            case GitTools.STATUS:
                try:
                    schema = GitStatus.model_validate(arguments)  # Validate GitStatus schema
                    status = GitOperation.git_status(repo)
                    return [TextContent(
                        type="text",
                        text=f"Repository status:\n{status}"
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")
                    
            case GitTools.PULL:
                try:
                    schema = GitPull.model_validate(arguments)  # Validate GitPull schema
                    result = GitOperation.git_pull(repo, schema.remote_name, schema.branch_name)
                    return [TextContent(
                        type="text",
                        text=f"Pull result:\n{result}"
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.PUSH:
                try:
                    schema = GitPush.model_validate(arguments)  # Validate GitPush schema
                    result = GitOperation.git_push(repo, schema.remote_name, schema.branch_name)
                    return [TextContent(
                        type="text",
                        text=f"Push result:\n{result}"
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.DIFF_UNSTAGED:
                try:
                    schema = GitDiffUnstaged.model_validate(arguments)  # Validate GitDiffUnstaged schema
                    diff = GitOperation.git_diff_unstaged(repo)
                    return [TextContent(
                        type="text",
                        text=f"Unstaged changes:\n{diff}"
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.DIFF_STAGED:
                try:
                    schema = GitDiffStaged.model_validate(arguments)  # Validate GitDiffStaged schema
                    diff = GitOperation.git_diff_staged(repo)
                    return [TextContent(
                        type="text",
                        text=f"Staged changes:\n{diff}"
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.DIFF:
                try:
                    schema = GitDiff.model_validate(arguments)  # Validate GitDiff schema
                    diff = GitOperation.git_diff(repo, schema.target)
                    return [TextContent(
                        type="text",
                        text=f"Diff with {schema.target}:\n{diff}"
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.COMMIT:
                try:
                    schema = GitCommit.model_validate(arguments)  # Validate GitCommit schema
                    result = GitOperation.git_commit(repo, schema.message)
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.ADD:
                try:
                    schema = GitAdd.model_validate(arguments)  # Validate GitAdd schema
                    result = GitOperation.git_add(repo, schema.files)
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.RESET:
                try:
                    schema = GitReset.model_validate(arguments)  # Validate GitReset schema
                    result = GitOperation.git_reset(repo)
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.LOG:
                try:
                    schema = GitLog.model_validate(arguments)  # Validate GitLog schema
                    log = GitOperation.git_log(repo, schema.max_count)
                    return [TextContent(
                        type="text",
                        text="Commit history:\n" + "\n".join(log)
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.CREATE_BRANCH:
                try:
                    schema = GitCreateBranch.model_validate(arguments)  # Validate GitCreateBranch schema
                    result = GitOperation.git_create_branch(
                        repo,
                        schema.branch_name,
                        schema.base_branch
                    )
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.CHECKOUT:
                try:
                    schema = GitCheckout.model_validate(arguments)  # Validate GitCheckout schema
                    result = GitOperation.git_checkout(repo, schema.branch_name)
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case GitTools.SHOW:
                try:
                    schema = GitShow.model_validate(arguments)  # Validate GitShow schema
                    result = GitOperation.git_show(repo, schema.revision)
                    return [TextContent(
                        type="text",
                        text=result
                    )]
                except ValidationError as e:
                    raise ValueError(f"Invalid arguments for {name}: {e}")

            case _:
                raise ValueError(f"Unknown tool: {name}")

# 运行服务器
def main(port: int = 9201):
    server = Server(port)
    server.run()

if __name__ == "__main__":
    import argparse
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9201)
    args = parser.parse_args()

    # 调用主函数
    main(port=args.port)

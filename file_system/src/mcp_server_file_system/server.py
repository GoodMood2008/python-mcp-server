import os
import sys
import pathlib
import shutil
import difflib
from pathlib import Path
from glob import glob
import json
import re
from typing import List, Dict
from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP
import mcp.types as types

class FileSystem():
    # Utility functions for file operations
    def get_file_stats(file_path: str) -> Dict:
        stats = os.stat(file_path)
        return {
            'size': stats.st_size,
            'created': stats.st_ctime,
            'modified': stats.st_mtime,
            'accessed': stats.st_atime,
            'is_directory': os.path.isdir(file_path),
            'is_file': os.path.isfile(file_path),
            'permissions': oct(stats.st_mode)[-3:]
        }

    def read_file(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def write_file(file_path: str, content: str) -> None:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def create_directory(file_path: str) -> None:
        os.makedirs(file_path, exist_ok=True)

    def list_directory(file_path: str) -> List[str]:
        return [f"[DIR] {entry}" if os.path.isdir(entry) else f"[FILE] {entry}" 
                for entry in os.listdir(file_path)]

    def move_file(source: str, destination: str) -> None:
        shutil.move(source, destination)

    def search_files(root_path: str, pattern: str, exclude_patterns: List[str]) -> List[str]:
        results = []
        for root, dirs, files in os.walk(root_path):
            for name in files + dirs:
                full_path = os.path.join(root, name)
                # Check for exclude patterns
                if any(re.match(exclude_pattern, full_path) for exclude_pattern in exclude_patterns):
                    continue
                if pattern.lower() in name.lower():
                    results.append(full_path)
        return results

    def apply_file_edits(file_path: str, edits: List[Dict], dry_run: bool = False) -> str:
        content = FileSystem.read_file(file_path)

        for edit in edits:
            old_text = edit['oldText']
            new_text = edit['newText']
            
            if old_text not in content:
                raise ValueError(f"Could not find exact match for edit: {old_text}")
            
            content = content.replace(old_text, new_text)

        # Generate diff if needed
        if dry_run:
            diff = difflib.unified_diff(content.splitlines(), content.splitlines(), fromfile=file_path, tofile=file_path)
            return '\n'.join(diff)
        else:
            FileSystem.write_file(file_path, content)
            return f"File {file_path} successfully edited."
    

# 参数模型定义
class ReadFileArgsSchema(BaseModel):
    path: str

class ReadMultipleFilesArgsSchema(BaseModel):
    paths: List[str]

class WriteFileArgsSchema(BaseModel):
    path: str
    content: str

class EditOperation(BaseModel):
    oldText: str
    newText: str

class EditFileArgsSchema(BaseModel):
    path: str
    edits: List[EditOperation]
    dryRun: bool = False  # default to False

class CreateDirectoryArgsSchema(BaseModel):
    path: str

class ListDirectoryArgsSchema(BaseModel):
    path: str

class DirectoryTreeArgsSchema(BaseModel):
    path: str

class MoveFileArgsSchema(BaseModel):
    source: str
    destination: str

class SearchFilesArgsSchema(BaseModel):
    path: str
    pattern: str
    excludePatterns: List[str] = []  # default to an empty list

class GetFileInfoArgsSchema(BaseModel):
    path: str

# Server and request handler (mockup for simplicity)
class Server:
    mcp: FastMCP = FastMCP("mcp-file-system")
    allowed_directories = None  # List[str] = None
    
    def __init__(self, port, allowed_dirs):
        Server.mcp.settings.port = port
        Server.allowed_directories = [Server.normalize_path(Server.expand_home(dir)) for dir in allowed_dirs]

    # Normalize paths
    def normalize_path(p: str) -> str:
        return os.path.normpath(p)

    def expand_home(filepath: str) -> str:
        if filepath.startswith('~'):
            return str(Path.home() / filepath[1:])
        return filepath
    
    # run
    def run(self):
        self.mcp.run('sse')

    # Security utilities
    async def validate_path(requested_path: str) -> str:
        expanded_path = Server.expand_home(requested_path)
        absolute = os.path.abspath(expanded_path)
        normalized_requested = Server.normalize_path(absolute)

        # Check if path is within allowed directories
        if not any(normalized_requested.startswith(dir) for dir in Server.allowed_directories):
            raise PermissionError(f"Access denied - path outside allowed directories: {absolute}")

        # Check if path is a symlink and validate
        real_path = os.path.realpath(absolute)
        if not any(real_path.startswith(dir) for dir in Server.allowed_directories):
            raise PermissionError(f"Access denied - symlink target outside allowed directories")
        
        return real_path
    
    @mcp._mcp_server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            {
                "name": "read_file",
                "description": "Read the complete contents of a file from the file system. "
                            "Handles various text encodings and provides detailed error messages "
                            "if the file cannot be read. Use this tool when you need to examine "
                            "the contents of a single file. Only works within allowed directories.",
                "inputSchema": ReadFileArgsSchema.model_json_schema(),
            },
            {
                "name": "read_multiple_files",
                "description": "Read the contents of multiple files simultaneously. This is more "
                            "efficient than reading files one by one when you need to analyze "
                            "or compare multiple files. Each file's content is returned with its "
                            "path as a reference. Failed reads for individual files won't stop "
                            "the entire operation. Only works within allowed directories.",
                "inputSchema": ReadMultipleFilesArgsSchema.model_json_schema(),
            },
            {
                "name": "write_file",
                "description": "Create a new file or completely overwrite an existing file with new content. "
                            "Use with caution as it will overwrite existing files without warning. "
                            "Handles text content with proper encoding. Only works within allowed directories.",
                "inputSchema": WriteFileArgsSchema.model_json_schema(),
            },
            {
                "name": "edit_file",
                "description": "Make line-based edits to a text file. Each edit replaces exact line sequences "
                            "with new content. Returns a git-style diff showing the changes made. "
                            "Only works within allowed directories.",
                "inputSchema": EditFileArgsSchema.model_json_schema(),
            },
            {
                "name": "create_directory",
                "description": "Create a new directory or ensure a directory exists. Can create multiple "
                            "nested directories in one operation. If the directory already exists, "
                            "this operation will succeed silently. Perfect for setting up directory "
                            "structures for projects or ensuring required paths exist. Only works within allowed directories.",
                "inputSchema": CreateDirectoryArgsSchema.model_json_schema(),
            },
            {
                "name": "list_directory",
                "description": "Get a detailed listing of all files and directories in a specified path. "
                            "Results clearly distinguish between files and directories with [FILE] and [DIR] "
                            "prefixes. This tool is essential for understanding directory structure and "
                            "finding specific files within a directory. Only works within allowed directories.",
                "inputSchema": ListDirectoryArgsSchema.model_json_schema(),
            },
            {
                "name": "directory_tree",
                "description": "Get a recursive tree view of files and directories as a JSON structure. "
                            "Each entry includes 'name', 'type' (file/directory), and 'children' for directories. "
                            "Files have no children array, while directories always have a children array (which may be empty). "
                            "The output is formatted with 2-space indentation for readability. Only works within allowed directories.",
                "inputSchema": DirectoryTreeArgsSchema.model_json_schema(),
            },
            {
                "name": "move_file",
                "description": "Move or rename files and directories. Can move files between directories "
                            "and rename them in a single operation. If the destination exists, the "
                            "operation will fail. Works across different directories and can be used "
                            "for simple renaming within the same directory. Both source and destination must be within allowed directories.",
                "inputSchema": MoveFileArgsSchema.model_json_schema(),
            },
            {
                "name": "search_files",
                "description": "Recursively search for files and directories matching a pattern. "
                            "Searches through all subdirectories from the starting path. The search "
                            "is case-insensitive and matches partial names. Returns full paths to all "
                            "matching items. Great for finding files when you don't know their exact location. "
                            "Only searches within allowed directories.",
                "inputSchema": SearchFilesArgsSchema.model_json_schema(),
            },
            {
                "name": "get_file_info",
                "description": "Retrieve detailed metadata about a file or directory. Returns comprehensive "
                            "information including size, creation time, last modified time, permissions, "
                            "and type. This tool is perfect for understanding file characteristics "
                            "without reading the actual content. Only works within allowed directories.",
                "inputSchema": GetFileInfoArgsSchema.model_json_schema(),
            },
            {
                "name": "list_allowed_directories",
                "description": "Returns the list of directories that this server is allowed to access. "
                            "Use this to understand which directories are available before trying to access files.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]


    @mcp._mcp_server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            # 根据操作类型选择对应的 Schema 和操作
            if name == "read_file":
                schema = ReadFileArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                content = await FileSystem.read_file(valid_path)
                return [types.TextContent(type="text", text=content)]

            elif name == "read_multiple_files":
                schema = ReadMultipleFilesArgsSchema.model_validate(arguments)
                results = []
                for file_path in schema.paths:
                    try:
                        valid_path = Server.validate_path(file_path)
                        content = await FileSystem.read_file(valid_path)
                        results.append(f"{file_path}:\n{content}\n")
                    except Exception as error:
                        results.append(f"{file_path}: Error - {str(error)}")
                return [types.TextContent(type="text", text="\n---\n".join(results))]

            elif name == "write_file":
                schema = WriteFileArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                await FileSystem.write_file(valid_path, schema.content)
                return [types.TextContent(type="text", text=f"Successfully wrote to {schema.path}")]

            elif name == "edit_file":
                schema = EditFileArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                result = await FileSystem.apply_file_edits(valid_path, schema.edits, schema.dryRun)
                return [types.TextContent(type="text", text=result)]

            elif name == "create_directory":
                schema = CreateDirectoryArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                await FileSystem.create_directory(valid_path)
                return [types.TextContent(type="text", text=f"Successfully created directory {schema.path}")]

            elif name == "list_directory":
                schema = ListDirectoryArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                entries = await FileSystem.list_directory(valid_path)
                formatted = "\n".join([f"[{'DIR' if entry['is_directory'] else 'FILE'}] {entry['name']}" for entry in entries])
                return [types.TextContent(type="text", text=formatted)]

            elif name == "directory_tree":
                schema = DirectoryTreeArgsSchema.model_validate(arguments)

                # 构建目录树
                async def build_tree(current_path: str):
                    valid_path = Server.validate_path(current_path)
                    entries = await FileSystem.list_directory(valid_path)
                    result = []
                    for entry in entries:
                        entry_data = {
                            "name": entry['name'],
                            "type": 'directory' if entry['is_directory'] else 'file',
                            "children": await build_tree(f"{current_path}/{entry['name']}") if entry['is_directory'] else []
                        }
                        result.append(entry_data)
                    return result

                tree_data = await build_tree(schema.path)
                return [types.TextContent(type="text", text=json.dumps(tree_data, indent=2))]

            elif name == "move_file":
                schema = MoveFileArgsSchema.model_validate(arguments)
                valid_source_path = Server.validate_path(schema.source)
                valid_dest_path = Server.validate_path(schema.destination)
                await FileSystem.move_file(valid_source_path, valid_dest_path)
                return [types.TextContent(type="text", text=f"Successfully moved {schema.source} to {schema.destination}")]

            elif name == "search_files":
                schema = SearchFilesArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                results = await FileSystem.search_files(valid_path, schema.pattern, schema.excludePatterns)
                return [types.TextContent(type="text", text="\n".join(results) if results else "No matches found")]

            elif name == "get_file_info":
                schema = GetFileInfoArgsSchema.model_validate(arguments)
                valid_path = Server.validate_path(schema.path)
                file_info = await FileSystem.get_file_info(valid_path)
                return [types.TextContent(type="text", text="\n".join([f"{key}: {value}" for key, value in file_info.items()]))]

            elif name == "list_allowed_directories":
                return [types.TextContent(type="text", text="\n".join(Server.allowed_directories))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as error:
            error_message = str(error)
            return [types.TextContent(type="text", text=f"Error: {error_message}")]


# 运行服务器
def main(port: int = 9200, allow_dirs: List[str] = []):

    # Validate that all directories exist and are accessible
    for dir in allow_dirs:
        try:
            if not os.path.isdir(Server.expand_home(dir)):
                print(f"Error: {dir} is not a directory")
                sys.exit(1)
        except Exception as e:
            print(f"Error accessing directory {dir}: {str(e)}")
            sys.exit(1)
    server = Server(port, allow_dirs)
    server.run()

if __name__ == "__main__":
    import argparse
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9200)
    parser.add_argument('--allow_dirs', type=str, nargs='+', default=[])
    args = parser.parse_args()

    # 调用主函数
    main(port=args.port, allow_dirs=args.allow_dirs)
from setuptools import setup, find_packages

setup(
    name="mcp_server_konwledge_service",
    version="0.1.1",
    description="mcp_server_konwledge_service",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="jieyu",
    author_email="26741980@qq.com",
    python_requires=">=3.11",
    install_requires=[
        "mcp>=1.0.0",
        "pydantic>=2.11.3",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "mcp_server_konwledge_service = mcp_server_konwledge_service.server:main",  # 对应 pyproject.toml 中的脚本
        ],
    },
    include_package_data=True,  # 确保包数据文件被包含
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)

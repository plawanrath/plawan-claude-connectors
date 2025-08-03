# @plawanrath

#!/usr/bin/env python
import os, sys, asyncio
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool                      

# Helper for Claude Desktop logs
def log(msg: str):
    print(f"[FilesystemConnector] {msg}", file=sys.stderr)

mcp = FastMCP("filesystem-connector")

# ---------- Tools -----------------------------------------------------------
@mcp.tool(name="list_directory", description="Lists files / sub‑dirs in a directory")
async def list_directory(path: str = ".") -> dict:
    log(f"list_directory({path})")
    if not os.path.isdir(path):
        return {"error": f"'{path}' is not a directory"}
    return {"directory": path, "contents": os.listdir(path)}


@mcp.tool(name="read_files", description="Read up to 8 kB from a file")
async def read_file(path: str) -> dict:
    log(f"read_file({path})")
    if not os.path.isfile(path):
        return {"error": f"File '{path}' not found"}
    with open(path, "r", encoding="utf‑8", errors="ignore") as f:
        return {"file_path": path, "content": f.read(8000)}


@mcp.tool(name="search_files", description="Find files whose *names* contain a keyword (recursive)")
async def search_files(start_path: str = ".", keyword: str = "") -> dict:
    log(f"search_files({start_path}, {keyword})")
    if not os.path.isdir(start_path):
        return {"error": f"'{start_path}' is not a directory"}
    matches = [
        os.path.join(root, f)
        for root, _, files in os.walk(start_path)
        for f in files
        if keyword.lower() in f.lower()
    ]
    return {"start_path": start_path, "keyword": keyword, "matches": matches}


# ---------- Entrypoint ------------------------------------------------------
if __name__ == "__main__":
    try:
        mcp.run()          # defaults to stdio transport for Claude Desktop
    except KeyboardInterrupt:
        log("Server shutting down.")
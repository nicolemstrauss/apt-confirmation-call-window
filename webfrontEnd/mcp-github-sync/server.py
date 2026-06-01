import os
import base64
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github-sync")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
API = "https://api.github.com"


@mcp.tool()
async def push_file(local_path: str, repo: str, repo_path: str, message: str = "Update file") -> str:
    """Push a local file to a GitHub repo. repo format: owner/repo"""
    content = open(os.path.expanduser(local_path), "rb").read()
    encoded = base64.b64encode(content).decode()

    async with httpx.AsyncClient() as client:
        # Check if file exists (need sha for updates)
        r = await client.get(f"{API}/repos/{repo}/contents/{repo_path}", headers=HEADERS)
        data = {"message": message, "content": encoded}
        if r.status_code == 200:
            data["sha"] = r.json()["sha"]

        r = await client.put(f"{API}/repos/{repo}/contents/{repo_path}", headers=HEADERS, json=data)
        if r.status_code in (200, 201):
            return f"Pushed {local_path} -> {repo}:{repo_path}"
        return f"Error: {r.status_code} {r.text}"


@mcp.tool()
async def pull_file(repo: str, repo_path: str, local_path: str) -> str:
    """Pull a file from GitHub repo to local machine. repo format: owner/repo"""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API}/repos/{repo}/contents/{repo_path}", headers=HEADERS)
        if r.status_code != 200:
            return f"Error: {r.status_code} {r.text}"

        content = base64.b64decode(r.json()["content"])
        dest = os.path.expanduser(local_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(content)
        return f"Pulled {repo}:{repo_path} -> {dest}"


@mcp.tool()
async def list_repo_files(repo: str, path: str = "") -> str:
    """List files in a GitHub repo directory. repo format: owner/repo"""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API}/repos/{repo}/contents/{path}", headers=HEADERS)
        if r.status_code != 200:
            return f"Error: {r.status_code} {r.text}"
        items = r.json()
        return "\n".join(f"{'[dir] ' if i['type'] == 'dir' else ''}{i['path']}" for i in items)


if __name__ == "__main__":
    mcp.run(transport="stdio")

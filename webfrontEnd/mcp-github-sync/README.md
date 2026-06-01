# mcp-github-sync

Minimal MCP server to sync files between your local machine and GitHub.

## Tools

- **push_file** — Push a local file to a GitHub repo
- **pull_file** — Pull a file from GitHub to your local machine
- **list_repo_files** — List files in a GitHub repo directory

## Setup

1. Create a GitHub Personal Access Token at https://github.com/settings/tokens (needs `repo` scope)

2. Export it in your shell profile (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export GITHUB_TOKEN="ghp_your_token_here"
   ```

3. The server is already registered globally in `~/.kiro/settings/mcp.json`. Restart Kiro to pick it up.

## Usage (in Kiro)

```
Push index.html to my repo nstrauss/webfrontEnd
Pull README.md from nstrauss/webfrontEnd to ./README.md
List files in nstrauss/webfrontEnd
```

## Manual test

```bash
cd /Users/nstrauss/webfrontEnd/mcp-github-sync
source .venv/bin/activate
python server.py
```

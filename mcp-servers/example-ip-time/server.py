# example-mcp-hello/server.py
# ──────────────────────────────────────────────────────────────
# Example MCP server for AppTelePorter.
# Demonstrates the simplest possible MCP server with greeting tools
# and public API integrations (no API keys needed).
# ──────────────────────────────────────────────────────────────
import datetime
import json
import urllib.request
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example-hello")

@mcp.tool()
def public_ip() -> str:
    """Get the public IP address of this machine. Useful for checking outbound connectivity and NAT."""
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as resp:
            data = json.loads(resp.read())
        return f"🌐 Public IP: {data['ip']}"
    except Exception as e:
        return f"Couldn't determine public IP: {e}"


@mcp.tool()
def current_time(timezone: str = "UTC") -> str:
    """Return the current date and time. Useful when the user asks what time it is."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"🕐 Current time ({timezone}): {now}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
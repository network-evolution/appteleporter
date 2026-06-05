# example-server/server.py
# ──────────────────────────────────────────────────────────────
# Example MCP server for AppTelePorter.
# Demonstrates how to build an MCP server that gets auto-discovered.
# This server provides a simple network ping tool.
# ──────────────────────────────────────────────────────────────
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example-network-tools")


@mcp.tool()
def ping_host(host: str, count: int = 3) -> str:
    """Ping a network host and return the result. Useful for basic connectivity checks."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", host],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Ping failed:\n{result.stderr or result.stdout}"
    except subprocess.TimeoutExpired:
        return f"Ping to {host} timed out after 15 seconds"
    except Exception as e:
        return f"Error pinging {host}: {str(e)}"


@mcp.tool()
def dns_lookup(hostname: str) -> str:
    """Perform a DNS lookup for the given hostname using the system resolver."""
    try:
        import socket
        results = socket.getaddrinfo(hostname, None)
        addresses = list(set(r[4][0] for r in results))
        return f"DNS results for {hostname}:\n" + "\n".join(f"  {addr}" for addr in addresses)
    except socket.gaierror as e:
        return f"DNS lookup failed for {hostname}: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
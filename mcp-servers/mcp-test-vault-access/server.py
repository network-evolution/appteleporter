# vault-test/server.py
# ──────────────────────────────────────────────────────────────
# Example MCP server for AppTelePorter.
# Demonstrates the simplest possible MCP server with greeting tools
# and public API integrations (no API keys needed).
#
# HOW IT WORKS
# ────────────
# Each @mcp.tool() decorated function becomes a tool that AppTelePorter
# can call during AI conversations. The function name becomes the tool
# name, the docstring becomes the tool description, and typed parameters
# become the tool's input schema — no extra configuration needed.

# HOW TO REGISTER THIS SERVER IN APPTELEPORTER
# ─────────────────────────────────────────────
# Open mcp_config.json (visible in the workspace panel) and add the
# following entry inside the "mcpServers" object:
#
#   "vault-test": {
#     "command": "python3",
#     "args": ["server.py"],
#     "cwd": "/app/backend/appteleporter-data/mcp_servers/vault-test",
#     "env": {}
#   }
#
# Save mcp_config.json, then click "Load Changes to ATP" in the bottom
# panel to reload — your tools will appear in the ATP tool list.
#
# HOW TO TEST RIGHT HERE
# ──────────────────────
# 1. Use "Refresh Tools" in the bottom panel to detect @mcp.tool() functions.
# 2. Select a tool from the Tool Selector drop-down.
# 3. Click "Fetch Params" to load its parameter form.
# 4. Fill in any parameters and click "Run MCP Tool" to execute live.
#
# ADDING DEPENDENCIES
# ───────────────────
# Create a requirements.txt next to this file (e.g. "requests\nparamiko")
# then click "Install Deps" to pip-install them into the server environment.
# ──────────────────────────────────────────────────────────────
import datetime
import json
import urllib.request
from mcp.server.fastmcp import FastMCP
from core.mcp_vault import get_vault_cred

mcp = FastMCP("vault-test")


@mcp.tool()
def test_vault_access(device_name: str) -> str:
    """
    Retrieve and display credential details for a vault-stored device.
    Password is masked in the output — all other fields are shown.
    """

    creds = get_vault_cred(device_name)

    if creds is None:
        return (
            f"No credential found in the vault for '{device_name}'.\n\n"
            f"To add one:\n"
            f"  1. Go to Settings → Credentials in AppTelePorter.\n"
            f"  2. Click '+ Add Credential'.\n"
            f"  3. Set Name = '{device_name}', then fill in Host, Username, Password, and Port.\n"
            f"  4. Click Save, then retry this tool."
        )

    host     = creds.get("host",     "<not set>")
    username = creds.get("username", "<not set>")
    port     = creds.get("port",     "<not set>")
    password = creds.get("password", "")

    password_status = "set (hidden)" if password else "NOT SET"

    return (
        f"Vault credential lookup successful for '{device_name}':\n"
        f"  Host     : {host}\n"
        f"  Username : {username}\n"
        f"  Port     : {port}\n"
        f"  Password : {password_status}\n\n"
        f"The vault is working correctly. You can now use get_vault_cred('{device_name}') "
        f"inside any plugin handler to retrieve these credentials securely."
    )

# @mcp.tool()
# def public_ip() -> str:
#     """Get the public IP address of this machine. Useful for checking outbound connectivity and NAT."""
#     try:
#         with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as resp:
#             data = json.loads(resp.read())
#         return f"\U0001f310 Public IP: {data['ip']}"
#     except Exception as e:
#         return f"Couldn't determine public IP: {e}"


# @mcp.tool()
# def current_time(timezone: str = "UTC") -> str:
#     """Return the current date and time. Useful when the user asks what time it is."""
#     now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     return f"\U0001f550 Current time ({timezone}): {now}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

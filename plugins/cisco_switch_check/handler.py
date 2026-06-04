# plugins/cisco_switch_check/handler.py
# ═══════════════════════════════════════════════════════════════════════════════
#
#  Cisco Switch Check Plugin — Real device queries via Netmiko + Vault
#  ────────────────────────────────────────────────────────────────────
#
#  PREREQUISITES
#  ─────────────
#  1. Add  netmiko  to this plugin's requirements.txt (or the global one):
#         netmiko>=4.3.0
#
#  2. Create a credential in  Settings → Credentials  with:
#         Name     :  e.g. core-sw-01
#         Host/IP  :  e.g. 192.168.1.10
#         Username :  your SSH username
#         Password :  your SSH password
#         Port     :  22  (default SSH)
#
#  3. Enable  "cisco_switch_check"  in  Settings → Tools.
#
#  USAGE EXAMPLES (in chat)
#  ────────────────────────
#     "Check VLANs on core-sw-01"
#     "Show me the interfaces on access-switch-floor2"
#     "Run a health check on core-sw-01"
#     "Get the ARP table from distribution-sw-03"
#
#  QUESTIONS?
#  ──────────
#  For additional help:  info@networkevolution.in
#
# ═══════════════════════════════════════════════════════════════════════════════

from core.vault_helpers import get_vault_cred

try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import (
        NetMikoTimeoutException,
        NetMikoAuthenticationException,
    )
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False


# ── Command map ───────────────────────────────────────────────────────────────
# Maps each check_type to one or more Cisco IOS commands.

COMMANDS = {
    "vlans":      ["show vlan brief"],
    "interfaces": ["show ip interface brief"],
    "version":    ["show version"],
    "arp":        ["show arp"],
    "mac":        ["show mac address-table"],
    "inventory":  ["show inventory"],
    "health":     ["show version", "show ip interface brief", "show vlan brief"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_connection_params(creds: dict) -> dict:
    """Build a Netmiko connection dictionary from vault credentials."""
    return {
        "device_type": creds.get("device_type", "cisco_ios"),
        "host":        creds.get("host"),
        "username":    creds.get("username"),
        "password":    creds.get("password"),
        "port":        int(creds.get("port", 22)),
        "timeout":     30,
        "read_timeout_override": 60,
    }


def _run_commands(connection_params: dict, commands: list[str]) -> dict[str, str]:
    """
    Open an SSH session, run each command, and return a dict of
    {command: output}.  The session is closed automatically.
    """
    results = {}
    with ConnectHandler(**connection_params) as conn:
        # Optional: enter enable mode if the device requires it
        # conn.enable()
        for cmd in commands:
            output = conn.send_command(cmd, read_timeout=60)
            results[cmd] = output.strip()
    return results


def _format_output(device_name: str, check_type: str,
                   results: dict[str, str]) -> str:
    """Format command outputs into a readable response."""
    sections = []
    header = f"━━━  {device_name}  ·  {check_type.upper()} CHECK  ━━━"
    sections.append(header)

    for cmd, output in results.items():
        sections.append(f"\n▸ {cmd}\n{'─' * 60}")
        sections.append(output if output else "(no output)")

    sections.append(f"\n{'━' * 60}")
    sections.append(f"✔ Completed {len(results)} command(s) on {device_name}")
    return "\n".join(sections)


# ── Main entry point ─────────────────────────────────────────────────────────

def cisco_switch_check(device_name: str, check_type: str) -> str:
    """
    Connect to a Cisco switch via Netmiko using vault credentials
    and run the requested check.

    Parameters
    ----------
    device_name : str
        Credential name stored in  Settings → Credentials.
    check_type  : str
        One of: vlans, interfaces, version, arp, mac, inventory, health.
    """

    # ── Guard: netmiko installed? ─────────────────────────────────────────
    if not NETMIKO_AVAILABLE:
        return (
            "❌ Netmiko is not installed in the container.\n\n"
            "Add the following to your requirements.txt and rebuild:\n"
            "    netmiko>=4.3.0"
        )

    # ── Validate check_type ───────────────────────────────────────────────
    check_type = check_type.strip().lower()
    if check_type not in COMMANDS:
        valid = ", ".join(sorted(COMMANDS.keys()))
        return (
            f"❌ Unknown check type: '{check_type}'.\n"
            f"Valid options: {valid}"
        )

    # ── Retrieve vault credentials ────────────────────────────────────────
    creds = get_vault_cred(device_name)
    if creds is None:
        return (
            f"❌ No credential found in the vault for '{device_name}'.\n\n"
            f"To add one:\n"
            f"  1. Go to  Settings → Credentials  in AppTelePorter.\n"
            f"  2. Click  '+ Add Credential'.\n"
            f"  3. Set  Name = '{device_name}',  then fill in Host, "
            f"Username, Password, and Port.\n"
            f"  4. Click  Save,  then retry."
        )

    host = creds.get("host")
    if not host:
        return (
            f"❌ Credential '{device_name}' exists but has no Host/IP set.\n"
            f"Update it in  Settings → Credentials."
        )

    # ── Connect and run commands ──────────────────────────────────────────
    try:
        conn_params = _build_connection_params(creds)
        commands    = COMMANDS[check_type]
        results     = _run_commands(conn_params, commands)
        return _format_output(device_name, check_type, results)

    except NetMikoTimeoutException:
        return (
            f"❌ Connection timed out to {host} (port {creds.get('port', 22)}).\n\n"
            f"Possible causes:\n"
            f"  • Device is unreachable from the AppTelePorter host.\n"
            f"  • SSH is not enabled on the switch.\n"
            f"  • Firewall is blocking port {creds.get('port', 22)}.\n"
            f"  • Incorrect Host/IP in the vault credential."
        )

    except NetMikoAuthenticationException:
        return (
            f"❌ Authentication failed for '{device_name}' at {host}.\n\n"
            f"Possible causes:\n"
            f"  • Wrong username or password in the vault.\n"
            f"  • SSH user not configured on the switch.\n"
            f"  • AAA / TACACS+ rejecting the credentials."
        )

    except Exception as e:
        return (
            f"❌ Unexpected error connecting to '{device_name}' ({host}):\n"
            f"    {type(e).__name__}: {e}\n\n"
            f"Check the device reachability and vault credential settings."
        )
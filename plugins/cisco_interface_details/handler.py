# plugins/cisco_interface_detail/handler.py
# ═══════════════════════════════════════════════════════════════════════════════
#
#  Cisco Interface Detail Plugin
#  ─────────────────────────────
#  Connects to a Cisco IOS device via SSH (Netmiko) and runs a comprehensive
#  "show interfaces <name>" diagnostic for one or all interfaces.
#
#  HIGH-LEVEL FLOW
#  ───────────────
#  Step 1 — Retrieve vault credentials for the device.
#  Step 2 — Open an SSH session via Netmiko.
#  Step 3 — Discover all interfaces using "show ip interface brief".
#  Step 4 — If the user asked for a specific interface, validate it exists.
#            If it does not exist, return a helpful error + the available list.
#  Step 5 — Run "show interfaces <name>" for each target interface.
#            Failures on individual interfaces are caught and reported inline
#            so that one bad interface never kills the whole run.
#  Step 6 — Format and return the full diagnostic output.
#
#  PREREQUISITES
#  ─────────────
#  1. Add netmiko to this plugin's requirements.txt (or the global one):
#         netmiko>=4.3.0
#
#  2. Create a credential in Settings → Credentials:
#         Name     : e.g. core-rtr-01
#         Host/IP  : e.g. 10.0.0.1
#         Username : your SSH username
#         Password : your SSH password
#         Port     : 22  (default)
#
#  3. Enable "cisco_interface_detail" in Settings → Tools.
#
#  USAGE EXAMPLES (in chat)
#  ────────────────────────
#    "Check all interfaces on core-rtr-01"
#    "Show interface Gi0/0 on edge-router"
#    "Are there CRC errors on dist-sw-02?"
#    "Give me interface Vlan10 details from access-sw-floor3"
#
#  QUESTIONS?
#  ──────────
#  For additional help:  info@networkevolution.in
#
# ═══════════════════════════════════════════════════════════════════════════════

import re
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


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — Cisco interface name normalisation
#  ─────────────────────────────────────────────────────────────────────────────
#  Cisco allows abbreviated interface names in CLI (e.g. "Gi0/0" instead of
#  "GigabitEthernet0/0").  When the user supplies a short-form name we need to
#  match it against the full names returned by "show ip interface brief".
#  This section defines the expansion map and helper functions.
# ══════════════════════════════════════════════════════════════════════════════

# Maps Cisco short-form prefixes → full prefix as IOS returns them.
CISCO_INTF_EXPANSIONS: dict[str, str] = {
    "gi":   "GigabitEthernet",
    "ge":   "GigabitEthernet",
    "fa":   "FastEthernet",
    "te":   "TenGigabitEthernet",
    "fo":   "FortyGigabitEthernet",
    "hu":   "HundredGigE",
    "tw":   "TwoGigabitEthernet",
    "fh":   "FiveGigabitEthernet",
    "mg":   "MgmtEth",
    "se":   "Serial",
    "lo":   "Loopback",
    "tu":   "Tunnel",
    "vl":   "Vlan",
    "po":   "Port-channel",
    "bv":   "BVI",
    "eth":  "Ethernet",
}


def _expand_intf_name(short: str) -> str | None:
    """
    Attempt to expand a Cisco short-form interface name to its full form.

    Examples
    --------
    "Gi0/0"      → "GigabitEthernet0/0"
    "Fa0/1"      → "FastEthernet0/1"
    "Lo0"        → "Loopback0"
    "Vlan10"     → "Vlan10"          (already correct)
    "Se0/0/0"    → "Serial0/0/0"

    Returns None if the prefix is not recognised.
    """
    # Split alphabetic prefix from the numeric suffix (e.g. "Gi" + "0/0")
    match = re.match(r'^([A-Za-z\-]+)(\d.*)?$', short.strip())
    if not match:
        return None

    prefix_raw, suffix = match.group(1), match.group(2) or ""
    prefix_lower = prefix_raw.lower()

    # Check for an exact or partial match in the expansion table.
    for short_key, full_key in CISCO_INTF_EXPANSIONS.items():
        if prefix_lower.startswith(short_key):
            return full_key + suffix

    return None  # Unknown prefix — caller will do a fuzzy match instead


def _normalise_intf_name(user_input: str, available: list[str]) -> str | None:
    """
    Given what the user typed, find the matching interface name in *available*.

    Strategy
    ────────
    1. Exact match (case-insensitive).
    2. Expand short-form prefix + numeric suffix, then exact match.
       e.g. "Gi0/0"  →  "GigabitEthernet0/0"
    3. Numeric-suffix substring match ONLY when the input contains digits.
       e.g. "0/0" matches "GigabitEthernet0/0".
       This pass is intentionally SKIPPED for inputs that contain only
       alphabetic characters (e.g. "Gigabit", "Gi", "fast") because those
       are ambiguous — they would silently match the first interface of that
       type instead of telling the user to be more specific.

    Returns the matched name from *available*, or None if no match found.
    """
    user_stripped = user_input.strip()
    user_lower    = user_stripped.lower()

    # --- Pass 1: exact case-insensitive match ---
    for name in available:
        if name.lower() == user_lower:
            return name

    # --- Pass 2: expand short-form prefix, then exact match ---
    expanded = _expand_intf_name(user_stripped)
    if expanded:
        for name in available:
            if name.lower() == expanded.lower():
                return name

    # --- Pass 3: numeric-suffix substring match ---
    # Only attempt this when the user input actually contains at least one
    # digit.  A bare type-word like "Gigabit" or "Gi" has no digit, so we
    # skip this pass entirely and fall through to return None — which causes
    # the caller to show the "interface not found" error with the full list.
    if re.search(r'\d', user_lower):
        for name in available:
            if user_lower in name.lower():
                return name

    return None


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — Device connectivity helpers
# ══════════════════════════════════════════════════════════════════════════════

def _build_connection_params(creds: dict) -> dict:
    """Build a Netmiko ConnectHandler parameter dict from vault credentials."""
    return {
        "device_type":           creds.get("device_type", "cisco_ios"),
        "host":                  creds.get("host"),
        "username":              creds.get("username"),
        "password":              creds.get("password"),
        "port":                  int(creds.get("port", 22)),
        "timeout":               30,
        "read_timeout_override": 90,
        # Disable auto-paging so we get complete output in one shot
        "global_delay_factor":   1,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — Interface discovery
#  ─────────────────────────────────────────────────────────────────────────────
#  Parse "show ip interface brief" to build the list of all interface names
#  present on the device.  We use this list for two purposes:
#    • Enumerate which interfaces to query when the user asks for "all".
#    • Validate a user-supplied interface name before running show commands.
# ══════════════════════════════════════════════════════════════════════════════

def _parse_ip_intf_brief(output: str) -> list[str]:
    """
    Extract interface names from the output of "show ip interface brief".

    IOS output looks like:
        Interface              IP-Address      OK? Method Status   Protocol
        GigabitEthernet0/0     192.168.1.1     YES NVRAM  up       up
        GigabitEthernet0/1     unassigned      YES NVRAM  up       up
        Loopback0              10.0.0.1        YES NVRAM  up       up

    We grab only the first column (the interface name).
    """
    names = []
    for line in output.splitlines():
        line = line.strip()
        # Skip blank lines and the header row
        if not line or line.lower().startswith("interface"):
            continue
        # First whitespace-delimited token is the interface name
        parts = line.split()
        if parts:
            names.append(parts[0])
    return names


def _discover_interfaces(conn) -> list[str]:
    """
    Run "show ip interface brief" on an open Netmiko connection and return
    the list of interface names found on the device.
    """
    raw = conn.send_command("show ip interface brief", read_timeout=60)
    return _parse_ip_intf_brief(raw)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — Per-interface data collection
#  ─────────────────────────────────────────────────────────────────────────────
#  Run "show interfaces <name>" for each target interface.  Individual
#  failures are caught so one unreachable interface does not abort the whole
#  diagnostic run.
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_interface_detail(conn, interface_name: str) -> tuple[bool, str]:
    """
    Run "show interfaces <interface_name>" on an open Netmiko connection.

    Returns
    ───────
    (True,  raw_output)   — command succeeded
    (False, error_message) — command failed or returned empty output
    """
    try:
        output = conn.send_command(
            f"show interfaces {interface_name}",
            read_timeout=60,
        ).strip()

        if not output:
            return False, f"Command returned empty output for {interface_name}."

        # IOS returns "% Invalid input" when the interface name is wrong.
        if output.lower().startswith("% invalid input") or \
           "invalid input" in output.lower():
            return False, f"Device returned 'Invalid input' for '{interface_name}'."

        return True, output

    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — Output formatting
#  ─────────────────────────────────────────────────────────────────────────────
#  Format the collected data into a readable block of text that the LLM can
#  summarise.  Each interface gets its own clearly-labelled section.
# ══════════════════════════════════════════════════════════════════════════════

_DIVIDER      = "─" * 70
_THICK_DIV    = "━" * 70


def _format_single_interface(name: str, success: bool, data: str) -> str:
    """Format the output section for one interface."""
    lines = [
        f"\n{'▶':─<1}  INTERFACE: {name}",
        _DIVIDER,
    ]
    if success:
        lines.append(data)
    else:
        lines.append(f"⚠  Could not retrieve details — {data}")
    return "\n".join(lines)


def _format_full_report(
    device_name: str,
    results: list[tuple[str, bool, str]],
    requested: str,
) -> str:
    """
    Assemble the complete diagnostic report.

    Parameters
    ──────────
    device_name : credential name / device label
    results     : list of (interface_name, success, data_or_error)
    requested   : what the user originally asked for ("all" or a specific name)
    """
    total      = len(results)
    succeeded  = sum(1 for _, ok, _ in results if ok)
    failed     = total - succeeded

    header_lines = [
        _THICK_DIV,
        f"  CISCO INTERFACE DIAGNOSTIC REPORT",
        f"  Device   : {device_name}",
        f"  Scope    : {requested}",
        f"  Checked  : {total} interface(s)   ✔ {succeeded} OK   ✘ {failed} failed",
        _THICK_DIV,
    ]

    body_sections = [
        _format_single_interface(name, ok, data)
        for name, ok, data in results
    ]

    footer_lines = [
        f"\n{_THICK_DIV}",
        f"  END OF REPORT — {device_name}",
        _THICK_DIV,
    ]

    return "\n".join(header_lines + body_sections + footer_lines)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — Main entry point
#  ─────────────────────────────────────────────────────────────────────────────
#  This is the function AppTelePorter calls when the LLM invokes the tool.
# ══════════════════════════════════════════════════════════════════════════════

def cisco_interface_detail(device_name: str, interface: str = "all") -> str:
    """
    Connect to a Cisco IOS device and return comprehensive interface details.

    Parameters
    ──────────
    device_name : str
        Credential name stored in Settings → Credentials.

    interface   : str  (default "all")
        "all"              — check every interface discovered on the device.
        "<interface_name>" — check only the specified interface.
                             Accepts full names ("GigabitEthernet0/0") or
                             Cisco short-forms ("Gi0/0", "Fa0/1", "Lo0", etc.).
    """

    # ── Guard: is Netmiko installed? ──────────────────────────────────────
    if not NETMIKO_AVAILABLE:
        return (
            "❌ Netmiko is not installed in the container.\n\n"
            "Add the following line to your requirements.txt and rebuild:\n"
            "    netmiko>=4.3.0"
        )

    # ── Normalise the interface parameter ────────────────────────────────
    interface = (interface or "all").strip()
    check_all = (interface.lower() == "all")

    # ── Retrieve vault credentials ────────────────────────────────────────
    creds = get_vault_cred(device_name)
    if creds is None:
        return (
            f"❌ No credential found in the vault for '{device_name}'.\n\n"
            f"To add one:\n"
            f"  1. Go to  Settings → Credentials  in AppTelePorter.\n"
            f"  2. Click  '+ Add Credential'.\n"
            f"  3. Set  Name = '{device_name}', then fill in Host, "
            f"Username, Password, and Port.\n"
            f"  4. Click  Save, then retry."
        )

    host = creds.get("host")
    if not host:
        return (
            f"❌ Credential '{device_name}' exists but has no Host/IP configured.\n"
            f"Update it in  Settings → Credentials."
        )

    # ── Open SSH session ──────────────────────────────────────────────────
    try:
        conn_params = _build_connection_params(creds)

        with ConnectHandler(**conn_params) as conn:
            # ── Step 3: Discover all interface names on the device ────────
            available_interfaces = _discover_interfaces(conn)

            if not available_interfaces:
                return (
                    f"❌ Could not discover any interfaces on '{device_name}'.\n"
                    f"The output of 'show ip interface brief' was empty or "
                    f"could not be parsed."
                )

            # ── Step 4a: Determine which interfaces to query ──────────────
            if check_all:
                # User wants all interfaces — query every one we found.
                target_interfaces = available_interfaces

            else:
                # User specified a particular interface — validate it first.
                matched = _normalise_intf_name(interface, available_interfaces)

                if matched is None:
                    # Interface not found — return helpful error + full list.
                    available_list = "\n".join(
                        f"    • {n}" for n in available_interfaces
                    )
                    return (
                        f"❌ Interface '{interface}' was not found on '{device_name}'.\n\n"
                        f"Available interfaces on this device:\n"
                        f"{available_list}\n\n"
                        f"Please retry with one of the names above."
                    )

                target_interfaces = [matched]

            # ── Step 5: Run "show interfaces <name>" for each target ──────
            # Failures on individual interfaces are caught here — a single
            # bad interface does NOT abort the entire run.
            results: list[tuple[str, bool, str]] = []

            for intf_name in target_interfaces:
                success, data = _fetch_interface_detail(conn, intf_name)
                results.append((intf_name, success, data))

        # ── Step 6: Format and return the full report ─────────────────────
        return _format_full_report(
            device_name=device_name,
            results=results,
            requested=interface,
        )

    # ── Connection-level error handling ───────────────────────────────────
    except NetMikoTimeoutException:
        port = creds.get("port", 22)
        return (
            f"❌ SSH connection timed out to '{device_name}' ({host}:{port}).\n\n"
            f"Possible causes:\n"
            f"  • Device is unreachable from the AppTelePorter host.\n"
            f"  • SSH is not enabled on the device (check 'ip ssh version 2').\n"
            f"  • A firewall is blocking TCP port {port}.\n"
            f"  • The Host/IP in the vault credential is incorrect."
        )

    except NetMikoAuthenticationException:
        return (
            f"❌ SSH authentication failed for '{device_name}' ({host}).\n\n"
            f"Possible causes:\n"
            f"  • Wrong username or password in the vault credential.\n"
            f"  • The SSH user is not defined on the device "
            f"('username <name> privilege 15 secret <pass>').\n"
            f"  • AAA / TACACS+ is rejecting the credentials."
        )

    except Exception as exc:
        return (
            f"❌ Unexpected error while connecting to '{device_name}' ({host}):\n"
            f"    {type(exc).__name__}: {exc}\n\n"
            f"Check device reachability and review the vault credential settings."
        )
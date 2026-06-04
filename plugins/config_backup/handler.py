# plugins/config_backup/handler.py
# ═══════════════════════════════════════════════════════════════════════════════
#
#  Config Backup Plugin — Bulk backup of all device configs via Netmiko + Vault
#  ─────────────────────────────────────────────────────────────────────────────
#
#  PURPOSE
#  ───────
#  When a user says "take config backup of all devices", this tool
#  automatically iterates through every device in the DEVICE_LIST below,
#  retrieves credentials from the vault, connects via Netmiko, pulls the
#  running/startup config, and saves each to a timestamped directory.
#
#  BACKUP LOCATION
#  ────────────────
#  /app/appteleporter-data/device-backup/bkp-YYYYMMDD-HHMMSS/
#      ├── core-sw-01_running.cfg
#      ├── core-sw-02_running.cfg
#      ├── access-sw-01_running.cfg
#      └── ...
#
#  SETUP
#  ─────
#  1. Add each device name below to DEVICE_LIST.
#     The name must match the credential Name in Settings → Credentials.
#
#  2. Ensure every device has a vault credential with Host, Username,
#     Password, and Port configured.
#
#  3. Add  netmiko>=4.3.0  to requirements.txt if not already present.
#
#  4. Enable  "config_backup_all"  in  Settings → Tools.
#
#  USAGE EXAMPLES (in chat)
#  ────────────────────────
#     "Take config backup of all devices"
#     "Backup all device configurations"
#     "Save running config of all switches"
#     "Take startup config backup of all devices"
#     "Back up both running and startup configs"
#
#  QUESTIONS?
#  ──────────
#  For additional help:  info@networkevolution.in
#
# ═══════════════════════════════════════════════════════════════════════════════

import os
from datetime import datetime

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


# ═══════════════════════════════════════════════════════════════════════════════
#  DEVICE LIST — Add or remove device names here
# ─────────────────────────────────────────────────────────────────────────────
#  Each entry must exactly match the credential Name saved in
#  Settings → Credentials.  The vault stores host, username, password, port.
#
#  Example:
#      DEVICE_LIST = [
#          "core-sw-01",
#          "core-sw-02",
#          "access-sw-01",
#          "access-sw-02",
#          "dist-sw-01",
#      ]
# ═══════════════════════════════════════════════════════════════════════════════

DEVICE_LIST = [
    "core-sw-01",
    "core-sw-02",
    "r01",
    # ← Add more device credential names here
]


# ── Paths ─────────────────────────────────────────────────────────────────────
BACKUP_BASE_DIR = "/app/backend/appteleporter-data/device-backup"


# ── Command map ───────────────────────────────────────────────────────────────
CONFIG_COMMANDS = {
    "running": "show running-config",
    "startup": "show startup-config",
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
        "read_timeout_override": 120,
    }


def _backup_single_device(
    device_name: str,
    backup_dir: str,
    backup_type: str,
) -> dict:
    """
    Back up a single device.  Returns a result dict with status and details.
    """
    result = {"device": device_name, "status": "success", "files": [], "error": None}

    # ── Vault lookup ──────────────────────────────────────────────────────
    creds = get_vault_cred(device_name)
    if creds is None:
        result["status"] = "skipped"
        result["error"]  = "No credential found in vault"
        return result

    host = creds.get("host")
    if not host:
        result["status"] = "skipped"
        result["error"]  = "Credential exists but Host/IP is empty"
        return result

    # ── Determine which configs to pull ───────────────────────────────────
    if backup_type == "both":
        types_to_backup = ["running", "startup"]
    else:
        types_to_backup = [backup_type]

    # ── Connect and save ──────────────────────────────────────────────────
    try:
        conn_params = _build_connection_params(creds)

        with ConnectHandler(**conn_params) as conn:
            for cfg_type in types_to_backup:
                command  = CONFIG_COMMANDS[cfg_type]
                output   = conn.send_command(command, read_timeout=120)

                filename = f"{device_name}_{cfg_type}.cfg"
                filepath = os.path.join(backup_dir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    # Write a header with metadata
                    f.write(f"! ═══════════════════════════════════════════\n")
                    f.write(f"! Device    : {device_name}\n")
                    f.write(f"! Host      : {host}\n")
                    f.write(f"! Config    : {cfg_type}\n")
                    f.write(f"! Backed up : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"! ═══════════════════════════════════════════\n\n")
                    f.write(output.strip())
                    f.write("\n")

                result["files"].append(filename)

    except NetMikoTimeoutException:
        result["status"] = "failed"
        result["error"]  = f"Connection timed out to {host}:{creds.get('port', 22)}"

    except NetMikoAuthenticationException:
        result["status"] = "failed"
        result["error"]  = f"Authentication failed for {host}"

    except Exception as e:
        result["status"] = "failed"
        result["error"]  = f"{type(e).__name__}: {e}"

    return result


def _format_summary(
    backup_dir: str,
    results: list[dict],
    duration_seconds: float,
) -> str:
    """Build a human-readable backup summary."""
    success = [r for r in results if r["status"] == "success"]
    failed  = [r for r in results if r["status"] == "failed"]
    skipped = [r for r in results if r["status"] == "skipped"]

    lines = []
    lines.append("━━━  CONFIGURATION BACKUP REPORT  ━━━\n")
    lines.append(f"📂 Backup path : {backup_dir}")
    lines.append(f"⏱  Duration    : {duration_seconds:.1f}s")
    lines.append(f"📊 Total       : {len(results)} device(s)\n")

    # ── Success ───────────────────────────────────────────────────────────
    if success:
        lines.append(f"✅ Successful  : {len(success)}")
        for r in success:
            files = ", ".join(r["files"])
            lines.append(f"    • {r['device']}  →  {files}")

    # ── Failed ────────────────────────────────────────────────────────────
    if failed:
        lines.append(f"\n❌ Failed      : {len(failed)}")
        for r in failed:
            lines.append(f"    • {r['device']}  —  {r['error']}")

    # ── Skipped ───────────────────────────────────────────────────────────
    if skipped:
        lines.append(f"\n⚠️  Skipped     : {len(skipped)}")
        for r in skipped:
            lines.append(f"    • {r['device']}  —  {r['error']}")

    lines.append(f"\n{'━' * 50}")

    if failed or skipped:
        lines.append(
            "\n💡 Tip: Check Settings → Credentials to verify vault "
            "entries for any failed or skipped devices."
        )

    return "\n".join(lines)


# ── Main entry point ─────────────────────────────────────────────────────────

def config_backup_all(backup_type: str = "running") -> str:
    """
    Back up the configuration of ALL devices in DEVICE_LIST.

    Parameters
    ----------
    backup_type : str, optional
        'running' (default), 'startup', or 'both'.
    """

    # ── Guard: netmiko installed? ─────────────────────────────────────────
    if not NETMIKO_AVAILABLE:
        return (
            "❌ Netmiko is not installed in the container.\n\n"
            "Add the following to requirements.txt and rebuild:\n"
            "    netmiko>=4.3.0"
        )

    # ── Guard: device list empty? ─────────────────────────────────────────
    if not DEVICE_LIST:
        return (
            "❌ No devices configured.\n\n"
            "Edit  plugins/config_backup/handler.py  and add device\n"
            "credential names to the DEVICE_LIST variable."
        )

    # ── Validate backup_type ──────────────────────────────────────────────
    backup_type = (backup_type or "running").strip().lower()
    if backup_type not in ("running", "startup", "both"):
        return (
            f"❌ Unknown backup type: '{backup_type}'.\n"
            f"Valid options: running, startup, both"
        )

    # ── Create timestamped backup directory ───────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = os.path.join(BACKUP_BASE_DIR, f"bkp-{timestamp}")

    try:
        os.makedirs(backup_dir, exist_ok=True)
    except OSError as e:
        return f"❌ Could not create backup directory:\n    {e}"

    # ── Run backups ───────────────────────────────────────────────────────
    start_time = datetime.now()
    results    = []

    for device_name in DEVICE_LIST:
        result = _backup_single_device(device_name, backup_dir, backup_type)
        results.append(result)

    duration = (datetime.now() - start_time).total_seconds()

    # ── Return summary ────────────────────────────────────────────────────
    return _format_summary(backup_dir, results, duration)

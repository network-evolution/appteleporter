# plugins/test-vault-access/handler.py
# ═══════════════════════════════════════════════════════════════════════════════
#
#  DEMO PLUGIN — How to read device credentials from the AppTelePorter Vault
#  ──────────────────────────────────────────────────────────────────────────
#
#  PURPOSE
#  ───────
#  This sample plugin demonstrates how to use core.vault_helpers.get_vault_cred()
#  to securely retrieve device credentials stored in the encrypted vault — without
#  hardcoding any passwords or IPs in your script.
#
#  STEP 1 — Create a test device in the Vault
#  ──────────────────────────────────────────
#  1. Open AppTelePorter in your browser.
#  2. Go to  Settings → Credentials  (the lock icon in the sidebar).
#  3. Click  "+ Add Credential"  and fill in:
#
#       Name     :  test-device          ← this is the lookup key used in code
#       Host/IP  :  192.168.1.100        ← set to your actual device IP
#       Username :  admin                ← set to your actual username
#       Password :  your-secret-pass     ← stored encrypted, never shown in logs
#       Port     :  22                   ← SSH port (or 23 for Telnet, 443 for API)
#
#  4. Click  Save.  The credential is now encrypted inside the vault.
#
#  STEP 2 — Enable this tool in the UI
#  ─────────────────────────────────────
#  1. Go to  Settings → Tools  in AppTelePorter.
#  2. Find  "test_vault_access"  in the plugin list.
#  3. Toggle it  ON  and click Save.
#
#  STEP 3 — Try it out
#  ────────────────────
#  In the chat window type something like:
#
#       "Test vault access for device test-device"
#          — or —
#       "Show me the credential details for test-device from the vault"
#
#  The assistant will call this tool, fetch the credential from the vault,
#  and return a summary.  The password is NEVER included in the response.
#
#  HOW TO REUSE THIS PATTERN IN YOUR OWN PLUGINS
#  ───────────────────────────────────────────────
#  Copy the import and the get_vault_cred() call into any handler.py:
#
#       from core.vault_helpers import get_vault_cred
#
#       creds = get_vault_cred("my-device-name")
#       if creds is None:
#           return "Credential not found in vault."
#
#       host     = creds.get("host")
#       username = creds.get("username")
#       password = creds.get("password")   # use this — don't log or return it
#       port     = creds.get("port", 22)
#
#  Then pass  host / username / password / port  directly to Netmiko, Paramiko,
#  NAPALM, requests, or any other library.  The user manages credentials through
#  the UI; your script stays clean and secret-free.
#
#  QUESTIONS?
#  ──────────
#  For additional help or clarifications reach out to:  info@networkevolution.in
#
# ═══════════════════════════════════════════════════════════════════════════════

from core.vault_helpers import get_vault_cred


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

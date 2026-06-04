# plugins/vlan_check/handler.py
# ──────────────────────────────────────────────────────────────
# Replace the mock data below with real Netmiko/NAPALM/Nornir
# calls to query your actual network devices.
#
# If you need netmiko: add a requirements.txt in this folder with:
#   netmiko==4.3.0
# ──────────────────────────────────────────────────────────────


def get_vlan_details(device: str) -> str:
    """Return the VLAN details for a specific switch."""

    # Fixed: Changed to a standard dictionary with device names as keys
    mock_data = {
        "switch1": ['VLAN10', 'VLAN11', 'VLAN12'],
        "switch2": ['VLAN20', 'VLAN21', 'VLAN22'],
        "switch3": ['VLAN30', 'VLAN31', 'VLAN32'],
    }

    # Normalize the input key
    key = device.strip().lower()
    vlans = mock_data.get(key)

    if not vlans:
        available_switches = ", ".join(mock_data.keys())
        return (
            f"No data found for switch: '{device}'. "
            f"Available switches: {available_switches}"
        )

    # Return the formatted VLAN list for the requested switch
    vlan_string = ", ".join(vlans)
    return f"VLANs for {device}: {vlan_string}"
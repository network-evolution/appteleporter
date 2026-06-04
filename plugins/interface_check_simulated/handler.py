# plugins/interface_check/handler.py
# ──────────────────────────────────────────────────────────────
# Replace the mock data below with real Netmiko/NAPALM/Nornir
# calls to query your actual network devices.
#
# If you need netmiko: add a requirements.txt in this folder with:
#   netmiko==4.3.0
# ──────────────────────────────────────────────────────────────


def get_interface_status(device: str, interface: str) -> str:
    """Return mock interface status for a network device."""

    mock_data = {
        ("router1", "gi0/0"): {"status": "up", "protocol": "up",   "speed": "1Gbps",  "errors": 0},
        ("router1", "gi0/1"): {"status": "up", "protocol": "down", "speed": "1Gbps",  "errors": 12},
        ("switch1", "eth0"):  {"status": "up", "protocol": "up",   "speed": "10Gbps", "errors": 0},
    }

    key = (device.strip().lower(), interface.strip().lower())
    data = mock_data.get(key)

    if not data:
        return (
            f"No data for {interface} on {device}. "
            f"Available: {[f'{d}:{i}' for d, i in mock_data.keys()]}"
        )

    return (
        f"Interface {interface} on {device}: "
        f"Status={data['status']}/{data['protocol']}, "
        f"Speed={data['speed']}, Errors={data['errors']}"
    )
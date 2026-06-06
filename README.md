<div align="center">

# AppTelePorter — Community Plugins & MCP Servers

**The self-hosted AI platform for network and infrastructure automation.**

[AppTelePorter Website](https://appteleporter.ai) &nbsp;·&nbsp;
[GitHub Repository](https://github.com/network-evolution/appteleporter) &nbsp;·&nbsp;
[Report an Issue](https://github.com/network-evolution/appteleporter/issues)

*Built by [Network Evolution](https://github.com/network-evolution)*

</div>

---

## Table of Contents

- [What is AppTelePorter?](#what-is-appteleporter)
- [What is Tool Studio?](#what-is-tool-studio)
- [How to Install AppTelePorter](#how-to-install-appteleporter)
  - [Step 1 — Pull the image](#step-1--pull-the-image)
  - [Step 2 — Create a local data directory](#step-2--create-a-local-data-directory)
  - [Step 3 — Start the container](#step-3--start-the-container)
    - [Linux](#linux)
    - [macOS (Docker Desktop)](#macos-docker-desktop)
    - [Windows (Docker Desktop)](#windows-docker-desktop)
  - [Step 4 — Open the UI and complete first-time setup](#step-4--open-the-ui-and-complete-first-time-setup)
    - [4a — Set the vault master password](#4a--set-the-vault-master-password)
    - [4b — Create the first admin user](#4b--create-the-first-admin-user)
    - [4c — Configure your LLM provider (Lite edition only)](#4c--configure-your-llm-provider-lite-edition-only)
- [This Repository](#this-repository)
- [Available Plugins](#available-plugins)
  - [Network — Cisco](#network--cisco)
  - [Simulated / Demo Tools](#simulated--demo-tools)
  - [Utilities](#utilities)
- [Available MCP Servers](#available-mcp-servers)
  - [Example & Demo Servers](#example--demo-servers)
- [How to Use These Tools in AppTelePorter](#how-to-use-these-tools-in-appteleporter)
  - [Option A — Copy into a running container](#option-a--copy-into-a-running-container)
  - [Option B — Place in your volume mount before starting](#option-b--place-in-your-volume-mount-before-starting)
  - [Option C — Use Tool Studio](#option-c--use-tool-studio-recommended-for-development)
  - [Installing Python dependencies](#installing-python-dependencies)
  - [Verify the tool loaded](#verify-the-tool-loaded)
- [How to Create Your Own Plugin](#how-to-create-your-own-plugin)
  - [Step 1 — Create the directory structure](#step-1--create-the-directory-structure)
  - [Step 2 — Write tool.yaml](#step-2--write-toolyaml)
  - [Step 3 — Write handler.py](#step-3--write-handlerpy)
  - [Using vault credentials](#using-vault-credentials)
  - [Start from the template](#start-from-the-template)
- [How to Create Your Own MCP Server](#how-to-create-your-own-mcp-server)
  - [Quickstart with FastMCP](#quickstart-with-fastmcp)
  - [Directory structure](#directory-structure)
  - [Register with AppTelePorter](#register-with-appteleporter)
  - [Accessing vault credentials from MCP servers](#accessing-vault-credentials-from-mcp-servers)
  - [Tool naming](#tool-naming)
  - [Start from the template](#start-from-the-template-1)
- [Why Build With AppTelePorter?](#why-build-with-appteleporter)
  - [No development environment setup needed](#no-development-environment-setup-needed)
  - [Install packages in seconds](#install-packages-in-seconds)
  - [Test against live infrastructure from the browser](#test-against-live-infrastructure-from-the-browser)
  - [The model handles parameter collection](#the-model-handles-parameter-collection)
  - [Credentials stay in the vault](#credentials-stay-in-the-vault)
  - [Easy to implement and run](#easy-to-implement-and-run)
- [Plugin vs. MCP Server — Quick Reference](#plugin-vs-mcp-server--quick-reference)
- [Contributing](#contributing)
- [What's Coming](#whats-coming)
- [Resources](#resources)
- [License](#license)

---

## What is AppTelePorter?

AppTelePorter is a **container-native AI platform** that gives network and DevOps teams a conversational AI agent capable of executing real infrastructure operations — with every credential encrypted in a vault that never leaves your server.

Think of it as **your own ChatAI App that can actually SSH into your switches, query your APIs, and run your automation scripts** — with credentials never exposed to any LLM, local or cloud.

It ships in two editions:

- **Lite edition** — bring your own LLM (OpenAI, Claude, or Gemini). The platform and **all credentials remain on your server**; conversation context — including tool results like device outputs — is sent to your chosen cloud LLM provider for inference only. Your credentials never leave the container. Choose this when you want frontier-model quality without hosting your own GPU. → [Docker Hub](https://hub.docker.com/r/networkevolution/appteleporter_lite/tags)
- **Max edition** — includes a bundled local AI model. Inference stays entirely inside your infrastructure. No prompt, no tool output, no data of any kind ever leaves your network. Runs fully offline. A GPU-enabled host is recommended for best performance, as the Max edition packages the AI model directly inside the container. → [Docker Hub](https://hub.docker.com/r/networkevolution/appteleporter_max/tags)


> **Important:** In both editions, your device credentials, passwords, and API keys are stored in an encrypted vault and are **never serialised into prompts or sent to any LLM**. Credentials are resolved locally at execution time — the handler function receives the actual value; the LLM (local or cloud) never sees it. Only the tool's *output* (e.g., a VLAN list) becomes part of the conversation.

**How it works in practice:**

1. You ask a question in plain English: *"What VLANs are configured on switch1?"*
2. AppTelePorter figures out which tool to run and presents an **approval card**.
3. You approve — credentials are resolved from the vault at execution time (never serialised into prompts), the tool executes, and the answer streams back.
4. **Max edition:** No data left your network. **Lite edition:** Tool execution stayed local; only the conversation context passed through your chosen LLM provider for synthesis — your credentials stayed in the vault the entire time.

**Key capabilities:**

| Feature | Description |
|---|---|
| **Private AI Chat** | Conversational interface backed by a local bundled model (Max edition) or your choice of OpenAI, Claude, or Gemini (Lite edition) |
| **Credentials Never Exposed** | Argon2id + Fernet encrypted vault; credentials are injected at execution time and **never sent to any LLM** — in either edition |
| **Plugin System** | Extend the AI with custom tools — just two files (`tool.yaml` + `handler.py`) dropped into a directory |
| **MCP Support** | Native MCP client over **stdio transport** — drop any Python MCP server into your volume mount and it auto-discovers. HTTP streamable MCP and TypeScript MCP support coming soon. |
| **Standard AI Model Compatible API** | Standard `/v1/chat/completions` API — compatible with any n8n workflow, LangChain app, or HTTP client that supports standard AI model APIs |
| **Tool Studio** | Browser-based IDE for creating, editing, and live-testing plugins without rebuilding the container |
| **Container-Native Deployment** | Single Docker container; one volume mount for persistence. Max edition runs fully offline; Lite edition requires only outbound LLM API access |

> For full product documentation, architecture details, and deployment guides, visit **[appteleporter.ai](https://appteleporter.ai)**.

---

## What is Tool Studio?

**Tool Studio** is AppTelePorter's built-in browser IDE for building and testing your own plugins and MCP servers — no SSH, no text editor, no container rebuild needed.

From your browser at `/tool-studio` you can:

- **Create a new plugin** — generates a skeleton `tool.yaml` + `handler.py` instantly
- **Edit any file** in the plugin or MCP server directory with a Monaco editor (the same editor that powers VS Code)
- **Install Python packages** with a single click — no container rebuild required
- **Run a tool live** and watch output stream in real time via the built-in console
- **Hot-reload** — changes take effect immediately; the model sees your updated tool on the next request
- **Test MCP servers** — trigger dependency installation and validate tool discovery without leaving the browser

**Why this matters:** The edit-run loop for a new automation tool drops from *"edit file → rebuild container → test"* to *"edit in browser → click Run."* For teams iterating against live infrastructure, this eliminates most of the friction.

---

## How to Install AppTelePorter

Getting AppTelePorter running is as simple as a single `docker run` command — no configuration files, no build steps, no dependencies to install on your host machine. The entire application — backend, frontend, AI runtime, vault, and Tool Studio — starts up in one container.

The examples below use the **Lite edition**. For the Max edition, replace `appteleporter_lite` with `appteleporter_max` in the image name.

| Edition | Docker Hub |
|---|---|
| Lite | [networkevolution/appteleporter_lite](https://hub.docker.com/r/networkevolution/appteleporter_lite/tags) |
| Max | [networkevolution/appteleporter_max](https://hub.docker.com/r/networkevolution/appteleporter_max/tags) |

---

### Step 1 — Pull the image

```bash
docker pull networkevolution/appteleporter_lite:latest
```

---

### Step 2 — Create a local data directory

Before starting the container, create a directory on your host machine. This is where AppTelePorter stores all its persistent data — plugins, MCP servers, the encrypted vault, chat history, and configuration.

> **No terminal required on Windows, macOS, or Linux desktop:** You can create this folder anywhere on your machine using your system's file manager — just create a new folder and name it `appteleporter-data`. The terminal commands below are an alternative if you prefer them.

```bash
# Linux / macOS
mkdir -p ~/appteleporter-data

# Windows (Command Prompt)
mkdir %USERPROFILE%\appteleporter-data

# Windows (PowerShell)
New-Item -ItemType Directory -Path "$env:USERPROFILE\appteleporter-data"
```

**Why this approach?** Mounting a local directory as the data volume means:
- Your data persists across container restarts and upgrades — just pull the new image and run with the same volume path
- You can browse, edit, or back up your plugins and MCP server files directly from your host file manager or any editor
- Upgrading AppTelePorter never touches your plugins, vault, or configuration

The Lite edition requires an external volume mount. The directory will be auto-populated with the correct folder structure on first run.

---

### Step 3 — Start the container

**Ports:**
- `3000` — AppTelePorter web UI (required)
- `1514/tcp` and `1514/udp` — Syslog receiver for Device Beacon (optional — only needed if you want AppTelePorter to passively receive syslog data from your network devices)

> **Device Beacon** is a built-in add-on that listens on port 1514 for syslog messages (RFC 3164/5424), extracts device identity and status, and maintains a live device inventory in the UI. If you do not need this feature, use the command without port 1514 — it can also be disabled at any time from **AppTelePorter UI → Settings → Add-On Settings → Device Beacon**.

---

#### Linux

**Without syslog receiver:**

```bash
docker run -d --name appteleporter \
  -v ~/appteleporter-data:/app/backend/appteleporter-data \
  -p 3000:3000 \
  --restart unless-stopped \
  networkevolution/appteleporter_lite:latest
```

**With syslog receiver (Device Beacon):**

```bash
docker run -d --name appteleporter \
  -v ~/appteleporter-data:/app/backend/appteleporter-data \
  -p 3000:3000 \
  -p 1514:1514/tcp \
  -p 1514:1514/udp \
  --restart unless-stopped \
  networkevolution/appteleporter_lite:latest
```

---

#### macOS (Docker Desktop)

**Option A — Docker Desktop UI:**

1. Open the **Docker Desktop** application on your Mac.
2. Click the **Search** bar at the top and type:
   ```
   networkevolution/appteleporter_lite
   ```
3. Select the image from the results and click **Pull** to download it.
4. Once the pull completes, find the image under **Images** in the left sidebar and click **Run**.
5. Expand **Optional settings** and fill in the following:
   - **Container name:** `appteleporter`
   - **Ports — Host port `3000` → Container port `3000`** *(required — this is the web UI)*
   - **Ports — Host port `1514` → Container port `1514`** *(optional — TCP and UDP, only if using Device Beacon syslog receiver)*
   - **Volumes — Host path:** select the directory you created in Step 2 (e.g. `/Users/yourname/appteleporter-data`)
   - **Volumes — Container path:** `/app/backend/appteleporter-data`
     > ⚠️ **Do not change the container path.** This is the internal path AppTelePorter expects and must be entered exactly as shown.
6. Click **Run**. The container will start and appear under **Containers**.

**Option B — Terminal:**

```bash
docker run -d --name appteleporter \
  -v ~/appteleporter-data:/app/backend/appteleporter-data \
  -p 3000:3000 \
  networkevolution/appteleporter_lite:latest
```

With syslog receiver (Device Beacon):

```bash
docker run -d --name appteleporter \
  -v ~/appteleporter-data:/app/backend/appteleporter-data \
  -p 3000:3000 \
  -p 1514:1514/tcp \
  -p 1514:1514/udp \
  networkevolution/appteleporter_lite:latest
```

---

#### Windows (Docker Desktop)

**Option A — Docker Desktop UI:**

1. Open the **Docker Desktop** application on Windows.
2. Click the **Search** bar at the top and type:
   ```
   networkevolution/appteleporter_lite
   ```
3. Select the image from the results and click **Pull** to download it.
4. Once the pull completes, find the image under **Images** in the left sidebar and click **Run**.
5. Expand **Optional settings** and fill in the following:
   - **Container name:** `appteleporter`
   - **Ports — Host port `3000` → Container port `3000`** *(required — this is the web UI)*
   - **Ports — Host port `1514` → Container port `1514`** *(optional — TCP and UDP, only if using Device Beacon syslog receiver)*
   - **Volumes — Host path:** select the directory you created in Step 2 (e.g. `C:\Users\yourname\appteleporter-data`)
   - **Volumes — Container path:** `/app/backend/appteleporter-data`
     > ⚠️ **Do not change the container path.** This is the internal path AppTelePorter expects and must be entered exactly as shown.
6. Click **Run**. The container will start and appear under **Containers**.

**Option B — Command line:**

*Command Prompt:*
```cmd
docker run -d --name appteleporter ^
  -v %USERPROFILE%\appteleporter-data:/app/backend/appteleporter-data ^
  -p 3000:3000 ^
  networkevolution/appteleporter_lite:latest
```

*PowerShell:*
```powershell
docker run -d --name appteleporter `
  -v "$env:USERPROFILE\appteleporter-data:/app/backend/appteleporter-data" `
  -p 3000:3000 `
  networkevolution/appteleporter_lite:latest
```

With syslog receiver (PowerShell):
```powershell
docker run -d --name appteleporter `
  -v "$env:USERPROFILE\appteleporter-data:/app/backend/appteleporter-data" `
  -p 3000:3000 `
  -p 1514:1514/tcp `
  -p 1514:1514/udp `
  networkevolution/appteleporter_lite:latest
```

> Docker Desktop must be running before using either option. WSL 2 backend is recommended for best performance on Windows.

---

### Step 4 — Open the UI and complete first-time setup

Once the container starts, open your browser and navigate to:

```
http://localhost:3000
```

> **SSL / HTTPS:** The standard container serves on HTTP. Custom SSL-enabled builds tailored to specific organisational requirements are available from Network Evolution — contact [appteleporter.ai](https://appteleporter.ai) for details.

---

#### 4a — Set the vault master password

The very first screen asks you to create the **vault master password**. This password encrypts everything AppTelePorter stores, including:

- All device and API credentials (SSH usernames, passwords, API keys, host addresses)
- User accounts and access tokens
- LLM provider API keys and model settings
- Application session signing secrets

> **⚠️ This password cannot be recovered — ever. Store it somewhere safe.**
>
> AppTelePorter never stores your master password on disk, in a database, or anywhere else. Internally, the vault works like this: your password is run through Argon2id (a memory-hard key derivation function) to produce a 256-bit encryption key. That key is used to encrypt the entire vault as a single AES-encrypted blob — and then the key is discarded. Only a bcrypt hash of the password is kept inside the vault itself, solely for verifying the password at unlock time.
>
> **The consequence:** there is no password reset, no recovery email, and no backdoor. If you lose the master password, the encrypted vault blob cannot be decrypted — all stored credentials, API keys, and user accounts will need to be recreated from scratch. Write it down and keep it safe.

---

#### 4b — Create the first admin user

After setting the vault password, you will be prompted to create the **first admin user** — the account you will use to log in to the AppTelePorter interface. Set a username and a strong password. Additional users can be added later from **Settings → Users**.

---

#### 4c — Configure your LLM provider (Lite edition only)

If you are running the **Lite edition**, the AI cannot process any requests until you connect it to an LLM provider. Go to:

**Settings → LLM Settings**

Select the model provider you want to use:

- **OpenAI (ChatGPT)** — enter your OpenAI API key
- **Google Gemini** — enter your Google AI Studio API key
- **Anthropic Claude** — enter your Anthropic API key

After entering the API key, click **Test Connection** to verify it is working. Once confirmed, AppTelePorter is ready to use.

> If you need support for a specific model or provider not listed, reach out to **info@networkevolution.in** — we will treat it as a feature enhancement request.

The Max edition has a bundled local model and does not require this step.

---

## This Repository

This repository is the **community hub** for AppTelePorter plugins and MCP servers — a place to share, discover, and collaborate on tools that extend AppTelePorter's capabilities.

```
appteleporter/
├── plugins/                  # Ready-to-use tool plugins
│   ├── cisco_interface_details/
│   ├── cisco_switch_check/
│   ├── config_backup/
│   ├── interface_check_simulated/
│   ├── vlan_check_simulated/
│   └── test-vault-access/
│
├── mcp-servers/              # Ready-to-use MCP servers
│   ├── example-dns-ping/
│   ├── example-ip-time/
│   └── mcp-test-vault-access/
│
└── docs/                     # Specifications, templates, and contributing guides
    ├── tools-ecosystem/      # Plugin spec, contributing guide, templates
    └── mcp-ecosystem/        # MCP server spec, contributing guide, templates
```

---

## Available Plugins

These plugins are ready to drop into your AppTelePorter instance. Each one is a self-contained directory with `tool.yaml` and `handler.py`. Example scripts include **detailed inline comments** explaining every step of the logic so you can understand and adapt them quickly.

### Network — Cisco

| Plugin | Tool Name | Description | Directory |
|---|---|---|---|
| Cisco Interface Diagnostics | `cisco_interface_detail` | SSH into a Cisco IOS device and run a comprehensive per-interface diagnostic: counters, errors, CRC, speed/duplex, traffic rates. Accepts full or short interface names (`Gi0/0`, `Fa0/1`, `Lo0`). | [cisco_interface_details](./plugins/cisco_interface_details/) |
| Cisco Switch Health Check | `cisco_switch_check` | Multi-mode Cisco switch checker via SSH. Supports: VLANs, interfaces, version, ARP table, MAC address table, inventory, and combined health overview. | [cisco_switch_check](./plugins/cisco_switch_check/) |
| Config Backup (All Devices) | `config_backup_all` | Bulk running/startup configuration backup across all devices registered in the vault. Saves timestamped backups to the server. | [config_backup](./plugins/config_backup/) |

### Simulated / Demo Tools

These tools use simulated data — ideal for learning the plugin structure, testing the Tool Studio, and validating your AppTelePorter setup before connecting real devices.

| Plugin | Tool Name | Description | Directory |
|---|---|---|---|
| Interface Status (Simulated) | `get_interface_status` | Returns simulated interface up/down status for a given device and interface. Great as a starter template. | [interface_check_simulated](./plugins/interface_check_simulated/) |
| VLAN Details (Simulated) | `get_vlan_details` | Returns a simulated VLAN list for a named switch. The classic "hello world" tool for AppTelePorter. | [vlan_check_simulated](./plugins/vlan_check_simulated/) |

### Utilities

| Plugin | Tool Name | Description | Directory |
|---|---|---|---|
| Vault Access Test | `test_vault_access` | Verifies that a named credential exists in the vault and displays its fields (host, username, port). Password is always masked. Use this to confirm vault setup before writing tools that depend on credentials. | [test-vault-access](./plugins/test-vault-access/) |

> **Note:** A README inside each plugin directory is helpful for others but not required. Documenting what the tool does, its prerequisites, and any vault credential format it expects is good practice.

---

## Available MCP Servers

MCP (Model Context Protocol) servers allow richer integrations — long-running processes, protocol-native clients, and multi-tool servers. AppTelePorter auto-discovers and launches them; their tools appear in the same chat interface as native plugins.

MCP tool names are prefixed with the server name: `{server-name}__{tool-name}`.

> **Current transport support:** AppTelePorter's MCP client currently supports **stdio transport** (Python-based MCP servers launched as subprocesses). Support for **HTTP streamable MCP servers** and **TypeScript MCP servers** is actively in development and will be available in a future release.

### Example & Demo Servers

| Server | Registered As | Tools | Description | Directory |
|---|---|---|---|---|
| DNS & Ping | `example-dns-ping` | `ping_host`, `dns_lookup` | Basic network connectivity tools: ICMP ping and DNS hostname resolution. | [example-dns-ping](./mcp-servers/example-dns-ping/) |
| IP & Time | `example-ip-time` | `public_ip`, `current_time` | Returns the container's public IP address and the current date/time. | [example-ip-time](./mcp-servers/example-ip-time/) |
| Vault Access Test | `mcp-test-vault-access` | `test_vault_access` | Demonstrates how MCP servers read credentials from the vault via `get_vault_cred()`. Use to verify vault access from an MCP server. | [mcp-test-vault-access](./mcp-servers/mcp-test-vault-access/) |

> More plugins and MCP servers are being added regularly. Star this repository to stay updated.

---

## How to Use These Tools in AppTelePorter

### Option A — Copy into a running container

```bash
# Copy a plugin directory into the container
docker cp ./plugins/cisco_switch_check \
  appteleporter:/app/backend/appteleporter-data/plugins/cisco_switch_check

# Reload tools without restarting the container
curl -X GET http://localhost:3000/api/tools/reload \
  -H "Authorization: Bearer <your-api-key>"
```

### Option B — Place in your volume mount before starting

```bash
# Copy to your local appteleporter-data directory
cp -r ./plugins/cisco_switch_check \
  ./appteleporter-data/plugins/cisco_switch_check

# Tools are discovered automatically on next container start
docker run --name appteleporter \
  -v ./appteleporter-data:/app/backend/appteleporter-data \
  -p 3000:3000 \
  appteleporter:latest
```

### Option C — Use Tool Studio (recommended for development)

1. Open AppTelePorter in your browser and navigate to **Tool Studio**.
2. Click **"New Plugin"** — a skeleton `tool.yaml` and `handler.py` are created instantly.
3. Paste in (or type) the plugin code from this repository.
4. Click **"Run"** to test immediately — output streams live in the console.
5. The tool is available in chat on the next message.

### Installing Python dependencies

If a plugin requires packages (e.g., `netmiko`, `paramiko`, `requests`):

- **Via Tool Studio:** Open the plugin directory, click **"Install Deps"** — packages are installed instantly, no container rebuild needed.
- **Via requirements.txt:** Add a `requirements.txt` file to the plugin directory. AppTelePorter installs it automatically on container startup.

---

## How to Create Your Own Plugin

A plugin is just **two files** in a directory. If you can write a Python function, you can write an AppTelePorter tool.

### Step 1 — Create the directory structure

```
my_tool/
├── tool.yaml         # Required — schema and description
├── handler.py        # Required — your Python function
└── requirements.txt  # Optional — pip dependencies
```

### Step 2 — Write `tool.yaml`

```yaml
name: check_device_reachability

description: >
  Check whether a network device is reachable by sending ICMP ping requests.
  Use when the user asks if a device is up, reachable, online, or responding to ping.
  Provide the device hostname or IP address, e.g. 'switch1' or '192.168.1.1'.

parameters:
  properties:
    device:
      type: string
      description: "Device hostname or IP address, e.g. 'switch1' or '10.0.0.1'"
    count:
      type: integer
      description: "Number of ping packets to send (default: 4)"
  required:
    - device
```

> **Write the description for the model, not for humans.** Be specific about *when* to use the tool and what the parameters look like — this is what the AI reads to decide whether to call your tool.

### Step 3 — Write `handler.py`

```python
import subprocess

def check_device_reachability(device: str, count: int = 4) -> str:
    # Function name must match the `name` field in tool.yaml.
    # Always return a string. Never raise an uncaught exception.

    if not device:
        return "Error: device parameter is required."

    count = max(1, min(int(count), 10))
    cmd = ["ping", "-c", str(count), "-W", "2", device]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return f"{device} is reachable."
        else:
            return f"{device} is NOT reachable."
    except Exception as e:
        return f"Error checking {device}: {e}"
```

**Key rules for handler.py:**
- The function name must match the `name` field in `tool.yaml` (or use `handle` / `run` as fallbacks).
- Always return a **string** — the model reads your return value to synthesise its answer.
- **Never let an exception escape the handler** — catch everything and return a descriptive error string.
- Parameters must match `tool.yaml` property names. Optional parameters need Python default values.

### Using vault credentials

To access device credentials stored in AppTelePorter's vault:

```python
from core.vault_helpers import get_vault_cred

def my_tool(device_name: str) -> str:
    creds = get_vault_cred(device_name)
    if creds is None:
        return f"No credential found for '{device_name}'. Add it in Settings → Credentials."

    host     = creds.get("host")
    username = creds.get("username")
    password = creds.get("password")
    # ... use credentials to connect
```

Credentials are stored in **Settings → Credentials** in the AppTelePorter UI. They are encrypted in the vault and injected at execution time — they never appear in chat history or prompts.

### Start from the template

Copy the starter template with full inline documentation:

```
docs/tools-ecosystem/templates/example-tool/
```

See [`docs/tools-ecosystem/TOOL_SPEC.md`](./docs/tools-ecosystem/TOOL_SPEC.md) for the complete plugin contract.

---

## How to Create Your Own MCP Server

Use an MCP server instead of a plain plugin when you need:
- Persistent state or long-lived connections between calls (SSH pools, streaming APIs)
- Multiple related tools that share initialisation cost
- Integration with an existing MCP-compliant server from the community

> **Transport note:** The current MCP client supports **stdio transport** (Python servers launched as subprocesses). HTTP streamable MCP and TypeScript MCP server support is coming in a future release.

### Quickstart with FastMCP

```python
# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-network-server")

@mcp.tool()
def check_bgp_neighbors(device: str) -> str:
    """
    Check BGP neighbor status on a network device.
    Use when the user asks about BGP peers, neighbors, or routing adjacencies.
    """
    # Your implementation here
    return f"BGP neighbors for {device}: ..."

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Directory structure

```
my-mcp-server/
├── server.py         # Your MCP server implementation
├── setup.yaml        # Optional — custom launch command and environment
├── pyproject.toml    # Optional — for uv-managed servers with dependencies
└── requirements.txt  # Optional — pip dependencies
```

### Register with AppTelePorter

Add an entry to `mcp_config.json` (visible in the Tool Studio workspace panel):

```json
{
  "mcpServers": {
    "my-network-server": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/app/backend/appteleporter-data/mcp_servers/my-network-server",
      "env": {}
    }
  }
}
```

Save the file, then click **"Load Changes to ATP"** in Tool Studio — your MCP tools appear in the tool list immediately.

### Accessing vault credentials from MCP servers

```python
from core.mcp_vault import get_vault_cred

# Reads from APPTELEPORTER_VAULT_CREDS env var injected by AppTelePorter
password = get_vault_cred("my_device", "password")
host     = get_vault_cred("my_device", "host")
```

### Tool naming

Your tool `check_bgp_neighbors` in server `my-network-server` is registered as:

```
my-network-server__check_bgp_neighbors
```

The prefix is added automatically — you work with the un-prefixed name in your server code.

### Start from the template

```
docs/mcp-ecosystem/templates/example-mcp-server/
```

See [`docs/mcp-ecosystem/MCP_SPEC.md`](./docs/mcp-ecosystem/MCP_SPEC.md) for the complete MCP server contract.

---

## Why Build With AppTelePorter?

### No development environment setup needed

Plugins run directly inside the AppTelePorter container. There is no local Python environment to configure, no Docker build step, and no deployment pipeline to manage. Write your tool, drop it in the directory, and it is live.

### Install packages in seconds

Need `netmiko`, `paramiko`, `requests`, or any other library? Add a `requirements.txt` to your plugin directory, or click **"Install Deps"** in Tool Studio. Packages are installed instantly into the running container — no rebuild, no restart.

### Test against live infrastructure from the browser

Tool Studio's built-in run console lets you execute your tool with real parameters against real devices while you are still writing it. See the raw output, iterate on the logic, and confirm it works — all without leaving the browser.

### The model handles parameter collection

You define *what* parameters your tool needs. The AI figures out *which values* to use from the user's question. You do not write argument parsing or user prompts — just the business logic.

### Credentials stay in the vault

Device credentials are stored once in the vault. Every tool that needs them calls `get_vault_cred()` — there is no credential management in individual tools, no hardcoded passwords, and no risk of secrets appearing in logs or chat history.

### Easy to implement and run

The entire plugin surface is two files and a handful of rules:
- `name` in `tool.yaml` matches the Python function name
- Function returns a string
- Exceptions are caught inside the handler

That is it. The example scripts in this repository have **detailed inline comments** explaining every part of the logic so you can adapt them for your own use cases in minutes.

---

## Plugin vs. MCP Server — Quick Reference

| Use Case | Recommended Approach |
|---|---|
| Simple stateless operation (ping, query, lookup) | **Plugin** (`tool.yaml` + `handler.py`) |
| Needs device credentials from the vault | **Plugin** — use `get_vault_cred()` |
| Multiple related tools sharing a connection pool | **MCP Server** |
| Long-lived SSH or API session between calls | **MCP Server** |
| Wrapping an existing MCP-compliant server | **MCP Server** |
| Fastest authoring loop | **Plugin** via Tool Studio |

---

## Contributing

Contributions are welcome. If you have built a plugin or MCP server that others might find useful, submit a pull request.

**Before submitting:**
- Read [`docs/tools-ecosystem/CONTRIBUTING.md`](./docs/tools-ecosystem/CONTRIBUTING.md) for plugins
- Read [`docs/mcp-ecosystem/CONTRIBUTING.md`](./docs/mcp-ecosystem/CONTRIBUTING.md) for MCP servers
- Review [`docs/tools-ecosystem/SECURITY.md`](./docs/tools-ecosystem/SECURITY.md) — especially if your tool handles credentials or executes commands

A README for your plugin or MCP server is **not mandatory**, but it helps others understand prerequisites, vault credential formats, and usage examples. Even a short one is appreciated.

---

## What's Coming

This repository is growing. Planned additions include:

- **Network automation tools:** BGP diagnostics, OSPF neighbour checks, route table queries, ACL audits
- **Cloud integrations:** AWS, Azure, GCP resource queries via API
- **Monitoring integrations:** Prometheus metrics, Grafana annotations, Zabbix host status
- **Infrastructure integrations:** NetBox, Nautobot, ServiceNow CMDB lookups
- **Security tools:** Certificate expiry checks, port scan summaries, CVE lookups
- **More MCP servers:** Protocol-native clients, multi-tool servers for complex workflows

Watch or star this repository to be notified of new additions.

---

## Resources

| Resource | Link |
|---|---|
| AppTelePorter Website | [appteleporter.ai](https://appteleporter.ai) |
| GitHub | [github.com/network-evolution/appteleporter](https://github.com/network-evolution/appteleporter) |
| Plugin Specification | [docs/tools-ecosystem/TOOL_SPEC.md](./docs/tools-ecosystem/TOOL_SPEC.md) |
| MCP Server Specification | [docs/mcp-ecosystem/MCP_SPEC.md](./docs/mcp-ecosystem/MCP_SPEC.md) |
| Plugin Template | [docs/tools-ecosystem/templates/example-tool/](./docs/tools-ecosystem/templates/example-tool/) |
| MCP Server Template | [docs/mcp-ecosystem/templates/example-mcp-server/](./docs/mcp-ecosystem/templates/example-mcp-server/) |
| Plugin Catalog | [docs/tools-ecosystem/catalog.md](./docs/tools-ecosystem/catalog.md) |
| MCP Server Catalog | [docs/mcp-ecosystem/catalog.md](./docs/mcp-ecosystem/catalog.md) |

---

## License

[Apache 2.0](./LICENSE) — see the LICENSE file for details.

---

<div align="center">

Built with care by **[Network Evolution](https://github.com/network-evolution)**

*Your network. Your AI. Your data.*

</div>

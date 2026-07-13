# Coastal Alpine Core

![coastal-alpine-core Banner](assets/social_preview.png)

**Coastal Alpine Tech Limited** — pre-seed startup, New Plymouth, Taranaki, Aotearoa New Zealand.
*Edge AI | Sovereign Systems | Practical Intelligence*


Shared python utility package designed for Taranaki-based Coastal Alpine Tech Edge systems. It handles local offline LLM wrapping, security checks, and hardware telemetry tracking.

**Canonical hardware target:** Raspberry Pi 5 **(16GB)** with **Hailo-10H NPU** (40 TOPS AI Accelerator / AI HAT+ 2).

---

## Architecture Overview

> **Diagrams:** Architecture images and Mermaid maps describe the **target product architecture** for this pre-seed stack. They are engineering design maps — not claims of large-scale commercial fleet deployment.

Coastal-Alpine-Core is the **shared edge SDK** used by every portal: offline LLM client, input/security guards, and hardware telemetry for **RPi 5 16GB + Hailo-10H** deployments.

![Coastal-Alpine-Core architecture — liquid glass overview](assets/architecture_overview.png)

### System map

```mermaid
%%{init: {
  "theme": "dark",
  "themeVariables": {
    "fontSize": "15px",
    "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
    "primaryColor": "#0ea5e9",
    "primaryTextColor": "#f8fafc",
    "primaryBorderColor": "#38bdf8",
    "lineColor": "#67e8f9",
    "secondaryColor": "#1e293b",
    "tertiaryColor": "#0f172a",
    "clusterBkg": "#0b1220cc",
    "clusterBorder": "#38bdf880",
    "titleColor": "#e2e8f0"
  },
  "flowchart": {
    "nodeSpacing": 36,
    "rankSpacing": 44,
    "padding": 18,
    "htmlLabels": true,
    "curve": "basis",
    "useMaxWidth": true
  }
}}%%
flowchart TB

    classDef edge fill:#0c4a6e,stroke:#38bdf8,stroke-width:2px,color:#f0f9ff
    classDef core fill:#134e4a,stroke:#2dd4bf,stroke-width:2px,color:#f0fdfa
    classDef ai fill:#3b0764,stroke:#e879f9,stroke-width:2px,color:#fdf4ff
    classDef app fill:#1e1b4b,stroke:#c4b5fd,stroke-width:2px,color:#eef2ff
    classDef host fill:#052e16,stroke:#4ade80,stroke-width:2px,color:#f0fdf4
    classDef orch fill:#312e81,stroke:#a5b4fc,stroke-width:2px,color:#eef2ff

    subgraph CONSUMERS["Hybrid consumers"]
        W["Weaver<br/>LangGraph multi-tenant"]
        P["Domain portals<br/>Aqua · Soil · Blue · Sting"]
        A["Aether companion<br/>skills · HITL · computer use"]
        S["coastal-alpine-stack<br/>compose / K3s monorepo"]
    end

    subgraph SDK["coastal_alpine_core package"]
        G["SecurityGuard / input_guard_check"]
        T["TelemetryTracker"]
        C["SovereignOllamaClient"]
        FW["DataFlywheel"]
        PC["portal_core<br/>AIAgent · MQTT · AV · Hardware"]
    end

    subgraph AI["Local AI"]
        O["Ollama<br/>Gemma / Qwen class"]
        HAI["Hailo-10H NPU<br/>edge vision optional"]
    end

    subgraph HOSTS["Dual-platform hosts"]
        WIN["Windows 10/11<br/>install.ps1 · venv"]
        LIN["Linux / RPi OS<br/>install.sh · venv / uv"]
        RPI["RPi 5 16GB + Hailo-10H<br/>production edge"]
    end

    W & P & A & S --> G & T & C & FW & PC
    C --> O
    PC --> HAI
    T --> RPI
    SDK -.-> HOSTS

    class W,P,A,S app
    class G,T,C,FW,PC core
    class O,HAI ai
    class WIN,LIN,RPI host
```

| Layer | Components | Role |
| :--- | :--- | :--- |
| **Security** | SecurityGuard / input_guard_check | Injection / scope screening |
| **LLM** | SovereignOllamaClient | Offline-resilient chat |
| **Telemetry** | TelemetryTracker | Joules · latency · load |
| **Flywheel** | DataFlywheel | Trajectories · golden sets |
| **Portal kit** | portal_core | MQTT · AV · hardware loop |
| **Consumers** | Weaver · portals · Aether · stack | One SDK, hybridised stack |
| **Hosts** | Windows · Linux · RPi 5 | Dev on Win/Linux; deploy on edge |

*Full detail: [ARCHITECTURE.md](./ARCHITECTURE.md) · [DEVELOPER_SETUP.md](./DEVELOPER_SETUP.md)*


## Key Features

1. **SovereignOllamaClient (`models.py`)**: A robust connection wrapper for local offline Ollama SLM deployments. Handles network dropouts and model loads with automated retries and exponential backoff, falling back to local deterministic responses when fully disconnected.
2. **Security & Input Guard (`security.py`)**: Scans incoming prompts for potential prompt injections, local file access attempts, or common injection patterns. It also enforces strict tenant scoping context mismatch flags.
3. **Telemetry & Performance (`telemetry.py`)**: Performance and hardware energy-efficiency tracking specifically designed for edge-native devices (e.g. Raspberry Pi 5 under active load, Hailo NPU draws). Estimates active power draw in Joules.

---

## Installation

**Platforms:** Windows 10/11 · Linux (Ubuntu/Debian/RPi OS) · macOS · production edge on **RPi 5 16GB + Hailo-10H**.

### One-line install (recommended)

<details open>
<summary><strong>🐧 Linux / macOS</strong></summary>

```bash
curl -fsSL https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.sh | bash
```

</details>

<details>
<summary><strong>🪟 Windows (PowerShell)</strong></summary>

```powershell
irm https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.ps1 | iex
```

> **Note:** If script execution is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

</details>

### Manual install

<details open>
<summary><strong>🐧 Linux / macOS (Bash)</strong></summary>

```bash
git clone https://github.com/fivepanelhat/Coastal-Alpine-Core.git
cd Coastal-Alpine-Core
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
# optional (uv):
# uv sync && uv run pytest
```

**System packages (Debian/Ubuntu/RPi OS):**

```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv python3-pip git build-essential
```

</details>

<details>
<summary><strong>🪟 Windows (PowerShell)</strong></summary>

```powershell
git clone https://github.com/fivepanelhat/Coastal-Alpine-Core.git
cd Coastal-Alpine-Core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

**Prerequisites:** [Python 3.10+](https://www.python.org/downloads/) with “Add Python to PATH”, [Git for Windows](https://git-scm.com/).

</details>

### Pin from GitHub (portals / CI)

Use a **tagged release** only (never `@main`):

```bash
pip install "git+https://github.com/fivepanelhat/Coastal-Alpine-Core.git@v0.5.4"
```

---

## Quick Start Code Example

```python
from coastal_alpine_core import SovereignOllamaClient, input_guard_check, TelemetryTracker

# Initialize client
client = SovereignOllamaClient(default_model="gemma4:e4b")

# Check security
prompt = "Format C:\\"
is_safe = input_guard_check(prompt)
print(f"Is Prompt Safe? {is_safe}")  # Expected: False (Security alert triggered)

# Measure edge execution performance
measurement = TelemetryTracker.measure_latency("gemma_generation")
response = client.generate("Evaluate crop health status: OK")
metrics = TelemetryTracker.complete_measurement(measurement, token_count=len(response.get("response", "").split()))
print(metrics)
```

---

*Built with focus on data sovereignty and edge intelligence.*  
**Coastal Alpine Tech Limited — New Plymouth, Taranaki, New Zealand.**

---

## Project badges

Status badges for this repository (CI, security, license, and stack metadata):

[![License](https://img.shields.io/badge/License-Proprietary--Commercial-blue?style=flat-square)](LICENSE)  
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)](https://www.python.org/)  
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20RPi-0078D6?style=flat-square)]()  
[![Install](https://img.shields.io/badge/Install-install.sh%20%7C%20install.ps1-0ea5e9?style=flat-square)]()  
[![Hardware Target](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%2016GB-C11A5B?style=flat-square&logo=raspberry-pi&logoColor=white)]()  
[![NPU Acceleration](https://img.shields.io/badge/NPU-Hailo--10H%20Accelerated-005A9C?style=flat-square)]()  
[![Sovereignty](https://img.shields.io/badge/Sovereignty-NZ%20Data%20Bound-00247D?style=flat-square)]()  
[![CI](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/ci-scan.yml/badge.svg?branch=main)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/ci-scan.yml)  
[![SecOps](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Coastal-Alpine-Core/secops.yml?branch=main&label=SecOps&style=flat-square&color=success)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/secops.yml)  
[![RedTeam](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Coastal-Alpine-Core/redteam.yml?branch=main&label=RedTeam&style=flat-square&color=critical)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/redteam.yml)  
[![Dependabot](https://img.shields.io/badge/Dependencies-Monitored-brightgreen?style=flat-square&logo=dependabot)]()  
[![Sustainability](https://img.shields.io/badge/EECA%20NZ-Carbon%20Tracked-green?style=flat-square)]()

# Coastal Alpine Core

![coastal-alpine-core Banner](assets/social_preview.png)

**Coastal Alpine Tech Limited**  
*Edge AI | Sovereign Systems | Practical Intelligence*


Shared python utility package designed for Taranaki-based Coastal Alpine Tech Edge systems. It handles local offline LLM wrapping, security checks, and hardware telemetry tracking.

**Canonical hardware target:** Raspberry Pi 5 **(16GB)** with **Hailo-10H NPU** (40 TOPS AI Accelerator / AI HAT+ 2).

---

## Architecture Overview

Coastal-Alpine-Core is the **shared edge SDK** used by every portal: offline LLM client, input/security guards, and hardware telemetry for **RPi 5 16GB + Hailo-10H** deployments.

![Coastal-Alpine-Core architecture — liquid glass overview](assets/architecture_overview.png)

### System map

```mermaid
%%{init: {
  "theme": "dark",
  "themeVariables": {
    "fontSize": "16px",
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
    "nodeSpacing": 40,
    "rankSpacing": 48,
    "padding": 20,
    "htmlLabels": true,
    "curve": "basis"
  }
}}%%
flowchart TB

    classDef sense fill:#052e16,stroke:#4ade80,stroke-width:2px,color:#f0fdf4
    classDef edge fill:#0c4a6e,stroke:#38bdf8,stroke-width:2px,color:#f0f9ff
    classDef core fill:#134e4a,stroke:#2dd4bf,stroke-width:2px,color:#f0fdfa
    classDef act fill:#422006,stroke:#fbbf24,stroke-width:2px,color:#fffbeb
    classDef store fill:#1e1b4b,stroke:#a5b4fc,stroke-width:2px,color:#eef2ff
    classDef ai fill:#3b0764,stroke:#e879f9,stroke-width:2px,color:#fdf4ff
    classDef app fill:#1e1b4b,stroke:#c4b5fd,stroke-width:2px,color:#eef2ff

    P["Portals<br/>Weaver · Aqua · Soil · Blue · Sting"] --> G["input_guard_check<br/>prompt safety"]
    P --> T["TelemetryTracker<br/>power · latency"]
    P --> C["SovereignOllamaClient<br/>retries · backoff"]
    C --> O["Local Ollama<br/>Gemma 4 e4b"]
    T --> H["Edge host metrics<br/>RPi 5 + NPU draw"]

    subgraph SDK["coastal_alpine_core package"]
        G
        T
        C
    end

    class P app
    class G,T,C core
    class O ai
    class H edge
```

| Layer | Components | Role |
| :--- | :--- | :--- |
| **Security** | input_guard_check | Injection / scope screening |
| **LLM** | SovereignOllamaClient | Offline-resilient chat |
| **Telemetry** | TelemetryTracker | Joules · latency · load |
| **Consumers** | All domain portals | One SDK, many agents |

*Full detail: [ARCHITECTURE.md](./ARCHITECTURE.md)*


## Key Features

1. **SovereignOllamaClient (`models.py`)**: A robust connection wrapper for local offline Ollama SLM deployments. Handles network dropouts and model loads with automated retries and exponential backoff, falling back to local deterministic responses when fully disconnected.
2. **Security & Input Guard (`security.py`)**: Scans incoming prompts for potential prompt injections, local file access attempts, or common injection patterns. It also enforces strict tenant scoping context mismatch flags.
3. **Telemetry & Performance (`telemetry.py`)**: Performance and hardware energy-efficiency tracking specifically designed for edge-native devices (e.g. Raspberry Pi 5 under active load, Hailo NPU draws). Estimates active power draw in Joules.

---

## Installation

First, set up a Python virtual environment:

<details open>
<summary><strong>🐧 Linux / macOS (Bash)</strong></summary>

```bash
python3 -m venv venv
source venv/bin/activate
```

</details>

<details>
<summary><strong>🪟 Windows (PowerShell)</strong></summary>

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Note:** If you receive an execution policy error, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

</details>

Then install the library (these commands work on all platforms):

To install as an editable local package:
```bash
pip install -e .
```

To install directly from GitHub (as used across all stack portals):
```bash
pip install git+https://github.com/fivepanelhat/coastal-alpine-core.git@v0.2.0
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
[![Hardware Target](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%2016GB-C11A5B?style=flat-square&logo=raspberry-pi&logoColor=white)]()  
[![NPU Acceleration](https://img.shields.io/badge/NPU-Hailo--10H%20Accelerated-005A9C?style=flat-square)]()  
[![Sovereignty](https://img.shields.io/badge/Sovereignty-NZ%20Data%20Bound-00247D?style=flat-square)]()  
[![CI](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/ci-scan.yml/badge.svg?branch=main)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/ci-scan.yml)  
[![SecOps](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Coastal-Alpine-Core/secops.yml?branch=main&label=SecOps&style=flat-square&color=success)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/secops.yml)  
[![RedTeam](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Coastal-Alpine-Core/redteam.yml?branch=main&label=RedTeam&style=flat-square&color=critical)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/redteam.yml)  
[![Dependabot](https://img.shields.io/badge/Dependencies-Monitored-brightgreen?style=flat-square&logo=dependabot)]()  
[![Sustainability](https://img.shields.io/badge/EECA%20NZ-Carbon%20Tracked-green?style=flat-square)]()

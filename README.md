# Coastal Alpine Core

<!-- BEGIN CAT_CONGRUENCE_SNIPPET -->
## Coastal Alpine Tech portfolio

[![Stage](https://img.shields.io/badge/Stage-Pre--seed-8B5CF6)](https://github.com/fivepanelhat/fivepanelhat)
[![Hybrid](https://img.shields.io/badge/Hybrid-Edge%20%2B%20Multi--model-0f766e)](https://github.com/fivepanelhat/fivepanelhat)
[![HITL](https://img.shields.io/badge/HITL-Draft%2FPrepare%20only-dc2626)](./.github/agent-fleet/AGENTS.md)
[![Te Mana Raraunga](https://img.shields.io/badge/Te%20Mana%20Raraunga-Aligned-0f766e)](https://github.com/fivepanelhat/fivepanelhat)

**Part of the [Kiwi Edge AI Stack](https://github.com/fivepanelhat/fivepanelhat)** · Founder OS: [NZ-Start-Up](https://github.com/fivepanelhat/NZ-Start-Up) · Agent policy: [`.github/agent-fleet/`](./.github/agent-fleet/)

> Sovereign hybrid edge AI for NZ farms & founders — local-first + multi-model, Te Mana Raraunga aligned — collaborating with Venture Taranaki, startups.com investors & Kotahitanga Investment Fund (HITL + cultural advisory for formal approaches).

**Agents inform, draft, prepare, monitor, and remind. Humans advise, sign, file, send, and pay.**  
Anti-hallucination policy: [`.github/agent-fleet/anti-hallucination.md`](./.github/agent-fleet/anti-hallucination.md) · Congruence: [`CAT_CONGRUENCE.md`](./CAT_CONGRUENCE.md)
<!-- END CAT_CONGRUENCE_SNIPPET -->


[![License: Proprietary](https://img.shields.io/badge/License-Proprietary--Commercial-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org)
[![Version](https://img.shields.io/badge/version-0.5.4-blue.svg)](./CHANGELOG.md)

[![Linux](https://img.shields.io/badge/Linux-Ubuntu%2C%20Debian%2C%20Fedora-FCC624?logo=linux&logoColor=black)](https://github.com/fivepanelhat/Coastal-Alpine-Core)
[![Windows](https://img.shields.io/badge/Windows-10%2B-0078D4?logo=windows&logoColor=white)](https://github.com/fivepanelhat/Coastal-Alpine-Core)
[![macOS](https://img.shields.io/badge/macOS-12%2B-000000?logo=apple&logoColor=white)](https://github.com/fivepanelhat/Coastal-Alpine-Core)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5%20%2816GB%29-C11A5B?logo=raspberry-pi&logoColor=white)](https://github.com/fivepanelhat/Coastal-Alpine-Core)

[![Claude AI](https://img.shields.io/badge/Claude-Anthropic-9C27B0)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-Google-4285F4?logo=google&logoColor=white)](https://gemini.google.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-00A67E)](https://openai.com)
[![Grok](https://img.shields.io/badge/Grok-xAI-000000)](https://x.ai)

[![Hailo NPU](https://img.shields.io/badge/NPU-Hailo--10H-005A9C)](https://github.com/fivepanelhat/Coastal-Alpine-Core)
[![Data Sovereign](https://img.shields.io/badge/Data%20Sovereign-NZ%20Bound-00247D)](./ARCHITECTURE.md)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-512BD4?logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiIGZpbGw9IiM1MTJCRDQiLz48L3N2Zz4=)](https://ollama.ai)

[![CI Status](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/ci-scan.yml/badge.svg?branch=main)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/ci-scan.yml)
[![Security Status](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Coastal-Alpine-Core/secops.yml?branch=main&label=Security&style=flat-square&color=success)](https://github.com/fivepanelhat/Coastal-Alpine-Core/actions/workflows/secops.yml)
[![Dependencies](https://img.shields.io/badge/Dependencies-Monitored-brightgreen?logo=dependabot)](https://github.com/fivepanelhat/Coastal-Alpine-Core/security/dependabot)

![coastal-alpine-core Banner](assets/social_preview.png)

**Coastal Alpine Tech Limited** â€” pre-seed startup, New Plymouth, Taranaki, Aotearoa New Zealand.
*Edge AI | Sovereign Systems | Practical Intelligence*

Shared python utility package designed for Taranaki-based Coastal Alpine Tech Edge systems. It handles local offline LLM wrapping, security checks, and hardware telemetry tracking.

**Canonical hardware target:** Raspberry Pi 5 **(16GB)** with **Hailo-10H NPU** (40 TOPS AI Accelerator / AI HAT+ 2).

---

## Architecture Overview

> **Diagrams:** Architecture images and Mermaid maps describe the **target product architecture** for this pre-seed stack. They are engineering design maps â€” not claims of large-scale commercial fleet deployment.

Coastal-Alpine-Core is the **shared edge SDK** used by every portal: offline LLM client, input/security guards, and hardware telemetry for **RPi 5 16GB + Hailo-10H** deployments.

![Coastal-Alpine-Core architecture â€” liquid glass overview](assets/architecture_overview.png)

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
        P["Domain portals<br/>Aqua Â· Soil Â· Blue Â· Sting"]
        A["Aether companion<br/>skills Â· HITL Â· computer use"]
        S["coastal-alpine-stack<br/>compose / K3s"]
    end

    subgraph SDK["coastal_alpine_core package"]
        G["SecurityGuard / input_guard_check"]
        T["TelemetryTracker"]
        C["SovereignOllamaClient"]
        FW["DataFlywheel"]
        PC["portal_core<br/>AIAgent Â· MQTT Â· AV Â· Hardware"]
    end

    subgraph AI["Local AI"]
        O["Ollama<br/>Gemma / Qwen class"]
        HAI["Hailo-10H NPU<br/>edge vision optional"]
    end

    subgraph HOSTS["Dual-platform hosts"]
        WIN["Windows 10/11<br/>install.ps1 Â· venv"]
        LIN["Linux / RPi OS<br/>install.sh Â· venv / uv"]
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
| **Telemetry** | TelemetryTracker | Joules Â· latency Â· load |
| **Flywheel** | DataFlywheel | Trajectories Â· golden sets |
| **Portal kit** | portal_core | MQTT Â· AV Â· hardware loop |
| **Consumers** | Weaver Â· portals Â· Aether Â· stack | One SDK, hybridised stack |
| **Hosts** | Windows Â· Linux Â· RPi 5 | Dev on Win/Linux; deploy on edge |

*Full detail: [ARCHITECTURE.md](./ARCHITECTURE.md) Â· [DEVELOPER_SETUP.md](./DEVELOPER_SETUP.md)*

## Key Features

1. **SovereignOllamaClient (`ollama_client.py`)**: A robust connection wrapper for local offline Ollama SLM deployments. Handles network dropouts and model loads with automated retries and exponential backoff, falling back to local deterministic responses when fully disconnected.
2. **Security & Input Guard (`security.py`)**: Scans incoming prompts for potential prompt injections, local file access attempts, or common injection patterns. It also enforces strict tenant scoping context mismatch flags.
3. **Telemetry & Performance (`telemetry.py`)**: Performance and hardware energy-efficiency tracking specifically designed for edge-native devices (e.g. Raspberry Pi 5 under active load, Hailo NPU draws). Estimates active power draw in Joules.

---

## Installation

**Platforms:** Windows 10/11 Â· Linux (Ubuntu/Debian/RPi OS) Â· macOS Â· production edge on **RPi 5 16GB + Hailo-10H**.

### One-line install (recommended)

<details open>
<summary><strong>ðŸ§ Linux / macOS</strong></summary>

```bash
curl -fsSL https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.sh | bash
```

</details>

<details>
<summary><strong>ðŸªŸ Windows (PowerShell)</strong></summary>

```powershell
irm https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.ps1 | iex
```

> **Note:** If script execution is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

</details>

### Manual install

<details open>
<summary><strong>ðŸ§ Linux / macOS (Bash)</strong></summary>

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
<summary><strong>ðŸªŸ Windows (PowerShell)</strong></summary>

```powershell
git clone https://github.com/fivepanelhat/Coastal-Alpine-Core.git
cd Coastal-Alpine-Core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

**Prerequisites:** [Python 3.10+](https://www.python.org/downloads/) with "Add Python to PATH", [Git for Windows](https://git-scm.com/).

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
**Coastal Alpine Tech Limited â€” New Plymouth, Taranaki, New Zealand.**

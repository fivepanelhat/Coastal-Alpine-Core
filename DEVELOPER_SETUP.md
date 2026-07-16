# Developer Setup — Coastal-Alpine-Core

Shared SDK for the hybrid Kiwi Edge stack (**Weaver · portals · Aether · coastal-alpine-stack**).

**Platforms:** Windows 10/11 · Linux (Ubuntu/Debian/RPi OS) · macOS · production edge on **RPi 5 16GB + Hailo-10H**.

---

## Prerequisites

| Tool | Notes |
| :--- | :--- |
| Python 3.10+ | 3.11+ recommended |
| Git | Required |
| pip / venv | Standard library |
| uv (optional) | Faster lockfile workflows |
| Ollama (optional) | For live LLM smoke tests |

### Linux packages

```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv python3-pip git build-essential
```

### Windows

- Install [Python](https://www.python.org/downloads/) with **Add to PATH**
- Install [Git for Windows](https://git-scm.com/)
- If needed: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## Install

### One-line

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.ps1 | iex
```

### From clone

<details open>
<summary><strong>🐧 Linux / macOS</strong></summary>

```bash
git clone https://github.com/fivepanelhat/Coastal-Alpine-Core.git
cd Coastal-Alpine-Core
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
pytest
ruff check .
```

With **uv**:

```bash
uv sync
uv run pytest
ruff check .
ruff format .
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
pytest
ruff check .
```

</details>

### Pin from GitHub (consumers)

Portals and Weaver should pin **tagged releases only**:

```bash
pip install "git+https://github.com/fivepanelhat/Coastal-Alpine-Core.git@v0.5.4"
```

---

## Monorepo workflow (coastal-alpine-stack)

```bash
git clone --recurse-submodules https://github.com/fivepanelhat/coastal-alpine-stack.git
cd coastal-alpine-stack
# Linux:
python3 -m venv .venv && source .venv/bin/activate
# Windows:
# python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e "./coastal_alpine_core[dev]"
```

Or use stack installers: `install.sh` / `install.ps1`.

---

## Hybrid consumers

| Repo | How it uses Core |
| :--- | :--- |
| **Weaver** | SecurityGuard, tenant isolation, Ollama client |
| **Domain portals** | portal_core, telemetry, flywheel |
| **Aether** | Architecture skills + stack awareness |
| **coastal-alpine-stack** | Editable workspace member |

---

## Versioning

1. Bump version in `pyproject.toml`
2. Push to `main`
3. Tag and push: `git tag v0.5.5 && git push origin v0.5.5`
4. Dependabot / portals update pins

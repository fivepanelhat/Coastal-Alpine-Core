# Developer Setup — Coastal Alpine Stack

## Prerequisites
- Python 3.11+
- uv (recommended) or pip
- Git

## Quick Start (Core)

```bash
git clone https://github.com/fivepanelhat/coastal-alpine-core.git
cd coastal-alpine-core

# At the root of your coastal-alpine-stack folder
uv sync
uv run pytest
ruff check .
ruff format .
```

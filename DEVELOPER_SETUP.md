# Developer Setup — Coastal Alpine Stack (Internal)

## Prerequisites
- Python 3.11+
- uv (recommended)

## Setup

```bash
# Clone the workspace root (recommended)
git clone https://github.com/fivepanelhat/coastal-alpine-stack.git
cd coastal-alpine-stack

uv sync
cd coastal-alpine-core
uv run pytest
ruff check .
ruff format .
```

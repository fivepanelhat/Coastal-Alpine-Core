#!/usr/bin/env bash
# Coastal-Alpine-Core - dual-platform installer (Linux / macOS)
#
# One-line:
# curl -fsSL https://raw.githubusercontent.com/fivepanelhat/Coastal-Alpine-Core/main/install.sh | bash
#
# From a clone:
# ./install.sh
#
# Creates a virtualenv, installs coastal-alpine-core (editable + dev extras when
# running from a checkout), and prints activation instructions.
set -euo pipefail

REPO_URL="${CORE_REPO_URL:-https://github.com/fivepanelhat/Coastal-Alpine-Core.git}"
INSTALL_DIR="${CORE_HOME:-$HOME/.coastal-alpine-core-app}"
VENV_DIR="$INSTALL_DIR/venv"
CORE_TAG="${CORE_TAG:-v0.5.4}"

info() { printf '\033[36m[core]\033[0m %s\n' "$1"; }
warn() { printf '\033[33m[core]\033[0m %s\n' "$1"; }
err() { printf '\033[31m[core]\033[0m %s\n' "$1" >&2; }

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
 err "Python 3.10+ is required. On Debian/Ubuntu/RPi OS:"
 err " sudo apt-get install -y python3 python3-venv python3-pip git build-essential"
 exit 1
fi
PY_VER="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
info "Using Python $PY_VER ($PYTHON_BIN)"
PY_MAJOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info[0])')"
PY_MINOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info[1])')"
if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 10 ]]; }; then
 err "Python 3.10+ is required (found ${PY_MAJOR}.${PY_MINOR})."
 exit 1
fi

if [[ -f "pyproject.toml" ]] && grep -q 'name = "coastal-alpine-core"' pyproject.toml 2>/dev/null; then
 SRC_DIR="$(pwd)"
 info "Installing from current checkout: $SRC_DIR"
 EDITABLE=1
else
 if ! command -v git >/dev/null 2>&1; then
 err "git is required to fetch Core. Install git or run from a clone."
 exit 1
 fi
 mkdir -p "$INSTALL_DIR"
 SRC_DIR="$INSTALL_DIR/src"
 if [[ -d "$SRC_DIR/.git" ]]; then
 info "Updating existing checkout in $SRC_DIR"
 git -C "$SRC_DIR" pull --ff-only || warn "Could not fast-forward; using existing checkout."
 else
 info "Cloning $REPO_URL"
 git clone --depth 1 --branch "$CORE_TAG" "$REPO_URL" "$SRC_DIR" \
 || git clone --depth 1 "$REPO_URL" "$SRC_DIR"
 fi
 EDITABLE=0
fi

info "Creating virtualenv at $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

if [[ "$EDITABLE" -eq 1 ]]; then
 info "Installing coastal-alpine-core[dev] (editable)"
 pip install -e "$SRC_DIR[dev]"
else
 info "Installing coastal-alpine-core from $SRC_DIR"
 pip install "$SRC_DIR"
fi

info "Verifying import"
python -c "from coastal_alpine_core import SovereignOllamaClient; print('ok')"

echo
info "Done. Activate the environment with:"
echo " source $VENV_DIR/bin/activate"
echo
info "Quick check:"
echo " python -c \"from coastal_alpine_core import SovereignOllamaClient; print('ok')\""
echo
info "Hybrid stack next steps:"
echo " Weaver: https://github.com/fivepanelhat/Weaver"
echo " Aether: https://github.com/fivepanelhat/Aether"
echo " Stack: https://github.com/fivepanelhat/coastal-alpine-stack"

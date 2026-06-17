#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_VERSION="${1:-3.12}"
VENV="${VENV:-.venv}"
UV="${UV:-uv}"

export PATH="${HOME}/.local/bin:${PATH}"

die() {
  echo "prepare: $*" >&2
  exit 1
}

ensure_python3() {
  if command -v python3 >/dev/null 2>&1; then
    return
  fi
  case "$(uname -s)" in
    Linux)
      if command -v apt-get >/dev/null 2>&1; then
        echo "prepare: installing python3 via apt-get..."
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-venv curl
      else
        die "python3 not found; install Python 3.8+ manually"
      fi
      ;;
    Darwin)
      die "python3 not found; install Python (e.g. brew install python@3.12) or ensure uv is available"
      ;;
    *)
      die "unsupported OS; install python3 manually"
      ;;
  esac
}

ensure_uv() {
  if command -v "$UV" >/dev/null 2>&1; then
    return
  fi
  echo "prepare: installing uv..."
  ensure_python3
  curl -fsSL https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
  command -v "$UV" >/dev/null 2>&1 || die "uv install failed"
}

ensure_venv() {
  ensure_uv
  if [ ! -x "${VENV}/bin/python" ]; then
    echo "prepare: creating virtualenv in ${VENV}..."
    if "$UV" python install "${PYTHON_VERSION}" 2>/dev/null; then
      "$UV" venv "${VENV}" --python "${PYTHON_VERSION}"
    else
      "$UV" venv "${VENV}" --python python3
    fi
  fi
}

ensure_poetry() {
  ensure_venv
  if [ ! -x "${VENV}/bin/poetry" ]; then
    echo "prepare: installing poetry..."
    "$UV" pip install --python "${VENV}/bin/python" "poetry>=1.8,<3"
  fi
  # packaging is used by version-sync semver helpers
  "$UV" pip install --python "${VENV}/bin/python" packaging >/dev/null
}

DAEMON_REQUIREMENTS="${ROOT}/daemon/requirements.txt"

ensure_daemon_deps() {
  ensure_venv
  [ -f "${DAEMON_REQUIREMENTS}" ] || die "missing ${DAEMON_REQUIREMENTS}"
  echo "prepare: installing daemon dependencies from daemon/requirements.txt..."
  "$UV" pip install --python "${VENV}/bin/python" -r "${DAEMON_REQUIREMENTS}"
}

ensure_poetry
ensure_daemon_deps
echo "prepare: ready ($( "${VENV}/bin/poetry" --version ))"

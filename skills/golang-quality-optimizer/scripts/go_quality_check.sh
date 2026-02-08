#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
go_quality_check.sh: run common Go quality checks for the current module.

Usage:
  go_quality_check.sh [--fix] [--no-race] [--pkgs <pattern>]

Options:
  --fix        Apply gofmt/goimports changes (default: check only).
  --no-race    Skip `go test -race` (default: run if supported).
  --pkgs       Package pattern for go commands (default: ./...).

Notes:
  - If optional tools are missing (staticcheck, golangci-lint, goimports), this script prints a hint and continues.
  - This script expects to be run inside a Go module (go.mod). If not, it exits with code 2.
EOF
}

FIX=0
RACE=1
PKGS="./..."

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --fix)
      FIX=1
      shift
      ;;
    --no-race)
      RACE=0
      shift
      ;;
    --pkgs)
      PKGS="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v go >/dev/null 2>&1; then
  echo "go not found in PATH" >&2
  exit 127
fi

GOMOD="$(go env GOMOD 2>/dev/null || true)"
if [[ -z "$GOMOD" || "$GOMOD" == "/dev/null" ]]; then
  echo "Not inside a Go module (go env GOMOD is /dev/null). Run in a module directory." >&2
  exit 2
fi

echo "Go module: $GOMOD"
echo "Packages:  $PKGS"

echo
echo "== Formatting =="
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GOFILES=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && GOFILES+=("$f")
  done < <(git ls-files '*.go' | grep -v '^vendor/' || true)
else
  GOFILES=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && GOFILES+=("$f")
  done < <(find . -type f -name '*.go' -not -path './vendor/*' -not -path './.git/*' -print || true)
fi

if [[ ${#GOFILES[@]} -eq 0 ]]; then
  echo "No .go files found; skipping gofmt/goimports."
else
  if [[ "$FIX" -eq 1 ]]; then
    echo "Running: gofmt -w (on ${#GOFILES[@]} files)"
    gofmt -w "${GOFILES[@]}"
  else
    echo "Running: gofmt -l (on ${#GOFILES[@]} files)"
    fmt_out="$(gofmt -l "${GOFILES[@]}" || true)"
    if [[ -n "$fmt_out" ]]; then
      echo "gofmt would reformat:"
      echo "$fmt_out"
      echo "Tip: re-run with --fix"
      exit 1
    fi
  fi

  if command -v goimports >/dev/null 2>&1; then
    if [[ "$FIX" -eq 1 ]]; then
      echo "Running: goimports -w"
      goimports -w "${GOFILES[@]}"
    else
      echo "Running: goimports -l"
      imp_out="$(goimports -l "${GOFILES[@]}" || true)"
      if [[ -n "$imp_out" ]]; then
        echo "goimports would change:"
        echo "$imp_out"
        echo "Tip: re-run with --fix"
        exit 1
      fi
    fi
  else
    echo "goimports not found; skipping import formatting (install: go install golang.org/x/tools/cmd/goimports@latest)."
  fi
fi

echo
echo "== Tests =="
echo "Running: go test $PKGS"
go test "$PKGS"

if [[ "$RACE" -eq 1 ]]; then
  echo
  echo "Running: go test -race $PKGS"
  # -race isn't supported for some architectures; handle that gracefully.
  if ! go test -race "$PKGS"; then
    echo "go test -race failed. If your environment doesn't support -race, re-run with --no-race." >&2
    exit 1
  fi
fi

echo
echo "== Vet =="
echo "Running: go vet $PKGS"
go vet "$PKGS"

echo
echo "== Static analysis (optional) =="
if command -v staticcheck >/dev/null 2>&1; then
  echo "Running: staticcheck $PKGS"
  staticcheck "$PKGS"
else
  echo "staticcheck not found; skipping (install: go install honnef.co/go/tools/cmd/staticcheck@latest)."
fi

echo
echo "== Lint (optional) =="
if command -v golangci-lint >/dev/null 2>&1; then
  echo "Running: golangci-lint run"
  golangci-lint run
else
  echo "golangci-lint not found; skipping (install: https://golangci-lint.run/usage/install/)."
fi

echo
echo "All checks passed."

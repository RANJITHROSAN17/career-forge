#!/usr/bin/env bash
# =============================================================================
# Career Forge — download the 4 Executa binaries from the GitHub Release built
# by .github/workflows/build-executa-binaries.yml into
#   executas/career-engine-python/dist/
#
# Usage (from the project root):
#   bash scripts/download-binaries.sh 1.0.1 <owner>/<repo>
# =============================================================================
set -euo pipefail

VERSION="${1:-1.0.1}"
REPO="${2:-REPLACE-ME/career-forge}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT/executas/career-engine-python/dist"
mkdir -p "$DIR"

BASE="https://github.com/$REPO/releases/download/career-engine-v$VERSION"

for f in \
  "career-engine-$VERSION-darwin-arm64.tar.gz" \
  "career-engine-$VERSION-darwin-x86_64.tar.gz" \
  "career-engine-$VERSION-linux-x86_64.tar.gz" \
  "career-engine-$VERSION-windows-x86_64.zip"; do
  echo "downloading $f"
  curl -fL "$BASE/$f" -o "$DIR/$f"
  size=$(wc -c < "$DIR/$f")
  if [ "$size" -lt 1024 ]; then
    echo "ERROR: $f is only $size bytes - download failed. Check repo/tag/version." >&2
    exit 1
  fi
  echo "  -> $size bytes"
done

echo
echo "All 4 archives are in: $DIR"
echo "Next: anna-app apps publish"

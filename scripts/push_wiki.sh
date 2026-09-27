#!/usr/bin/env bash
set -euo pipefail

# Script to deploy the wiki/ directory directly to the GitHub Wiki git repository.

REMOTE_ORIGIN=$(git config --get remote.origin.url || true)
if [ -z "${REMOTE_ORIGIN}" ]; then
  echo "Error: remote.origin.url is not set."
  exit 1
fi

WIKI_URL="${REMOTE_ORIGIN%.git}.wiki.git"
echo "Target GitHub Wiki repository: ${WIKI_URL}"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "${TMP_DIR}"' EXIT

if git clone "${WIKI_URL}" "${TMP_DIR}" 2>/dev/null; then
  echo "Cloned existing wiki repo."
else
  echo "Initializing local repository for wiki..."
  git -C "${TMP_DIR}" init -b master
  git -C "${TMP_DIR}" remote add origin "${WIKI_URL}"
fi

cp -r wiki/* "${TMP_DIR}/"
cd "${TMP_DIR}"
git add .

if git diff --quiet && git diff --staged --quiet; then
  echo "Wiki is already up to date. Nothing to commit."
else
  git commit -m "docs: sync wiki documentation"
  git push origin HEAD:master || git push origin HEAD:main
  echo "Successfully updated GitHub Wiki!"
fi

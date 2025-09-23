#!/usr/bin/env bash
set -euo pipefail

pushd frontend >/dev/null

if [ ! -f package-lock.json ]; then
  echo "package-lock.json is required to build the frontend" >&2
  exit 1
fi

echo "📦 Installing frontend dependencies"
npm ci

echo "🏗 Building frontend bundle"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-https://translate-doc-backend.example.com}" npm run build

popd >/dev/null

echo "✅ Frontend build available in frontend/dist"

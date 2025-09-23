#!/usr/bin/env bash
set -euo pipefail

: "${SCW_NAMESPACE_ID:?SCW_NAMESPACE_ID is required}"
BACKEND_IMAGE_NAME="${BACKEND_IMAGE_NAME:-translate-doc-backend}"
BACKEND_CONTAINER_NAME="${BACKEND_CONTAINER_NAME:-translate-doc-backend}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"

if ! command -v scw >/dev/null 2>&1; then
  echo "scw CLI is required for deployment" >&2
  exit 1
fi

REGISTRY_ENDPOINT=$(scw container namespace get "$SCW_NAMESPACE_ID" -o json | python -c "import json,sys; print(json.load(sys.stdin)['registry_endpoint'])")

FULL_IMAGE="${REGISTRY_ENDPOINT}/${BACKEND_IMAGE_NAME}:${IMAGE_TAG}"

echo "🛠 Building backend image ${FULL_IMAGE}"
docker build -f backend/Dockerfile --target prod -t "$FULL_IMAGE" backend

echo "🔐 Logging into Scaleway registry"
scw registry login --namespace-id "$SCW_NAMESPACE_ID"

echo "⬆️ Pushing image to registry"
docker push "$FULL_IMAGE"

CONTAINER_ID=$(scw container container list --namespace-id "$SCW_NAMESPACE_ID" -o json | python -c "import json,sys; data=json.load(sys.stdin);\nprint(next((item['id'] for item in data if item['name']==\"$BACKEND_CONTAINER_NAME\"), '' ))")

if [[ -z "$CONTAINER_ID" ]]; then
  echo "Unable to find container named $BACKEND_CONTAINER_NAME in namespace $SCW_NAMESPACE_ID" >&2
  exit 1
fi

echo "🚀 Updating container $BACKEND_CONTAINER_NAME to image $FULL_IMAGE"
scw container container update "$CONTAINER_ID" registry-image="$FULL_IMAGE"

echo "⌛ Waiting for container rollout"
while true; do
  STATUS=$(scw container container get "$CONTAINER_ID" -o json | python -c "import json,sys; print(json.load(sys.stdin)['status'])")
  [[ "$STATUS" == "ready" ]] && break
  echo "Current status: $STATUS"
  sleep 5
done

echo "✅ Backend deployment completed"

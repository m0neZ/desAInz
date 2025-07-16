#!/usr/bin/env bash
# Perform a blue-green deployment using kubectl.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <service> <image> <namespace>" >&2
  exit 1
fi

SERVICE="$1"
IMAGE="$2"
NAMESPACE="$3"

current_color="$(kubectl get svc "$SERVICE" -n "$NAMESPACE" -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo blue)"
if [[ "$current_color" == "blue" ]]; then
  new_color="green"
else
  new_color="blue"
fi

deployment="$SERVICE-$new_color"

echo "Deploying $SERVICE as $deployment with image $IMAGE"

kubectl set image deployment/"$deployment" "$SERVICE"="$IMAGE" -n "$NAMESPACE" --record
kubectl rollout status deployment/"$deployment" -n "$NAMESPACE"

kubectl patch svc "$SERVICE" -n "$NAMESPACE" -p "{\"spec\":{\"selector\":{\"app\":\"$SERVICE\",\"color\":\"$new_color\"}}}"

old_deployment="$SERVICE-$current_color"
kubectl rollout status deployment/"$deployment" -n "$NAMESPACE"

# Optionally scale down old deployment
if kubectl get deployment "$old_deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
  kubectl scale deployment "$old_deployment" -n "$NAMESPACE" --replicas=0
fi

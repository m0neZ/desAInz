#!/usr/bin/env bash
# Perform a blue-green deployment using kubectl.
#
# The script gradually shifts traffic from the current deployment to the new
# one by scaling replicas in small increments. The service selector is first
# expanded to include both colors. After each step a health check is performed
# via ``scripts/check_k8s_health.sh``. If the check fails, the script rolls back
# to the previous deployment and aborts.

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

new_deployment="$SERVICE-$new_color"
old_deployment="$SERVICE-$current_color"

replicas="$(kubectl get deployment "$old_deployment" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo 1)"

echo "Updating $new_deployment to image $IMAGE"
kubectl set image deployment/"$new_deployment" "$SERVICE"="$IMAGE" -n "$NAMESPACE" --record

# Ensure new deployment starts from zero replicas
kubectl scale deployment "$new_deployment" -n "$NAMESPACE" --replicas=0
kubectl rollout status deployment/"$new_deployment" -n "$NAMESPACE"

# Allow service to route to both colors during traffic shifting
kubectl patch svc "$SERVICE" -n "$NAMESPACE" -p '{"spec":{"selector":{"app":"'"$SERVICE"'"}}}'

for ((i=1; i<=replicas; i++)); do
  echo "Shifting replica $i of $replicas"
  kubectl scale deployment "$new_deployment" -n "$NAMESPACE" --replicas="$i"
  kubectl scale deployment "$old_deployment" -n "$NAMESPACE" --replicas="$((replicas - i))"
  kubectl rollout status deployment/"$new_deployment" -n "$NAMESPACE"
  if ! scripts/check_k8s_health.sh "$NAMESPACE" "$SERVICE"; then
    echo "Health check failed, rolling back" >&2
    kubectl patch svc "$SERVICE" -n "$NAMESPACE" \
      -p '{"spec":{"selector":{"app":"'"$SERVICE"'","color":"'"$current_color"'"}}}'
    kubectl scale deployment "$new_deployment" -n "$NAMESPACE" --replicas=0
    kubectl scale deployment "$old_deployment" -n "$NAMESPACE" --replicas="$replicas"
    exit 1
  fi
done

echo "Switching service selector to $new_color"
kubectl patch svc "$SERVICE" -n "$NAMESPACE" \
  -p '{"spec":{"selector":{"app":"'"$SERVICE"'","color":"'"$new_color"'"}}}'

kubectl scale deployment "$old_deployment" -n "$NAMESPACE" --replicas=0
kubectl rollout status deployment/"$new_deployment" -n "$NAMESPACE"

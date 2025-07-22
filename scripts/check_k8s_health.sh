#!/usr/bin/env bash
# Wait for Kubernetes services to pass readiness checks.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <namespace> <service1> [service2 ...]" >&2
  exit 1
fi

NAMESPACE="$1"
shift
SERVICES=("$@")

TIMEOUT=${TIMEOUT:-60}

for svc in "${SERVICES[@]}"; do
  echo "Waiting for $svc in namespace $NAMESPACE"
  port="$(kubectl get service "$svc" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].port}')"
  local_port=$((RANDOM%30000 + 1025))
  kubectl port-forward "service/$svc" "$local_port:$port" -n "$NAMESPACE" >/tmp/pf-$svc.log 2>&1 &
  pf_pid=$!
  start=$(date +%s)
  until curl -fsS "http://localhost:$local_port/ready" >/dev/null 2>&1; do
    if [[ $(($(date +%s) - start)) -ge $TIMEOUT ]]; then
      echo "$svc failed readiness check"
      kill "$pf_pid" || true
      exit 1
    fi
    sleep 2
  done
  kill "$pf_pid"
  echo "$svc is healthy"
  rm -f "/tmp/pf-$svc.log"
done

echo "All services healthy"

#!/usr/bin/env bash
set -e
set -o pipefail

for container in qworker qworker-analytics; do
  if ./ci/compose.sh run --rm --no-deps -e QWORKER_HEALTH_CHECK=true "$container"; then
    >&2 echo "worker-health test for $container passed when it should have failed (redis should not be running)!"
    exit 1
  else
    echo "worker-health test for $container failed successfully"
  fi
done

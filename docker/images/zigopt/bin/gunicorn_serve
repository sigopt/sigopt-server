#!/usr/bin/env bash
set -e
set -o pipefail

exec gunicorn \
 --log-file - \
 --worker-class gevent \
 --limit-request-line 8190 \
 "$@"

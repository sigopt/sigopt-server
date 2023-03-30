#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

set -e
set -o pipefail

protected_branch='master'
current_upstream="$(git for-each-ref --format='%(upstream:short)' "$(git symbolic-ref -q HEAD)")"
current_branch="$(basename "$current_upstream")"

if [ "$protected_branch" = "$current_branch" ]
then
    >&2 echo pre-push error: dont push to default branch
    exit 1 # push will not execute
else
    exit 0 # push will execute
fi

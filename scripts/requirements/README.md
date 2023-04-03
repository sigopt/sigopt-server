<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

# Requirements scripts

The scripts in this directory were created to make updating requirements easy.

## Freezing python requirements

After editing requirements in `requirements-to-freeze.txt`, you will need to freeze the requirements to persist them.
This can be done by running `./scripts/requirements/freeze_requirements.sh`, which will update `requirements.txt`.
Finally, commit both `requirements-to-freeze.txt` and `requirements.txt`.

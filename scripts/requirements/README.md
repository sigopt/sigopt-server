<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

# Requirements scripts

The scripts in this directory were created to make updating requirements easy.

## Editing yarn packages

Run `./scripts/requirements/yarn_command.sh add X` to add the package `X`.
All yarn commands should work.
Finally, commit both `package.json` and `yarn.lock`.
Your `node` image will be updated, so you can now start using this new package configuration in development.

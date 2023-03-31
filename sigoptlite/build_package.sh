#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

set -e
set -o pipefail


SCRIPT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

LITE_PREFIX="lite_"
REQUIRED_SIGOPT_PACKAGES=("sigoptcompute" "sigoptaux")

function setup_packages () { 
    local packages=("$@")

    # Vendor required packages with different names so they don't shadow when installed in sigopt-server
    # TODO: Undo this one compute/aux are moved into seperate packages
    for package_name in "${packages[@]}";
        do
            local lite_package_name="${LITE_PREFIX}${package_name}"
            cp -r "${SCRIPT_DIR}/../${package_name}/${package_name}" "${SCRIPT_DIR}/${lite_package_name}"
        done

    # Replace import names. Could be codemod.
    for package_name in "${packages[@]}";
        do
            local lite_package_name="${LITE_PREFIX}${package_name}"
            find "$SCRIPT_DIR/" -name "*.py" -type f -exec sed -i '' "s/from ${package_name}/from ${lite_package_name}/g" {} \;
        done  
}

function cleanup_packages () {
    local packages=("$@")
        
    for package_name in "${packages[@]}";
        do
            local lite_package_name="${LITE_PREFIX}${package_name}"
            rm -rf "${SCRIPT_DIR:?}/${lite_package_name}"
            find "$SCRIPT_DIR/" -name "*.py" -type f -exec sed -i '' "s/from ${lite_package_name}/from ${package_name}/g" {} \;
        done
    
}

rm -rf "${SCRIPT_DIR:?}/sigoptlite.egg-info"
rm -rf "${SCRIPT_DIR:?}/dist"

setup_packages "${REQUIRED_SIGOPT_PACKAGES[@]}"

python -m build

cleanup_packages "${REQUIRED_SIGOPT_PACKAGES[@]}"

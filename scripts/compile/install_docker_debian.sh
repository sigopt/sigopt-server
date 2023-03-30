#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
set -e
set -o pipefail

echo "This script will make changes to your base operating system, using sudo permissions. We provide it as" \
     "a convenience to help you get everything working as quickly as possible, but strongly recommend that you do" \
     "it yourself, following the steps at https://docs.docker.com/engine/install/ubuntu/"

read -r -p "Do you wish to proceed? (Yes/no)" yn

case $yn in
  [Yy]*) echo "Installing docker";;
  [Nn]*)  echo "exiting...";
        exit 0;;
  *) echo "Invalid response";
      exit 1;;
esac

sudo apt-get install ca-certificates curl gnupg lsb-release software-properties-common

sudo mkdir -m 0755 -p /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo apt-key add /etc/apt/keyrings/docker.gpg
sudo apt-add-repository "deb https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

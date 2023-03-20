# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import subprocess
import sys


APPLICATION_IMAGES = [
  "nginx",
  "node",
  "zigopt",
]

parser = argparse.ArgumentParser()
parser.add_argument("--registry", default=None)
parser.add_argument("--tag", default="latest")
parser.add_argument("trivy_args", nargs=argparse.REMAINDER)

if __name__ == "__main__":
  args = parser.parse_args()
  trivy_args = args.trivy_args
  if trivy_args and trivy_args[0] == "--":
    trivy_args.pop(0)
  failed = []
  for image in APPLICATION_IMAGES:
    image_uri = image
    if args.registry:
      image_uri = f"{args.registry}/{image}"
    image_uri = f"{image_uri}:{args.tag}"
    result = subprocess.call(
      [
        "trivy",
        "image",
        f"--output=artifacts/trivy/{image}.json",
        image_uri,
        *args.trivy_args,
      ]
    )
    if result:
      failed.append(image_uri)
  if failed:
    print(f"Trivy scan failed for the following images: {' '.join(failed)}")
  sys.exit(bool(failed))

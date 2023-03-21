<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

# SigOpt Docker images

This directory contains the scripts for building SigOpt docker images for development.
This will eventually be extended to building images for production, but we are not there yet.

## Building and tagging all images from a specific commit

To build images, run the following:

```
python3 docker/image_builder.py [images]
```

## Choosing a custom tag

To tag the built images with a specific tag, use the --build-tag argument.
Example:

```
python3 docker/image_builder.py [images] --build-tag=testing
```

## Building the CI images

The `circleci-image` image is built and pushed with the `image_builder.py` script.

```
python3 docker/image_builder.py circleci-image --push-tag="$(date +%F)"
```

Update the `circleci-image` tag in `.circleci/config.yml` when this is complete.

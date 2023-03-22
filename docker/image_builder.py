# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import docker
from dotenv import dotenv_values


TARGET_BUILD = "build"
TARGET_CLEAN = "clean"
TARGET_ENSURE_IMAGE = "ensure_image"
TARGET_PULL = "pull"

AUX_IMAGES = [
  "nginx",
]
PYTHON_IMAGES = [
  "python",
]
ZIGOPT_IMAGES = [
  "test-runner",
  "zigopt",
]
NODE_IMAGES = [
  "node",
]
WEB_IMAGES = [
  "test-routes",
  "web",
]
RUNTIME_IMAGES = [
  *AUX_IMAGES,
  *PYTHON_IMAGES,
  *ZIGOPT_IMAGES,
  *NODE_IMAGES,
  *WEB_IMAGES,
]

OUTPUT_ERROR_ONLY = "error_only"
OUTPUT_SYNC = "sync"
OUTPUT_ASYNC = "async"
OUTPUT_FILE = "file"
DEFAULT_LOG_DIR = "artifacts/docker/logs"


parser = argparse.ArgumentParser()
parser.add_argument("images", nargs="*", help="images to build, defaults to all runtime images")
parser.add_argument("--aux-images", action="store_true", help=f"build aux images: {', '.join(AUX_IMAGES)}")
parser.add_argument("--node-images", action="store_true", help=f"build node images: {', '.join(NODE_IMAGES)}")
parser.add_argument("--python-images", action="store_true", help=f"build python images: {', '.join(PYTHON_IMAGES)}")
parser.add_argument("--web-images", action="store_true", help=f"build web images: {', '.join(WEB_IMAGES)}")
parser.add_argument("--zigopt-images", action="store_true", help=f"build zigopt images: {', '.join(ZIGOPT_IMAGES)}")
parser.add_argument("--pull-image", default=[], action="append", help="pull these images instead of building")
parser.add_argument("--build-tag", default="latest", help="tag for built images")
parser.add_argument("--registry", default="docker.io", help="registry for images")
parser.add_argument("--cache-tag", default=[], action="append", help="image tags to use as build cache")
parser.add_argument("--build-arg", default=[], action="append", help="build args to pass to docker")
parser.add_argument("--threads", type=int, default=8, help="number of concurrent threads for pulling/building")
parser.add_argument("--retries", type=int, default=1, help="number of times to retry docker operations")
parser.add_argument(
  "--output",
  default=OUTPUT_ERROR_ONLY,
  choices=[OUTPUT_ERROR_ONLY, OUTPUT_SYNC, OUTPUT_ASYNC, OUTPUT_FILE],
  help="show build output",
)
parser.add_argument(
  "--clean-intermediate",
  action="store_true",
  help="clean intermediate images used just for building",
)
parser.add_argument(
  "--no-cache-probability",
  type=float,
  default=0,
  help="0 to 1 probability that caching is skipped",
)


def _retry(func, retries):
  for retry_number in range(retries + 1):
    try:
      return func()
    except Exception:
      if retry_number == retries:
        raise
  raise Exception(f"retries must be a positive number, got {retries}")


def sanitize_tag(tag):
  return tag.replace("/", "__")


class BuildGraph:
  def __init__(self):
    self.targets = {}
    self.lock = threading.Lock()

  def is_finished(self):
    return not self.targets

  def add_target(self, target, depends):
    with self.lock:
      self.targets[target] = set(depends)

  def pop_leaves(self):
    leaves = []
    with self.lock:
      for target, depends in self.targets.items():
        if not depends:
          leaves.append(target)
      for target in leaves:
        del self.targets[target]
    return leaves

  def set_finished(self, target):
    with self.lock:
      for depends in self.targets.values():
        depends.discard(target)

  def trim_keeping_targets(self, targets):
    new_targets = {}
    targets = set(targets)
    with self.lock:
      while targets:
        next_targets = set()
        for target in targets:
          depends = set(self.targets[target])
          new_targets[target] = depends
          next_targets.update(depends)
        targets = next_targets
      self.targets = new_targets

  def targets_that_depend_on(self, target):
    dependants = set()
    for dependant, depends in self.targets.items():
      if target in depends:
        dependants.add(dependant)
    return dependants

  def run(self, handle_target, threads=8):
    error_event = threading.Event()
    ticker_event = threading.Event()
    ticker_event.set()

    def wrap_handle(target):
      try:
        handle_target(target)
        self.set_finished(target)
      except Exception:
        error_event.set()
        raise
      finally:
        ticker_event.set()

    results = []
    with ThreadPoolExecutor(max_workers=threads) as tpe:
      while not self.is_finished():
        ticker_event.wait()
        ticker_event.clear()
        if error_event.is_set():
          break
        leaves = self.pop_leaves()
        results.extend(tpe.submit(wrap_handle, target) for target in leaves)
    for r in results:
      r.result()


class BuildContext:
  def __init__(
    self,
    docker_client,
    registry,
    build_tag,
    cache_tags,
    build_path,
    build_args,
    retries,
    output_mode,
    no_cache_probability,
    dot_env,
  ):
    self.docker_client = docker_client
    self.registry = registry
    self.build_tag = build_tag
    self.cache_tags = cache_tags
    self.build_args = build_args
    self.build_path = build_path
    self.retries = retries
    self.output_mode = output_mode
    self.no_cache_probability = no_cache_probability
    self.dot_env = dot_env

  def get_image_repository(self, name):
    return f"{self.registry}/sigopt/{name}"

  def get_image_uri(self, name, tag):
    return f"{self.get_image_repository(name)}:{sanitize_tag(tag)}"

  def get_build_image_uri(self, name):
    return f"sigopt/{name}:{sanitize_tag(self.build_tag)}"

  def build_image(self, name):
    use_cache = random.random() >= self.no_cache_probability
    for retry_number in range(self.retries + 1):
      with tempfile.TemporaryFile("w+") as output_fp:
        stdout, stderr = (sys.stdout, sys.stderr) if self.output_mode == OUTPUT_ASYNC else (output_fp, output_fp)
        if not use_cache:
          print("*** Skipping cache for this build ***", file=stdout)
        proc = subprocess.Popen(
          [
            "docker",
            "build",
            self.build_path,
            f"--file={self.build_path}/docker/images/{name}/Dockerfile",
            f"--tag={self.get_build_image_uri(name)}",
            "--build-arg=BUILDKIT_INLINE_CACHE=1",
            f"--build-arg=BUILD_TAG={sanitize_tag(self.build_tag)}",
            "--progress=plain",
            *(f"--build-arg={arg}" for arg in self.build_args),
            *(f"--build-arg={key}={value}" for key, value in self.dot_env.items()),
            *([] if use_cache else ["--no-cache"]),
            *(f"--cache-from={self.get_image_uri(name, tag)}" for tag in self.cache_tags),
          ],
          env={
            "DOCKER_BUILDKIT": "1",
            **os.environ,
          },
          stdout=stdout,
          stderr=stderr,
        )
        exit_code = proc.wait()
        error_occurred = exit_code != 0
        if self.output_mode == OUTPUT_SYNC or self.output_mode in (OUTPUT_ERROR_ONLY, OUTPUT_FILE) and error_occurred:
          sys_out = sys.stderr if error_occurred else sys.stdout
          print("", file=sys_out)
          if error_occurred:
            print(f"****** ERROR OUTPUT FOR {name} ******", file=sys_out)
          output_fp.seek(0)
          shutil.copyfileobj(output_fp, sys_out)
        if self.output_mode == OUTPUT_FILE:
          output_fp.seek(0)
          os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
          with open(os.path.join(DEFAULT_LOG_DIR, f"{name}.log"), "w") as log_fp:
            shutil.copyfileobj(output_fp, log_fp)
        if not error_occurred:
          break
        if retry_number == self.retries:
          raise Exception("Build failed!")

  def pull_image(self, name):
    repo = self.get_image_repository(name)
    tag = sanitize_tag(self.build_tag)
    image = _retry(
      lambda: self.docker_client.images.pull(self.get_image_repository(name), tag=sanitize_tag(self.build_tag)),
      self.retries,
    )
    image.tag(self.get_build_image_uri(name))
    self.docker_client.images.remove(f"{repo}:{tag}")

  def remove_image(self, name):
    self.docker_client.images.remove(self.get_build_image_uri(name))

  def handle_target(self, target):
    target_type, target_info = target.split(":", 1)
    if not target_type:
      image = target_info
      print(f"Finished all tasks for {image}")
    elif target_type == TARGET_BUILD:
      image = target_info
      print(f"Building {image}")
      start = time.time()
      self.build_image(image)
      print(f"Finished building {image} in {time.time() - start} seconds")
    elif target_type == TARGET_PULL:
      image = target_info
      print(f"Pulling {image}")
      start = time.time()
      self.pull_image(image)
      print(f"Finished pulling {image} in {time.time() - start} seconds")
    elif target_type == TARGET_ENSURE_IMAGE:
      image = target_info
      print(f"{image} exists locally")
    elif target_type == TARGET_CLEAN:
      image = target_info
      print(f"Cleaning up {image}")
      self.remove_image(image)
      print(f"Finished cleaning up {image}")
    else:
      raise Exception(f"Target not recognized: {target}")


def create_build_graph(images, pull_images, clean_intermediate):
  build_graph = BuildGraph()
  pull_images = set(pull_images)
  for name in os.listdir("docker/images"):
    deps = []
    if name in pull_images:
      real_target = f"{TARGET_PULL}:{name}"
    else:
      real_target = f"{TARGET_BUILD}:{name}"
      try:
        with open(f"docker/images/{name}/depends") as fp:
          deps = fp.read().splitlines()
      except FileNotFoundError:
        pass
    ensure_image_target = f"{TARGET_ENSURE_IMAGE}:{name}"
    build_graph.add_target(ensure_image_target, [real_target])
    build_graph.add_target(real_target, [f"{TARGET_ENSURE_IMAGE}:{dep}" for dep in deps])
    main_targets = [ensure_image_target]
    build_graph.add_target(f":{name}", main_targets)
  build_graph.trim_keeping_targets(f":{image}" for image in images)
  if clean_intermediate:
    images_to_clean = {
      target.split(":", 2)[1] for target in build_graph.targets if target.split(":", 1)[0] == TARGET_ENSURE_IMAGE
    } - set(images)
    for image in images_to_clean:
      target = f"{TARGET_CLEAN}:{image}"
      build_graph.add_target(
        target,
        build_graph.targets_that_depend_on(f"{TARGET_ENSURE_IMAGE}:{image}"),
      )
  return build_graph


if __name__ == "__main__":
  dot_env = dotenv_values(".env")
  args = parser.parse_args()
  client = docker.from_env()
  context = BuildContext(
    docker_client=client,
    registry=args.registry,
    build_args=args.build_arg,
    build_path=".",
    build_tag=args.build_tag,
    cache_tags=args.cache_tag,
    retries=args.retries,
    output_mode=args.output,
    no_cache_probability=args.no_cache_probability,
    dot_env=dot_env,
  )
  images = list(args.images or [])
  if args.aux_images:
    images.extend(AUX_IMAGES)
  if args.python_images:
    images.extend(PYTHON_IMAGES)
  if args.zigopt_images:
    images.extend(ZIGOPT_IMAGES)
  if args.node_images:
    images.extend(NODE_IMAGES)
  if args.web_images:
    images.extend(WEB_IMAGES)
  if not images:
    images.extend(RUNTIME_IMAGES)
  build_graph = create_build_graph(
    images=images,
    pull_images=args.pull_image,
    clean_intermediate=args.clean_intermediate,
  )
  build_graph.run(context.handle_target, threads=args.threads)

#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import datetime
import os
import re
import sys


# customlint: disable=AccidentalFormatStringRule


YEAR = datetime.datetime.now().year
COPYRIGHT = f"Copyright © {YEAR} Intel Corporation"
LICENSE = "SPDX-License-Identifier: Apache License 2.0"

DISCLAIMER_RE_LINES = [
  re.compile(r"^[ *#]*Copyright © [0-9]{4} Intel Corporation$"),
  re.compile(r"^[ *#]*$"),
  re.compile(r"^[ *#]*SPDX-License-Identifier:.*$"),
]

SKIP_DIRECTORIES = {
  "node_modules",
}


class Filetype:
  dockerfile = "Dockerfile"
  js = ".js"
  less = ".less"
  markdown = ".md"
  python = ".py"
  shell = ".sh"


FILETYPES = (
  Filetype.dockerfile,
  Filetype.js,
  Filetype.less,
  Filetype.markdown,
  Filetype.python,
  Filetype.shell,
)

COMMENT_BLOCKS = {
  Filetype.dockerfile: ("", ""),
  Filetype.js: ("/**\n", " */\n\n"),
  Filetype.less: ("/**\n", " */\n"),
  Filetype.markdown: ("<!--\n", "-->\n\n"),
  Filetype.python: ("", ""),
  Filetype.shell: ("", ""),
}

COMMENT_LINES = {
  Filetype.dockerfile: "# ",
  Filetype.js: " * ",
  Filetype.less: " * ",
  Filetype.markdown: "",
  Filetype.python: "# ",
  Filetype.shell: "# ",
}


def guess_filetype(filename):
  for filetype in FILETYPES:
    if filename.endswith(filetype):
      return filetype
    # Filenames like "Dockerfile.api" are allowed
    if os.path.basename(filename).startswith(Filetype.dockerfile):
      return Filetype.dockerfile
  return None


def generate_disclaimer(filetype):
  opener, closer = COMMENT_BLOCKS[filetype]
  separator = COMMENT_LINES[filetype]
  return "\n".join(
    [
      f"{opener}{separator}{COPYRIGHT}",
      separator.rstrip(" "),
      f"{separator}{LICENSE}",
      f"{closer}",
    ]
  )


DISCLAIMERS_BY_FILETYPE = {filetype: generate_disclaimer(filetype) for filetype in FILETYPES}


def file_has_disclaimer(filename, filetype, verbose=False):
  if verbose:
    print(f"Checking: {filename}")  # noqa: T001
  with open(filename) as fp:
    to_check = []
    line = next(fp)
    if line.startswith("#!"):
      line = next(fp)
    if line in ("/**\n", "<!--\n"):
      line = next(fp)
    to_check.append(line)
    to_check.extend(l for l, _ in zip(fp, range(len(DISCLAIMER_RE_LINES) - 1)))

  to_check = "".join(to_check).split("\n")
  if len(to_check) < len(DISCLAIMER_RE_LINES):
    return False

  return all(regex.match(line) for regex, line in zip(DISCLAIMER_RE_LINES, to_check))


def check_all(directory, verbose=False):
  missing = []
  if os.path.isfile(directory):
    gen = [("", "", [directory])]
  else:
    gen = os.walk(directory)
  for dirpath, _, filenames in gen:
    if any(skip in dirpath for skip in SKIP_DIRECTORIES):
      continue
    for filename in filenames:
      absolute_filename = os.path.join(dirpath, filename)
      filetype = guess_filetype(absolute_filename)
      if filetype and os.stat(absolute_filename).st_size > 0:
        if not file_has_disclaimer(absolute_filename, filetype, verbose=verbose):
          missing.append(absolute_filename)
  return missing


def fix_in_place(filename, filetype, verbose):
  if verbose:
    print(f"Fixing {filename}")  # noqa: T001

  disclaimer = DISCLAIMERS_BY_FILETYPE[filetype]
  with open(filename, "r+") as fp:
    maybe_shebang = fp.readline()
    remaining = fp.read()

    fp.seek(0)

    if maybe_shebang.startswith("#!"):
      fp.write(maybe_shebang + disclaimer + remaining)
    else:
      fp.write(disclaimer + maybe_shebang + remaining)


def fix_all(filenames, verbose=False):
  failed_to_fix = []
  for filename in filenames:
    filetype = guess_filetype(filename)
    try:
      fix_in_place(filename, filetype, verbose=verbose)
    except Exception as e:
      print(f"failed to fix {filename}: {e}")  # noqa: T001
      failed_to_fix.append(filename)
    if not file_has_disclaimer(filename, filetype):
      print(f"fix did not work for {filename}")  # noqa: T001
      failed_to_fix.append(filename)
  return failed_to_fix


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("directories", action="extend", nargs="+", type=str)
  parser.add_argument("--fix-in-place", "-f", action="store_true")
  parser.add_argument("--verbose", "-v", action="store_true")

  args = parser.parse_args()
  missing = []
  for dirname in args.directories:
    missing.extend(check_all(dirname, verbose=args.verbose))
  if args.fix_in_place:
    missing = fix_all(missing, verbose=args.verbose)
  if missing:
    print(  # noqa: T001
      "\nThe following files failed the copyright + license check:\n\t" + "\n\t".join(f for f in missing)
    )
    sys.exit(1)
  else:
    if args.verbose:
      print("\nAll files have disclaimer")  # noqa: T001

# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os
import subprocess
import sys
import tempfile

from zigopt.common.lists import omit


def assert_experiments_equivalent(experiment1, experiment2):
  deny_list = {"client", "created", "id", "progress", "state", "updated", "user"}
  assert omit(experiment1.to_json(), *deny_list) == omit(experiment2.to_json(), *deny_list)


def run_tmp_python_module(code, append_lines):
  # HACK: the version of the python client we're using doesn't support TLS certs via environment variables so we
  # need to modify the code
  with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as f:
    code_lines = code.splitlines(True)
    certs = os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS")
    if certs:
      try:
        connection_line_idx = next(i for i, l in enumerate(code_lines) if "conn = Connection" in l)
        code_lines.insert(connection_line_idx + 1, f"conn.set_verify_ssl_certs({certs!r}){os.linesep}")
      except StopIteration:
        pass
    f.writelines(code_lines)
    f.write(os.linesep)
    f.writelines(f"{l}{os.linesep}" for l in append_lines)
    f.flush()
    return subprocess.check_output([sys.executable, f.name]).decode("utf-8")

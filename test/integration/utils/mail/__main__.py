# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import logging

from integration.utils.mail.smtp import smtp_server


def main(parsed_args):
  smtp_server(parsed_args.send_port, parsed_args.receive_port, parsed_args.verbose)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--send-port", type=int, default=6001)
  parser.add_argument("--receive-port", type=int, default=6002)
  parser.add_argument("--verbose", action="store_true")
  args = parser.parse_args()
  logging.basicConfig()
  main(args)

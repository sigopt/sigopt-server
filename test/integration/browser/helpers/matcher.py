# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
def xpath_disabled_clause(disabled):
  if disabled is None:
    return ""
  if disabled:
    return " and (@disabled)"
  return " and not(@disabled)"


def text_in_element(text, partial_match=False, disabled=None):
  if partial_match:
    return f"//*[contains(text(),{text!r}){xpath_disabled_clause(disabled)}]"
  return f"//*[text()={text!r}{xpath_disabled_clause(disabled)}]"

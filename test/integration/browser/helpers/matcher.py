# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
def xpath_disabled_clause(disabled):
  if disabled is None:
    return ""
  elif disabled:
    return " and (@disabled)"
  else:
    return " and not(@disabled)"


def text_in_element(text, partial_match=False, disabled=None):
  if partial_match:
    return f"//*[contains(text(),{text!r}){xpath_disabled_clause(disabled)}]"
  else:
    return f"//*[text()={text!r}{xpath_disabled_clause(disabled)}]"

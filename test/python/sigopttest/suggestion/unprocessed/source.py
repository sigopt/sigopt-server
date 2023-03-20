# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import re

from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion, source_to_string


class TestSerializeUnprocessedSources(object):
  def test_serialize_unprocessed_sources(self):
    patt = re.compile(r"^__[a-z_]+__$")
    sources = [
      getattr(UnprocessedSuggestion.Source, attr) for attr in dir(UnprocessedSuggestion.Source) if not patt.match(attr)
    ]
    sources = [s for s in sources if not hasattr(s, "__call__")]
    assert sources
    for source in sources:
      assert source_to_string(source)

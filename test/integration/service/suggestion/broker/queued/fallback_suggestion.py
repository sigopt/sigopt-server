# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import *
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from integration.service.suggestion.broker.test_base import SuggestionBrokerTestBase
from sigopttest.base.config_broker import StrictAccessConfigBroker


class TestFallbackSuggestion(SuggestionBrokerTestBase):
  def test_fallback_suggestion(
    self,
    services,
    experiment,
    processed_suggestion_meta,
  ):
    suggestion = services.suggestion_broker.fallback_suggestion(
      experiment,
      processed_suggestion_meta,
    )
    assert isinstance(suggestion, Suggestion)
    assert suggestion.source == UnprocessedSuggestion.Source.UNKNOWN_FALLBACK_RANDOM
    assert suggestion.experiment_id == experiment.id
    if processed_suggestion_meta.HasField("client_provided_data"):
      assert suggestion.client_provided_data == processed_suggestion_meta.client_provided_data
    else:
      assert suggestion.client_provided_data is None

  def test_has_conditionals(self, services, processed_suggestion_meta):
    services.config_broker = StrictAccessConfigBroker.from_configs(
      {
        "queue": {"forbid_random_fallback": False},
      }
    )
    experiment_meta = ExperimentMeta(
      all_parameters_unsorted=[
        ExperimentParameter(
          name="d1",
          param_type=PARAMETER_DOUBLE,
          bounds=Bounds(minimum=-1, maximum=1),
          conditions=[ParameterCondition(name="cond", values=[1])],
        ),
        ExperimentParameter(
          name="i1",
          param_type=PARAMETER_INT,
          bounds=Bounds(minimum=-14, maximum=12),
          conditions=[ParameterCondition(name="cond", values=[2])],
        ),
        ExperimentParameter(
          name="c1",
          param_type=PARAMETER_CATEGORICAL,
          all_categorical_values=[
            ExperimentCategoricalValue(name="c1_0", enum_index=0),
            ExperimentCategoricalValue(name="c1_1", enum_index=1),
          ],
          conditions=[ParameterCondition(name="cond", values=[3])],
        ),
      ],
      conditionals=[
        ExperimentConditional(
          name="cond",
          values=[
            ExperimentConditionalValue(name="activate_double", enum_index=1),
            ExperimentConditionalValue(name="activate_integer", enum_index=2),
            ExperimentConditionalValue(name="activate_categorical", enum_index=3),
          ],
        )
      ],
    )
    experiment = self.new_experiment(experiment_meta)
    services.experiment_service.insert(experiment)
    suggestion = services.suggestion_broker.fallback_suggestion(
      experiment,
      processed_suggestion_meta,
    )
    assignments = suggestion.get_assignments(experiment)
    assert len(assignments) == 2
    assert "cond" in assignments
    assert assignments["cond"] is not None
    if "d1" in assignments:
      assert assignments["d1"] is not None
    elif "i1" in assignments:
      assert assignments["i1"] is not None
    elif "c1" in assignments:
      assert assignments["c1"] is not None
    else:
      assert False

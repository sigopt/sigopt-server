# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.common.lists import list_get, max_option
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.exception.logger import SoftException
from zigopt.experiment.model import Experiment
from zigopt.optimize.sources.categorical import CategoricalOptimizationSource
from zigopt.optimize.sources.spe import SPEOptimizationSource
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMetric
from zigopt.protobuf.gen.optimize.sources_pb2 import MultimetricHyperparameters, NullHyperparameters

from integration.service.optimize.optimizer.test_base import OptimizerServiceTestBase


class TestAuxService(OptimizerServiceTestBase):
  @pytest.fixture
  def aux_service(self, services):
    return services.aux_service

  def get_setup(self, services, experiment):
    opt_args = services.optimizer.fetch_optimization_args(experiment)
    source = opt_args.source
    hyperparams = source.get_hyperparameters(opt_args)
    date_updated = current_datetime()
    return source, hyperparams, date_updated

  def get_most_recent_aux(self, experiment, aux_service):
    auxes = aux_service.get_stored_auxes(experiment)
    return max_option(auxes, key=lambda aux: aux.date_updated)

  def test_persist_hyperparameters(self, services, experiment, aux_service):
    aux = self.get_most_recent_aux(experiment, aux_service)
    assert aux is None

    source, hyperparams, date_updated = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)

    aux = self.get_most_recent_aux(experiment, aux_service)
    assert aux is not None

  def test_persist_hyperparameters_overlapping_calls(self, services, experiment, aux_service):
    source_1, hyperparams_1, date_updated_1 = self.get_setup(services, experiment)

    # new observations kick off another call to optimize hyperparameters
    self.make_observations(services, experiment, 20)
    source_2, hyperparams_2, date_updated_2 = self.get_setup(services, experiment)

    # persist first set of hyperparameters
    aux_service.persist_hyperparameters(experiment, source_1.name, hyperparams_1, date_updated_1)

    # persist second (newer) set of hyperparameters
    aux_service.persist_hyperparameters(experiment, source_2.name, hyperparams_2, date_updated_2)

    current_aux = self.get_most_recent_aux(experiment, aux_service)
    current_hyperparams = aux_service.get_hyperparameters_from_aux(
      experiment,
      source_2.hyperparameter_type,
      current_aux,
    )
    assert current_hyperparams == hyperparams_2

  def test_persist_hyperparameters_race_condition_first_aux(self, services, experiment, aux_service):
    source_1, hyperparams_1, date_updated_1 = self.get_setup(services, experiment)

    # new observations that create *and persist* hyperparameters before first one persists
    self.make_observations(services, experiment, 20)
    source_2, hyperparams_2, date_updated_2 = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(experiment, source_2.name, hyperparams_2, date_updated_2)

    # try to persist stale hyperparameters
    aux_service.persist_hyperparameters(experiment, source_1.name, hyperparams_1, date_updated_1)

    current_aux = self.get_most_recent_aux(experiment, aux_service)
    current_hyperparams = aux_service.get_hyperparameters_from_aux(
      experiment,
      source_2.hyperparameter_type,
      current_aux,
    )
    assert current_hyperparams == hyperparams_2

  def test_persist_hyperparameters_race_condition_not_first_aux(self, services, experiment, aux_service):
    init_source, init_hyperparams, init_date_updated = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(
      experiment,
      init_source.name,
      init_hyperparams,
      init_date_updated,
    )

    self.make_observations(services, experiment, 20)
    source_1, hyperparams_1, date_updated_1 = self.get_setup(services, experiment)

    # new observations that create *and persist* hyperparameters before first one persists
    self.make_observations(services, experiment, 20)
    source_2, hyperparams_2, date_updated_2 = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(experiment, source_2.name, hyperparams_2, date_updated_2)

    # try to persist stale hyperparameters
    aux_service.persist_hyperparameters(experiment, source_1.name, hyperparams_1, date_updated_1)

    current_aux = self.get_most_recent_aux(experiment, aux_service)
    current_hyperparams = aux_service.get_hyperparameters_from_aux(
      experiment,
      source_2.hyperparameter_type,
      current_aux,
    )
    assert current_hyperparams == hyperparams_2

  def test_return_none_with_mismatched_hparam_type_and_aux(
    self,
    services,
    experiment,
    aux_service,
  ):
    source, hyperparameters, date_updated = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(
      experiment,
      source.name,
      hyperparameters,
      date_updated,
    )

    assert len(experiment.optimized_metrics) == 1
    single_metric_opt_args = services.optimizer.fetch_optimization_args(
      experiment,
    )
    single_metric_source = single_metric_opt_args.source
    (single_metric_aux,) = aux_service.get_stored_auxes(experiment, source_name=single_metric_source.name)

    assert (
      aux_service.get_hyperparameters_from_aux(
        experiment,
        single_metric_source.hyperparameter_type,
        single_metric_aux,
      )
      is not None
    )

    # We have MultimetricHyperparameters with a different length
    multimetric_meta = experiment.experiment_meta.copy_protobuf()
    multimetric_meta.ClearField("metrics")
    multimetric_meta.metrics.extend([ExperimentMetric(name="not"), ExperimentMetric(name="real")])
    experiment = Experiment(experiment_meta=multimetric_meta)
    multimetric_source = type(single_metric_source)(
      services,
      experiment,
    )
    with pytest.raises(SoftException):
      aux_service.get_hyperparameters_from_aux(
        experiment,
        multimetric_source.hyperparameter_type,
        single_metric_aux,
      )

  def test_get_stored_hyperparameters(self, services, experiment, aux_service):
    source, hyperparams, date_updated = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)

    stored_hp = aux_service.get_stored_hyperparameters(experiment, source)
    assert stored_hp == hyperparams

    aux = self.get_most_recent_aux(experiment, aux_service)
    stored_hp = aux_service.get_stored_hyperparameters(experiment, source, auxes=[aux])
    assert stored_hp == hyperparams

  def test_get_hyperparameters_from_aux(self, services, experiment, aux_service):
    source, hyperparams, date_updated = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)
    aux = self.get_most_recent_aux(experiment, aux_service)
    assert aux_service.get_hyperparameters_from_aux(experiment, source.hyperparameter_type, aux) == hyperparams

  def test_get_stored_aux_none(self, services, experiment, aux_service):
    self.get_setup(services, experiment)
    assert aux_service.get_stored_auxes(experiment) == []

  @pytest.mark.parametrize("should_use_source", [True, False])
  def test_get_stored_aux(self, services, experiment, should_use_source, aux_service):
    source, hyperparams, date_updated = self.get_setup(services, experiment)
    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)
    aux = self.get_most_recent_aux(experiment, aux_service)
    date_updated = aux.date_updated

    (updated_aux,) = aux_service.get_stored_auxes(
      experiment,
      source_name=source.name if should_use_source else None,
    )

    assert updated_aux.date_updated == date_updated
    assert updated_aux.source_name == source.name

    current_aux = self.get_most_recent_aux(experiment, aux_service)
    assert current_aux.date_updated == date_updated

  def test_reset_hyperparameters(self, services, experiment, aux_service):
    spe_source = SPEOptimizationSource(services, experiment)
    spe_hyperparams = NullHyperparameters()
    spe_date_updated = current_datetime()

    aux_service.persist_hyperparameters(experiment, spe_source.name, spe_hyperparams, spe_date_updated)
    stored_auxes = aux_service.get_stored_auxes(experiment)
    assert len(stored_auxes) == 1

    aux_service.reset_hyperparameters(experiment)
    stored_auxes = aux_service.get_stored_auxes(experiment)
    assert len(stored_auxes) == 0

    mm_date_updated = current_datetime()
    mm_hyperparameters = MultimetricHyperparameters()

    aux_service.persist_hyperparameters(experiment, spe_source.name, spe_hyperparams, spe_date_updated)
    aux_service.persist_hyperparameters(
      experiment=experiment,
      source_name=CategoricalOptimizationSource.name,
      hyperparameters=mm_hyperparameters,
      current_aux_date_updated=mm_date_updated,
    )
    stored_auxes = aux_service.get_stored_auxes(experiment)
    assert len(stored_auxes) == 2

    aux_service.reset_hyperparameters(experiment)
    stored_auxes = aux_service.get_stored_auxes(experiment)
    assert len(stored_auxes) == 0

  def test_get_stored_aux_multiple_sources(self, services, experiment, aux_service):
    source, hyperparams, date_updated = self.get_setup(services, experiment)
    spe_source = SPEOptimizationSource(services, experiment)
    spe_hyperparams = NullHyperparameters()
    spe_date_updated = current_datetime()

    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)
    aux_service.persist_hyperparameters(
      experiment,
      spe_source.name,
      spe_hyperparams,
      spe_date_updated,
    )

    all_auxes = aux_service.get_stored_auxes(experiment)
    spe_auxes = aux_service.get_stored_auxes(
      experiment,
      source_name=spe_source.name,
    )

    assert len(all_auxes) == 2
    assert [aux.source_name for aux in sorted(all_auxes, key=lambda a: a.date_updated)] == [
      source.name,
      spe_source.name,
    ]
    assert len(spe_auxes) == 1
    assert spe_auxes[0].source_name == spe_source.name

  @pytest.mark.slow
  def test_no_hyper_opt_if_too_many_observations(self, services, experiment, aux_service):
    def sources_are_equal(source1, source2):
      return isinstance(source1, type(source2)) and isinstance(source2, type(source1))

    # Make sure that, if hyper_opt is called on a GP problem, it skips it when too many points are present
    source, hyperparams, date_updated = self.get_setup(services, experiment)

    optimization_args = services.optimizer.fetch_optimization_args(experiment)
    assert sources_are_equal(optimization_args.source, source)
    aux = list_get(aux_service.get_stored_auxes(experiment, source_name=optimization_args.source.name), 0)
    assert aux is None  # None because no hypers have ever been persisted

    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)
    optimization_args = services.optimizer.fetch_optimization_args(experiment)
    aux = list_get(aux_service.get_stored_auxes(experiment, source_name=optimization_args.source.name), 0)
    assert aux is not None  # Now they have been persisted so there should be something there

    self.make_observations(services, experiment, 1000)
    aux_service.persist_hyperparameters(experiment, source.name, hyperparams, date_updated)
    optimization_args = services.optimizer.fetch_optimization_args(experiment)

    # This confirms that the source for which the hyperparams were originally created is not the source after 1000 obs
    assert not sources_are_equal(optimization_args.source, source)

    # This is not fundamental (we could store something by default for each source) but this occurs because the
    # current source has never run a hyper_opt, so no hypers have been persisted for this source
    aux = list_get(aux_service.get_stored_auxes(experiment, source_name=optimization_args.source.name), 0)
    assert aux is None

    recent_aux = self.get_most_recent_aux(experiment, aux_service)
    recent_hp_from_db = aux_service.get_hyperparameters_from_aux(
      experiment,
      source.hyperparameter_type,
      recent_aux,
    )

    with pytest.raises(AssertionError):  # Cannot allow call on zero data
      services.sc_adapter.gp_hyper_opt_categorical(experiment, [], None)

    hp_from_default = source.get_hyperparameters(optimization_args)
    assert recent_hp_from_db.SerializeToString() == hp_from_default.SerializeToString()

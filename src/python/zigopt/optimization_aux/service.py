# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import func

from zigopt.common import *
from zigopt.optimization_aux.model import ExperimentOptimizationAux
from zigopt.protobuf.gen.optimize.sources_pb2 import MultimetricHyperparameters
from zigopt.services.base import Service


class BaseAuxService(Service):
  def persist_hyperparameters(self, experiment, source_name, hyperparameters, current_aux_date_updated):
    raise NotImplementedError()

  def get_stored_auxes(self, experiment, source_name=None):
    raise NotImplementedError()

  def delete_hyperparameters_for_experiment(self, experiment):
    raise NotImplementedError()

  def get_stored_hyperparameters(self, experiment, source, auxes=None):
    if auxes is None:
      auxes = self.get_stored_auxes(experiment, source_name=source.name)
    aux = find(auxes, lambda aux: aux.source_name == source.name)
    return self.get_hyperparameters_from_aux(experiment, source.hyperparameter_type, aux)

  def attempt_to_deserialize_as(self, serialized_hyperparameters, hyperparameter_type):
    protobuf_cls = hyperparameter_type
    protobuf = protobuf_cls()
    protobuf.ParseFromString(serialized_hyperparameters)

    hyperparameter_string_as_stored = protobuf.SerializeToString()
    protobuf.DiscardUnknownFields()
    interpretable_hyperparameter_string = protobuf.SerializeToString()
    if hyperparameter_string_as_stored == interpretable_hyperparameter_string:
      return protobuf, None
    inconsistency = {
      "Stored data column": hyperparameter_string_as_stored,
      "Interpreted data column": interpretable_hyperparameter_string,
      "Hyperparameter type": hyperparameter_type,
    }
    return None, inconsistency

  def get_hyperparameters_from_aux(self, experiment, hyperparameter_type, optimization_aux):
    serialized_hyperparameters = optimization_aux and optimization_aux.data_column
    if not serialized_hyperparameters:
      return None

    protobuf, inconsistency = self.attempt_to_deserialize_as(serialized_hyperparameters, hyperparameter_type)
    if protobuf:
      # we have correctly deserialized protobuf, then check if the number of experiment metrics match up
      # with number of stored metrics
      if hyperparameter_type == MultimetricHyperparameters and len(experiment.all_metrics) != len(
        protobuf.multimetric_hyperparameter_value
      ):
        inconsistency = {
          "Stored number of metrics": len(protobuf.multimetric_hyperparameter_value),
          "Experiment number of metrics": len(experiment.all_metrics),
        }
        self.services.exception_logger.soft_exception(
          msg="Mismatch MultimetricHyperparameters length and Experiment metric length",
          extra=inconsistency,
        )
        return None
    else:
      self.services.exception_logger.soft_exception(
        msg="Inconsistent hyperparameter type and aux storage",
        extra=inconsistency,
      )
      return None

    return protobuf

  def reset_hyperparameters(self, experiment):
    self.delete_hyperparameters_for_experiment(experiment)


class PostgresAuxService(BaseAuxService):
  def persist_hyperparameters(self, experiment, source_name, hyperparameters, current_aux_date_updated):
    experiment = self.services.experiment_service.find_by_id(experiment.id)
    if experiment:
      self.services.database_service.upsert(
        ExperimentOptimizationAux(
          experiment_id=experiment.id,
          source_name=source_name,
          date_updated=current_aux_date_updated,
          data_column=hyperparameters.SerializeToString(),
        ),
        where=(
          func.coalesce(ExperimentOptimizationAux.date_updated, current_aux_date_updated) <= current_aux_date_updated
        ),
        skip_none=True,
      )

  def delete_hyperparameters_for_experiment(self, experiment):
    aux_query = self.services.database_service.query(ExperimentOptimizationAux).filter(
      ExperimentOptimizationAux.experiment_id == experiment.id
    )

    self.services.database_service.delete(aux_query)

  def get_stored_auxes(self, experiment, source_name=None):
    aux_query = self.services.database_service.query(ExperimentOptimizationAux).filter(
      ExperimentOptimizationAux.experiment_id == experiment.id
    )
    if source_name is not None:
      aux_query = aux_query.filter(ExperimentOptimizationAux.source_name == source_name)

    return self.services.database_service.all(aux_query)

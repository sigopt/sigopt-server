# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import BigInteger, Column, ForeignKeyConstraint, LargeBinary, PrimaryKeyConstraint, String

from zigopt.db.column import ImpliedUTCDateTime
from zigopt.db.declarative import Base


class ExperimentOptimizationAux(Base):
  __tablename__ = "experiment_optimization_aux"
  __table_args__ = tuple(
    [
      PrimaryKeyConstraint("experiment_id", "source_name"),
      ForeignKeyConstraint(
        ["experiment_id"], ["experiments.id"], ondelete="CASCADE", name="experiment_optimization_aux_experiment_id_fkey"
      ),
    ]
  )

  experiment_id = Column(BigInteger)
  source_name = Column(String)
  date_updated = Column(ImpliedUTCDateTime)

  # Stored as binary, since different sources will deserialize the data differently
  data_column = Column(LargeBinary)

# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime as dt
from copy import deepcopy

import pytest
from mock import patch

from zigopt.common.sigopt_datetime import current_datetime

from integration.service.experiment.test_base import ExperimentServiceTestBase


class TestExperimentCacheCount(ExperimentServiceTestBase):
  @pytest.fixture
  def time_interval(self):
    now = current_datetime()
    start = now - dt.timedelta(seconds=60)
    end = now + dt.timedelta(seconds=60)
    return start, end

  def _get_redis_key(self, services, organization, time_interval):
    return services.redis_key_service.create_experiment_count_by_org_billing_key(
      organization.id,
      time_interval and time_interval[0],
    )

  def test_incr_count_by_organization_id_for_billing(
    self,
    services,
    experiment,
    time_interval,
    organization,
  ):
    key = self._get_redis_key(services, organization, time_interval)
    assert services.redis_service.exists(key) is False

    experiment2 = deepcopy(experiment)

    with patch.object(services.redis_service, "increment", wraps=services.redis_service.increment) as increment_mock:
      services.experiment_service.insert(experiment)
      services.experiment_service.incr_count_by_organization_id_for_billing(
        experiment,
        organization.id,
        time_interval,
      )
      assert services.redis_service.exists(key) is True
      assert services.redis_service.get(key) == b"1"
      assert increment_mock.call_count == 0

      services.experiment_service.insert(experiment2)
      services.experiment_service.incr_count_by_organization_id_for_billing(
        experiment2,
        organization.id,
        time_interval,
      )
      assert services.redis_service.exists(key) is True
      assert services.redis_service.get(key) == b"2"
      assert increment_mock.call_count == 1

  def test_incr_count_by_organization_id_for_billing_no_development(
    self,
    services,
    experiment,
    time_interval,
    organization,
  ):
    key = self._get_redis_key(services, organization, time_interval)
    assert services.redis_service.exists(key) is False

    new_meta = experiment.experiment_meta.copy_protobuf()
    new_meta.development = True
    experiment.experiment_meta = new_meta
    services.experiment_service.insert(experiment)
    services.experiment_service.incr_count_by_organization_id_for_billing(
      experiment,
      organization.id,
      time_interval,
    )
    assert services.redis_service.exists(key) is False

  def test_incr_count_by_organization_id_for_billing_redis_down(
    self,
    services,
    experiment,
    time_interval,
    organization,
  ):
    services.experiment_service.insert(experiment)
    with patch.object(services.redis_service, "set") as set_mock:
      set_mock.side_effect = Exception

      services.config_broker.data.setdefault("features", {})["raiseSoftExceptions"] = False
      services.experiment_service.incr_count_by_organization_id_for_billing(
        experiment,
        organization.id,
        time_interval,
      )
      assert set_mock.call_count == 1

      services.config_broker["features"]["raiseSoftExceptions"] = True
      with pytest.raises(Exception):
        services.experiment_service.incr_count_by_organization_id_for_billing(
          experiment,
          organization.id,
          time_interval,
        )
      assert set_mock.call_count == 2

  def test_count_by_organization_id_for_billing(
    self,
    services,
    experiment,
    time_interval,
    organization,
  ):
    services.experiment_service.insert(experiment)
    services.experiment_service.incr_count_by_organization_id_for_billing(
      experiment,
      organization.id,
      time_interval,
    )

    with patch.object(services.redis_service, "get", wraps=services.redis_service.get) as get_mock:
      count = services.experiment_service.count_by_organization_id_for_billing(
        organization.id,
        time_interval,
        use_cache=False,
      )
      assert count == 1
      assert get_mock.call_count == 0

      count = services.experiment_service.count_by_organization_id_for_billing(
        organization.id,
        time_interval,
        use_cache=True,
      )
      assert count == 1
      assert get_mock.call_count == 1

  def test_count_by_organization_id_for_billing_no_redis(
    self,
    services,
    experiment,
    time_interval,
    organization,
  ):
    services.experiment_service.insert(experiment)
    with patch.object(services.redis_service, "set") as set_mock:
      set_mock.side_effect = Exception
      with patch.object(services.redis_service, "get") as get_mock:
        get_mock.side_effect = Exception

        services.config_broker.setdefault("features", {})["raiseSoftExceptions"] = False
        count = services.experiment_service.count_by_organization_id_for_billing(
          organization.id,
          time_interval,
          use_cache=True,
        )
        assert count == 1
        assert set_mock.call_count == 1
        assert get_mock.call_count == 1

        services.config_broker["features"]["raiseSoftExceptions"] = True
        with pytest.raises(Exception):
          services.experiment_service.count_by_organization_id_for_billing(
            organization.id,
            time_interval,
            use_cache=True,
          )
        assert get_mock.call_count == 2
        assert set_mock.call_count == 1

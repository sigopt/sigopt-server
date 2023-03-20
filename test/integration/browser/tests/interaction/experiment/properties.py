# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-
import json
import re

import pytest

from zigopt.common import *
from zigopt.common.strings import random_string
from zigopt.project.model import MAX_ID_LENGTH as MAX_PROJECT_ID_LENGTH

from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META


class TestProperties(ExperimentBrowserTest):
  def editing(self, driver, experiment):
    class _Editing(object):
      @classmethod
      def __enter__(cls):
        self.navigate_to_experiment_page(driver, experiment, "Properties", "/properties")
        driver.find_and_click(element_text="Edit")
        driver.wait_for_element_by_css_selector(".create-button")

      @classmethod
      def __exit__(cls, exc_type, value, traceback):
        driver.find_and_click(css_selector="a.btn.submit-button.create-button")
        driver.wait_for_element_by_text("Edit")
        driver.wait_for_element_by_css_selector(".experiment-table-holder")

    return _Editing()

  @pytest.fixture
  def multimetric_experiment(self, api_connection, unicode_experiment_meta):
    meta = unicode_experiment_meta
    meta["observation_budget"] = 100
    meta["metrics"] = [{"name": "first metric"}, {"name": "second metric"}]
    e = api_connection.create_experiment(meta)
    return e

  @pytest.fixture
  def experiment_with_threshold(self, api_connection, unicode_experiment_meta):
    meta = unicode_experiment_meta
    meta["observation_budget"] = 100
    meta["metrics"] = [{"name": "first metric", "threshold": 11.2}, {"name": "second metric"}]
    e = api_connection.create_experiment(meta)
    return e

  @pytest.fixture
  def experiment_runs_only(self, api_connection, unicode_experiment_meta, project):
    meta = unicode_experiment_meta
    meta["budget"] = 10
    meta["runs_only"] = True
    meta["project"] = project.id
    e = api_connection.create_experiment(meta)
    return e

  def test_edit_name(self, logged_in_driver, api_connection, experiment):
    driver = logged_in_driver
    with self.editing(driver, experiment):
      driver.find_and_send_keys(
        css_selector=".experiment-properties .name-input input", keys="experiment name", clear=True
      )
    e = api_connection.experiments(experiment.id).fetch()
    assert e.name == "experiment name"

  def test_add_threshold(self, logged_in_driver, api_connection, multimetric_experiment):
    driver = logged_in_driver
    metric_element_selector = ".metrics-table tbody:nth-child(1)"
    with self.editing(driver, multimetric_experiment):
      driver.find_and_click(css_selector=f"{metric_element_selector} .threshold-input .create-threshold-button")
      driver.find_and_send_keys(
        css_selector=f"{metric_element_selector} .threshold-input input",
        keys="0.1",
      )
    threshold_element = driver.find_element_by_css_selector(
      css_selector=f'{metric_element_selector} tr[data-key="threshold"] td',
    )
    assert threshold_element.text == "0.1"
    updated_experiment = api_connection.experiments(multimetric_experiment.id).fetch()
    assert updated_experiment.metrics[0].threshold == 0.1
    assert updated_experiment.metrics[1].threshold is None

  def test_remove_threshold(self, logged_in_driver, api_connection, experiment_with_threshold):
    driver = logged_in_driver
    metric_element_selector = ".metrics-table tbody:nth-child(1)"
    with self.editing(driver, experiment_with_threshold):
      driver.find_and_click(css_selector=f"{metric_element_selector} .threshold-input .remove-threshold-button")
    threshold_element = driver.find_element_by_css_selector(
      css_selector=f'{metric_element_selector} tr[data-key="threshold"] td',
    )
    assert threshold_element.text == ""
    updated_experiment = api_connection.experiments(experiment_with_threshold.id).fetch()
    assert all(metric.threshold is None for metric in updated_experiment.metrics)

  def test_add_parameter(self, logged_in_driver, api_connection, experiment):
    driver = logged_in_driver
    with self.editing(driver, experiment):
      driver.find_and_click(element_text="Add Parameter")
      driver.find_and_send_keys(css_selector='tr[data-parameter-name=""] input[name="name"]', keys="w", clear=True)
      driver.find_and_send_keys(css_selector='tr[data-parameter-name="w"] .min-input', keys="100", clear=True)
      driver.find_and_send_keys(css_selector='tr[data-parameter-name="w"] .max-input', keys="1000", clear=True)
      driver.find_and_send_keys(
        css_selector='tr[data-parameter-name="w"] input[name="default_value"]', keys="500", clear=True
      )
    e = api_connection.experiments(experiment.id).fetch()
    assert len(e.parameters) == len(experiment.parameters) + 1
    w_parameter = find(e.parameters, lambda p: p.name == "w")
    assert w_parameter.bounds.min == 100
    assert w_parameter.bounds.max == 1000

  def test_remove_parameter(self, logged_in_driver, api_connection, experiment):
    driver = logged_in_driver
    with self.editing(driver, experiment):
      driver.find_and_click(css_selector='tr[data-parameter-name="ೠ"] .remove-parameter-button')
    e = api_connection.experiments(experiment.id).fetch()
    assert len(e.parameters) == len(experiment.parameters) - 1
    assert find(e.parameters, lambda p: p.name == "°") is not None
    assert find(e.parameters, lambda p: p.name == "ೠ") is None
    assert find(e.parameters, lambda p: p.name == "🌎") is not None

  def test_edit_parameters(self, logged_in_driver, api_connection, experiment):
    driver = logged_in_driver
    with self.editing(driver, experiment):
      driver.find_and_send_keys(css_selector='tr[data-parameter-name="°"] .min-input', keys="5", clear=True)
      driver.find_and_send_keys(css_selector='tr[data-parameter-name="°"] .max-input', keys="45", clear=True)
      driver.find_and_click(
        css_selector="tr .categorical-value-input .rbt-token-remove-button",
      )
      driver.find_and_send_keys(
        css_selector="tr .categorical-value-input input",
        keys="c₤",
      )
      driver.find_and_click(css_selector="tr .categorical-value-input .dropdown-menu a")
    e = api_connection.experiments(experiment.id).fetch()
    x_parameter = find(e.parameters, lambda p: p.name == "°")
    y_parameter = find(e.parameters, lambda p: p.name == "ೠ")
    z_parameter = find(e.parameters, lambda p: p.name == "🌎")
    assert x_parameter.bounds.min == 5
    assert x_parameter.bounds.max == 45
    assert y_parameter.bounds.min == -50
    assert y_parameter.bounds.max == 0
    assert {cv.name for cv in z_parameter.categorical_values} == {"c₤", "e🐧"}

  @pytest.fixture
  def project(self, api_connection, experiment):
    return (
      api_connection.clients(experiment.client)
      .projects()
      .create(
        id=random_string(MAX_PROJECT_ID_LENGTH).lower(),
        name=f"test project for {type(self).__name__}",
      )
    )

  @pytest.fixture
  def runs_experiment(self, api_connection, project):
    return (
      api_connection.clients(project.client).projects(project.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    )

  def test_archive_cancel(self, logged_in_driver, experiment):
    driver = logged_in_driver
    e = experiment
    driver.get_path(f"/experiment/{e.id}/properties", title_text="Properties")
    driver.find_and_click(element_text="Archive Experiment")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal .btn.cancel")
    driver.wait_while_present(css_selector=".modal.fade.in")
    driver.get_path(f"/experiment/{e.id}/properties", title_text="Properties")
    driver.find_element_by_text("Archive Experiment")

  def test_archive(self, logged_in_driver, runs_experiment, api_connection):
    driver = logged_in_driver
    e = runs_experiment
    api_connection.aiexperiments(e.id).training_runs().create(name="test run")
    driver.get_path(f"/aiexperiment/{e.id}/properties", title_text="Properties")
    driver.find_and_click(element_text="Archive Experiment")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal .btn.archive")
    driver.wait_for_path(f"/aiexperiment/{e.id}/properties")
    driver.wait_for_element_by_css_selector(".deleted-alert")
    runs_page = (
      api_connection.clients(e.client)
      .projects(e.project)
      .training_runs()
      .fetch(filters=json.dumps([{"operator": "==", "field": "experiment", "value": e.id}]))
    )
    assert runs_page.count == 1
    assert len(runs_page.data) == 1
    for run in runs_page.data:
      assert not run.deleted

  def test_archive_with_runs(self, logged_in_driver, runs_experiment, api_connection):
    driver = logged_in_driver
    e = runs_experiment
    api_connection.aiexperiments(e.id).training_runs().create(name="test run")
    driver.get_path(f"/aiexperiment/{e.id}/properties", title_text="Properties")
    driver.find_and_click(element_text="Archive Experiment")
    driver.wait_for_element_by_css_selector(".modal.fade.in")
    driver.find_and_click(css_selector=".modal .toggle-runs")
    driver.find_and_click(css_selector=".modal .btn.archive")
    driver.wait_for_path(f"/aiexperiment/{e.id}/properties")
    driver.wait_for_element_by_css_selector(".deleted-alert")
    runs_page = (
      api_connection.clients(e.client)
      .projects(e.project)
      .training_runs()
      .fetch(filters=json.dumps([{"operator": "==", "field": "experiment", "value": e.id}]))
    )
    assert runs_page.count == 1
    assert len(runs_page.data) == 1
    for run in runs_page.data:
      assert run.deleted

  def test_unarchive(self, logged_in_driver, experiment, api_connection):
    api_connection.experiments(experiment.id).delete()
    driver = logged_in_driver
    e = experiment
    driver.get_path(f"/experiment/{e.id}/properties", title_text="Properties")
    driver.find_and_click(element_text="Unarchive")
    driver.wait_while_present(css_selector=".deleted-alert")

    driver.get_path(f"/experiment/{e.id}/properties", title_text="Properties")
    driver.find_clickable(element_text="Archive Experiment")

  def test_duplicate(self, logged_in_driver, api_connection, experiment_with_conditionals):
    driver = logged_in_driver
    e = experiment_with_conditionals
    driver.get_path(f"/experiment/{e.id}/properties", title_text="Properties")
    driver.find_and_click(element_text="Duplicate Experiment")
    driver.find_and_click(css_selector=".duplicate-modal form button")
    driver.wait_for_element_by_text(element_text=f"{e.name} Copy")
    match = re.search(r"/experiment/(\d+)/properties", driver.current_url)
    experiment_id = match.group(1)
    e = api_connection.experiments(experiment_id).fetch()
    assert len(e.conditionals) == 1
    assert all(len(p.conditions) > 0 for p in e.parameters)

  def test_view_constraints(self, logged_in_driver, api_connection, experiment_with_constraints):
    driver = logged_in_driver
    e = experiment_with_constraints
    driver.get_path(f"/experiment/{e.id}/properties", title_text="Properties")
    assert len(driver.find_elements_by_css_selector(".experiment-constraints tr")) == 2
    assert driver.find_element_by_text("alpha🤖 + beta + gamma <= 1")
    assert driver.find_element_by_text("3 * alpha🤖 + -5 * beta >= 0")

  def test_edit_parallel_bandwidth(self, logged_in_driver, api_connection, experiment):
    driver = logged_in_driver
    with self.editing(driver, experiment):
      driver.find_and_send_keys(
        css_selector=".experiment-properties .parallel-bandwidth-input input",
        keys="3",
        clear=True,
      )
    e = api_connection.experiments(experiment.id).fetch()
    assert e.parallel_bandwidth == 3

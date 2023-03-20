# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-

import pytest

from integration.browser.tests.browser_test import BrowserTest


class ExperimentBrowserTest(BrowserTest):
  @pytest.fixture
  def unicode_experiment_meta(self):
    return dict(
      name="unicode 🐠 experiment",
      parameters=[
        dict(name="°", type="int", bounds=dict(min=1, max=50)),
        dict(name="ೠ", type="double", bounds=dict(min=-50, max=0)),
        dict(name="🌎", type="categorical", categorical_values=[dict(name="d🐤"), dict(name="e🐧")]),
      ],
    )

  @pytest.fixture
  def experiment(self, api_connection, unicode_experiment_meta):
    """
        Experiment meant to be used to test basic page loading.
        """
    return api_connection.create_experiment(unicode_experiment_meta)

  @pytest.fixture
  def experiment_with_data(self, api_connection, experiment):
    """
        Experiment meant to be used to test basic page loading. Includes observations.
        """
    s = api_connection.experiments(experiment.id).suggestions().create()
    api_connection.experiments(experiment.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      values=[{"value": 1}],
    )
    api_connection.experiments(experiment.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      values=[{"value": 1.5}],
    )
    api_connection.experiments(experiment.id).observations().create(
      suggestion=s.id,
      no_optimize=True,
      failed=True,
    )
    return experiment

  @pytest.fixture
  def experiment_with_suggestions(self, api_connection, experiment):
    """
        Experiment with suggestions.
        """
    api_connection.experiments(experiment.id).suggestions().create()
    return experiment

  @pytest.fixture
  def development_experiment(self, development_api_connection, unicode_experiment_meta):
    return development_api_connection.create_experiment(unicode_experiment_meta)

  @pytest.fixture
  def experiment_with_conditionals(self, api_connection, unicode_experiment_meta):
    unicode_experiment_meta["conditionals"] = [dict(name="c1🤖", values=["a🙈", "b🙉", "c🙊"])]
    unicode_experiment_meta["parameters"][0]["conditions"] = {"c1🤖": ["a🙈", "b🙉", "c🙊"]}
    unicode_experiment_meta["parameters"][1]["conditions"] = {"c1🤖": ["b🙉", "c🙊"]}
    unicode_experiment_meta["parameters"][2]["conditions"] = {"c1🤖": ["c🙊"]}
    return api_connection.create_experiment(unicode_experiment_meta)

  @pytest.fixture
  def ascii_experiment_meta(self):
    return dict(
      name="ascii experiment",
      parameters=[
        dict(name="a", type="int", bounds=dict(min=1, max=50)),
        dict(name="b", type="double", bounds=dict(min=-50, max=0)),
        dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
      ],
    )

  @pytest.fixture
  def ascii_experiment(self, api_connection, ascii_experiment_meta):
    return api_connection.create_experiment(ascii_experiment_meta)

  @pytest.fixture
  def experiment_with_constraints(self, api_connection):
    return api_connection.create_experiment(
      dict(
        name="Experiment with constraints",
        parameters=[
          dict(name="alpha🤖", type="double", bounds=dict(min=0.0, max=1.0)),
          dict(name="beta", type="double", bounds=dict(min=0.0, max=1.0)),
          dict(name="gamma", type="double", bounds=dict(min=0.0, max=1.0)),
          dict(name="nodes", type="int", bounds=dict(min=1, max=10)),
        ],
        linear_constraints=[
          # Constraint equation: alpha + beta + gamma <= 1
          dict(
            type="less_than",
            threshold=1,
            terms=[dict(name="alpha🤖", weight=1), dict(name="beta", weight=1), dict(name="gamma", weight=1)],
          ),
          # Constraint equation: 3 * alpha - 5 * beta >= 0
          dict(type="greater_than", threshold=0, terms=[dict(name="alpha🤖", weight=3), dict(name="beta", weight=-5)]),
        ],
      )
    )

  def navigate_to_experiment_page(self, driver, experiment, page_title, sub_path="", **kwargs):
    real_path = f"/experiment/{experiment.id}{sub_path}"
    driver.get_path(real_path, title_text=f"{experiment.name} - {page_title} - SigOpt", **kwargs)

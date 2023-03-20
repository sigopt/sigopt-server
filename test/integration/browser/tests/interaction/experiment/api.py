# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.browser.tests.interaction.experiment.test_base import ExperimentBrowserTest
from integration.utils.autogen_code import assert_experiments_equivalent, run_tmp_python_module


class TestAPIPage(ExperimentBrowserTest):
  def test_code_block(self, logged_in_driver, api_connection, logged_in_web_connection, experiment):
    self.navigate_to_experiment_page(logged_in_driver, experiment, "API", "/api")
    experiment_code = logged_in_driver.find_element_by_css_selector(".code-block").text
    # module contains auto-generated code which has been run by the time
    # we get module (since auto-gen code is all top-level, it runs on import)
    output = run_tmp_python_module(experiment_code, append_lines=["print(experiment.id)"])
    new_experiment_id = output.splitlines()[-1]
    # test that we didn't just fetch the same experiment
    assert new_experiment_id != experiment.id
    new_experiment = api_connection.experiments(new_experiment_id).fetch()
    # test that fields we expect to be the same are the same
    assert_experiments_equivalent(new_experiment, experiment)

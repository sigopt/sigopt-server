/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/report.less";
import "../../../../experiment/task_section.less";

import React from "react";

import Component from "../../../../react/component";
import ExperimentPage from "../../page_wrapper";
import ui from "../../../../experiment/ui";
import {AssignmentsTable} from "../../../../experiment/model_evaluation";
import {DOCS_URL} from "../../../../net/constant";
import {MeasurementsView} from "../../../../experiment/measurements";
import {TaskView} from "../../../../experiment/task";
import {promiseFinally} from "../../../../utils";

const getInitialState = function () {
  return {
    assignmentsInput: ui.getInitialAssignments(this.props.experiment),
    failureInput: false,
    submitting: false,
    taskInput: ui.getInitialTask(this.props.experiment),
    valuesInput: ui.getInitialValues(this.props.experiment),
  };
};

export default class ExperimentReportPage extends Component {
  state = getInitialState.apply(this);

  onAssignmentsChange = (assignmentsInput) => this.setState({assignmentsInput});

  onMetricsChange = (valuesInput, failureInput) =>
    this.setState({failureInput, valuesInput});

  onTaskChange = (taskInput) => this.setState({taskInput});

  submitReport = () => {
    const sanitizedAssignments = ui.sanitizeAssignments(
      this.props.experiment,
      this.state.assignmentsInput,
    );
    const sanitizedValues = this.state.failureInput
      ? null
      : ui.sanitizeValues(this.state.valuesInput);
    if (
      ui.validateObservationInput(
        this.props.experiment,
        {
          assignments: sanitizedAssignments,
          failed: this.state.failureInput,
          values: sanitizedValues,
        },
        (msg) => this.services.alertBroker.show(msg),
      )
    ) {
      this.setState({submitting: true});
      promiseFinally(
        this.services.promiseApiClient
          .experiments(this.props.experiment.id)
          .observations()
          .create({
            assignments: sanitizedAssignments,
            failed: this.state.failureInput,
            values: sanitizedValues,
            task: this.state.taskInput,
          })
          .then(() => {
            this.setState(getInitialState.apply(this));
            this.services.alertBroker.show("Observation recorded!", "success");
          }, this.services.alertBroker.errorHandlerThatExpectsStatus(400, 403)),
        () => this.setState({submitting: false}),
      );
    }
  };

  render() {
    const csvUrl = `/experiment/${this.props.experiment.id}/report/file`;
    return (
      <ExperimentPage {...this.props} className="experiment-report-page">
        <div className="add-data-block">
          <h2 className="subtitle">Add Data</h2>
          <div className="report-description">
            If you want to perform an experiment with your own parameter
            configuration, you can manually report an observation below.
          </div>
          <div className="metrics-section">
            <MeasurementsView
              editing={true}
              experiment={this.props.experiment}
              failed={this.state.failureInput}
              measurements={this.state.valuesInput}
              onChange={this.onMetricsChange}
              submitting={this.state.submitting}
            />
          </div>
          <div className="assignments-section">
            <AssignmentsTable
              assignments={this.state.assignmentsInput}
              editing={true}
              experiment={this.props.experiment}
              onChange={this.onAssignmentsChange}
              submitting={this.state.submitting}
            />
          </div>
          {this.props.experiment.tasks ? (
            <div className="task-section">
              <TaskView
                creating={true}
                onChange={this.onTaskChange}
                submitting={this.state.submitting}
                task={this.state.taskInput}
                taskList={this.props.experiment.tasks}
              />
            </div>
          ) : null}
          <div className="form-group centered-button-holder">
            <button
              className="btn btn-lg btn-primary submit-button"
              disabled={this.state.submitting}
              onClick={this.state.submitting ? null : this.submitReport}
              type="button"
            >
              Add
            </button>
          </div>
          <div>
            <div className="alternative-uploads-block">
              <p className="alternative-uploads">
                You can also upload your results{" "}
                <a href={DOCS_URL}>through the API</a>, or you can{" "}
                <a href={csvUrl}>bulk upload</a> your data in CSV format.
              </p>
            </div>
          </div>
        </div>
      </ExperimentPage>
    );
  }
}

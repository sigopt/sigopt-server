/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/suggestions.less";
import "./page.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../../../../react/component";
import ExperimentPage from "../../page_wrapper";
import Loading from "../../../../component/loading";
import QueuedSuggestionModal from "../../../../queued_suggestion/modal";
import SuggestionTable from "../../../../suggestion/table";
import Tooltip from "../../../../component/tooltip";
import schemas from "../../../../react/schemas";
import ui from "../../../../experiment/ui";
import {AssignmentsTable} from "../../../../experiment/model_evaluation";
import {MeasurementsView} from "../../../../experiment/measurements";
import {promiseFinally} from "../../../../utils";

const convertValuesToMapping = (values) =>
  _.chain(values)
    .map((value) => [value.name, _.omit(value, "name")])
    .object()
    .value();

class AddCompletedRunComponent extends Component {
  state = {};

  componentDidMount() {
    this.resetState();
  }

  resetState = () =>
    this.setState({
      assignmentsInput: {},
      failureInput: false,
      submitting: false,
      valuesInput: [],
    });

  onAssignmentsChange = (assignmentsInput) => this.setState({assignmentsInput});

  onMetricsChange = (valuesInput, failureInput) =>
    this.setState({failureInput, valuesInput});

  submit = () => {
    this.setState({submitting: true}, () => {
      const sanitizedAssignments = ui.sanitizeAssignments(
        this.props.experiment,
        this.state.assignmentsInput,
      );
      const sanitizedValues = this.state.failureInput
        ? null
        : convertValuesToMapping(ui.sanitizeValues(this.state.valuesInput));
      promiseFinally(
        this.services.promiseApiClient
          .aiexperiments(this.props.experiment.id)
          .trainingRuns()
          .create({
            name: `Experiment: ${this.props.experiment.id} - Manually Entered Run`,
            values: sanitizedValues,
            assignments: sanitizedAssignments,
            state: this.state.failureInput ? "failed" : "completed",
          })
          .then(() => {
            this.services.alertBroker.show(
              <>
                Run added successfully. View your recent data on the{" "}
                <a
                  href={ui.getExperimentUrl(this.props.experiment, "/history")}
                >
                  history page
                </a>
                {""}.
              </>,
              "success",
            );
            this.resetState();
          }, this.services.alertBroker.errorHandlerThatExpectsStatus(400, 403)),
        () => this.setState({submitting: false}),
      );
    });
  };

  render() {
    return (
      <div className="add-completed-run">
        <MeasurementsView
          editing={true}
          experiment={this.props.experiment}
          failed={this.state.failureInput}
          measurements={this.state.valuesInput}
          onChange={this.onMetricsChange}
          submitting={this.state.submitting}
        />
        <AssignmentsTable
          assignments={this.state.assignmentsInput}
          editing={true}
          experiment={this.props.experiment}
          onChange={this.onAssignmentsChange}
          submitting={this.state.submitting}
        />
        <a
          className="add-run-btn btn btn-lg btn-primary"
          disabled={this.state.submitting}
          onClick={this.submit}
        >
          Add Run
        </a>
      </div>
    );
  }
}

class InformOptimizerPage extends Component {
  static propTypes = {
    canEdit: PropTypes.bool.isRequired,
    experiment: schemas.Experiment.isRequired,
  };

  state = {};
  _queuedSuggestionModal = React.createRef();

  componentDidMount() {
    // TODO(SN-1038): Old Route
    this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .queuedSuggestions()
      .exhaustivelyPage()
      .then((queuedSuggestions) => this.setState({queuedSuggestions}));
  }

  showQueuedParamsModal = (s) => this._queuedSuggestionModal.current.show(s);
  newQueuedParamsModal = () => this._queuedSuggestionModal.current.createNew();
  addQueuedSuggestion = (s) =>
    this.setState(({queuedSuggestions}) => ({
      queuedSuggestions: [s].concat(queuedSuggestions),
    }));
  removeQueuedSuggestion = ({id}) =>
    this.setState(({queuedSuggestions}) => ({
      queuedSuggestions: _.reject(queuedSuggestions, (q) => q.id === id),
    }));

  render() {
    return (
      <div>
        <QueuedSuggestionModal
          canEdit={this.props.canEdit}
          experiment={this.props.experiment}
          onQueuedSuggestionCreated={this.addQueuedSuggestion}
          onQueuedSuggestionDeleted={this.removeQueuedSuggestion}
          createTitle="Queue Parameters"
          viewTitle="Queued Parameters"
          deleteMessage="Queued parameters deleted"
          createMessage="Parameters queued"
          ref={this._queuedSuggestionModal}
        />
        <div className="queued-suggestion-section">
          <div>
            <h2>
              <Tooltip tooltip="Queued parameter configurations are prioritized for new Runs created in this Experiment.">
                Queued Parameters
              </Tooltip>
            </h2>
            <Loading
              loading={!this.state.queuedSuggestions}
              empty={_.isEmpty(this.state.queuedSuggestions)}
            >
              <SuggestionTable
                {...this.props}
                experiment={this.props.experiment}
                onSelectSuggestion={this.showQueuedParamsModal}
                suggestions={this.state.queuedSuggestions || []}
              />
            </Loading>
          </div>
          {this.props.canEdit && (
            <button
              className="btn btn-sm btn-primary queued-suggestion-button"
              onClick={this.newQueuedParamsModal}
              type="button"
            >
              Queue Parameters
            </button>
          )}
        </div>
        <div className="add-runs-section">
          <h2>Add Completed Runs</h2>
          <AddCompletedRunComponent experiment={this.props.experiment} />
        </div>
      </div>
    );
  }
}

export default function ExperimentInformOptimizerPage(props) {
  return (
    <ExperimentPage className="experiment-suggestions-page" {...props}>
      <InformOptimizerPage {...props} />
    </ExperimentPage>
  );
}

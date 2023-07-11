/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../experiment/task_section.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../react/component";
import Loading from "../component/loading";
import ModalForm from "../component/modal/form";
import schemas from "../react/schemas";
import ui from "../experiment/ui";
import {
  AssignmentsTable,
  ModelEvaluationComponent,
} from "../experiment/model_evaluation";
import {TaskView} from "../experiment/task.js";
import {promiseFinally} from "../utils";

export default class QueuedSuggestionModal extends Component {
  static propTypes = {
    canEdit: PropTypes.bool.isRequired,
    createMessage: PropTypes.string,
    createTitle: PropTypes.string,
    deleteMessage: PropTypes.string,
    experiment: schemas.Experiment.isRequired,
    onQueuedSuggestionCreated: PropTypes.func,
    onQueuedSuggestionDeleted: PropTypes.func,
    viewTitle: PropTypes.string,
  };

  static defaultProps = {
    createMessage: "Suggestion queued successfully",
    createTitle: "Queue Suggestion",
    deleteMessage: "Queued suggestion deleted",
    onQueuedSuggestionCreated: _.noop,
    onQueuedSuggestionDeleted: _.noop,
    viewTitle: "Queued Suggestion",
  };

  constructor(...args) {
    super(...args);
    this.state = {
      assignmentsInput: null,
      taskInput: null,
      creating: false,
      queuedSuggestion: null,
      submitting: false,
    };
    this._modal = React.createRef();
  }

  extractStateFromQueuedSuggestion = (queuedSuggestion) => ({
    assignmentsInput: ui.getInitialAssignments(this.props.experiment),
    taskInput: ui.getInitialTask(this.props.experiment),
    creating: false,
    queuedSuggestion,
    submitting: false,
  });

  deleteQueuedSuggestion = () => {
    this.setState({submitting: true});
    return this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .queuedSuggestions(this.state.queuedSuggestion.id)
      .delete()
      .then(
        () => {
          this.services.alertBroker.info(this.props.deleteMessage);
          setTimeout(() => this._modal.current.hide(), 2000);
          this.props.onQueuedSuggestionDeleted(this.state.queuedSuggestion);
        },
        (err) => {
          this.setState({submitting: false});
          return this.services.alertBroker.errorHandlerThatExpectsStatus(
            403,
            404,
          )(err);
        },
      );
  };

  createSuggestion = () => {
    const sanitizedAssignments = ui.sanitizeAssignments(
      this.props.experiment,
      this.state.assignmentsInput,
    );
    if (
      ui.validateAssignmentsInput(
        this.props.experiment,
        sanitizedAssignments,
        (msg) => this.services.alertBroker.show(msg),
      )
    ) {
      this.setState({submitting: true});
      promiseFinally(
        this.services.promiseApiClient
          .experiments(this.props.experiment.id)
          .queuedSuggestions()
          .create({
            assignments: sanitizedAssignments,
            task: this.state.taskInput,
          })
          .then((queuedSuggestion) => {
            this.props.onQueuedSuggestionCreated(queuedSuggestion);
            this.services.alertBroker.show(this.props.createMessage, "success");
            this.setState(
              this.extractStateFromQueuedSuggestion(queuedSuggestion),
            );
          }, this.services.alertBroker.errorHandlerThatExpectsStatus(400, 403, 404)),
        () => this.setState({submitting: false}),
      );
    }
  };

  createNew() {
    this.show({});
    this.setState({creating: true});
  }

  show(queuedSuggestion) {
    this.setState(this.extractStateFromQueuedSuggestion(queuedSuggestion), () =>
      this._modal.current.show(this.services.alertBroker.clearAlerts),
    );
  }

  render() {
    const leftButtonSection = !this.state.creating && this.props.canEdit && (
      <button
        className="btn delete-btn"
        disabled={this.state.submitting}
        onClick={this.deleteQueuedSuggestion}
        type="button"
      >
        Delete
      </button>
    );
    const bottomButtonSection = this.state.creating && (
      <>
        <button
          className="btn cancel-submit-btn"
          disabled={this.state.submitting}
          onClick={() => this._modal.current.hide()}
          type="button"
        >
          Cancel
        </button>
        <button
          className="btn submit-btn"
          disabled={this.state.submitting}
          onClick={this.createSuggestion}
          type="button"
        >
          Queue
        </button>
      </>
    );
    return (
      <ModalForm
        ref={this._modal}
        title={
          this.state.creating ? this.props.createTitle : this.props.viewTitle
        }
      >
        <div className="observation-modal">
          <Loading loading={!this.state.queuedSuggestion}>
            <div className="button-section">
              <div className="left-button-section">{leftButtonSection}</div>
            </div>
            <div className="model-evaluation-section">
              {this.state.creating ? (
                <div className="model-evaluation-component">
                  {this.props.experiment.tasks ? (
                    <div className="task-section">
                      <div className="display-row">
                        <TaskView
                          creating={true}
                          onChange={(taskInput) => this.setState({taskInput})}
                          submitting={this.state.submitting}
                          task={this.state.taskInput}
                          taskList={this.props.experiment.tasks}
                        />
                      </div>
                    </div>
                  ) : null}
                  <div className="assignments-section">
                    <div className="display-row">
                      <AssignmentsTable
                        assignments={this.state.assignmentsInput}
                        editing={true}
                        experiment={this.props.experiment}
                        onChange={(assignmentsInput) =>
                          this.setState({assignmentsInput})
                        }
                        submitting={this.state.submitting}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <ModelEvaluationComponent
                  alertBroker={this.services.alertBroker}
                  experiment={this.props.experiment}
                  suggestion={this.state.queuedSuggestion}
                />
              )}
            </div>
            <div className="button-section">
              <div className="center-button-section">{bottomButtonSection}</div>
            </div>
          </Loading>
        </div>
      </ModalForm>
    );
  }
}

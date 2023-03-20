/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../react/component";
import Loading from "../component/loading";
import ModalForm from "../component/modal/form";
import schemas from "../react/schemas";
import ui from "./ui";
import {ModelEvaluationComponent} from "./model_evaluation";
import {promiseFinally} from "../utils";

export default class ObservationModal extends Component {
  static propTypes = {
    canEdit: PropTypes.bool.isRequired,
    children: PropTypes.node,
    experiment: schemas.Experiment.isRequired,
    onObservationDeleted: PropTypes.func,
    onObservationUpdated: PropTypes.func,
  };

  static defaultProps = {
    onObservationDeleted: _.noop,
    onObservationUpdated: _.noop,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      editing: false,
      observation: {},
      submitting: false,
      suggestion: null,
    };
    this._modal = React.createRef();
  }

  extractStateFromObservation = (observation) => ({
    assignmentsInput: observation.assignments,
    editing: false,
    failureInput: observation.failed,
    observation,
    submitting: false,
    valuesInput: observation.values,
  });

  getObservationInput() {
    return _.extend({}, this.state.observation, {
      assignments: this.state.assignmentsInput,
      failed: this.state.failureInput,
      values: this.state.valuesInput,
    });
  }

  updateObservation = () => {
    const sanitizedObservation = ui.sanitizeObservation(
      this.props.experiment,
      this.getObservationInput(),
      this.state.observation,
    );
    if (
      ui.validateObservationInput(
        this.props.experiment,
        sanitizedObservation,
        (msg) => this.services.alertBroker.show(msg),
      )
    ) {
      this.setState({submitting: true});
      promiseFinally(
        this.services.promiseApiClient
          .experiments(this.props.experiment.id)
          .observations(this.state.observation.id)
          .update(sanitizedObservation)
          .then((newObservation) => {
            this.setState(this.extractStateFromObservation(newObservation));
            this.services.alertBroker.info("Observation updated");
            this.props.onObservationUpdated(newObservation);
          }, this.services.alertBroker.errorHandlerThatExpectsStatus(400, 403, 404)),
        () => this.setState({submitting: false}),
      );
    }
  };

  deleteObservation = () => {
    this.setState({submitting: true});
    return this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .observations(this.state.observation.id)
      .delete()
      .then(
        () => {
          this.services.alertBroker.info("Observation deleted");
          setTimeout(() => this._modal.current.hide(), 2000);
          this.props.onObservationDeleted();
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

  show(observation, next) {
    if (observation.suggestion) {
      this.services.promiseApiClient
        .experiments(this.props.experiment.id)
        .suggestions(observation.suggestion)
        .fetch()
        .then(
          (suggestion) => this.setState({suggestion}),
          this.services.alertBroker.errorHandlerThatExpectsStatus(404),
        );
    }
    this.setState(this.extractStateFromObservation(observation), () =>
      this._modal.current.show(() => {
        this.services.alertBroker.clearAlerts();
        return next && next();
      }),
    );
  }

  render() {
    const leftButtonSection = this.state.editing && (
      <button
        className="btn delete-btn"
        disabled={this.state.submitting}
        onClick={this.deleteObservation}
        type="button"
      >
        Delete
      </button>
    );
    const rightButtonSection = this.state.editing ? (
      <>
        <button
          className="btn cancel-btn"
          disabled={this.state.submitting}
          onClick={() =>
            this.setState((prevState) =>
              this.extractStateFromObservation(prevState.observation),
            )
          }
          type="button"
        >
          Cancel
        </button>
        <button
          className="btn finish-btn"
          disabled={this.state.submitting}
          onClick={this.updateObservation}
          type="button"
        >
          Finish
        </button>
      </>
    ) : (
      this.props.canEdit && (
        <button
          className="btn edit-btn"
          disabled={this.state.submitting}
          onClick={() => this.setState({editing: true})}
          type="button"
        >
          Edit
        </button>
      )
    );
    return (
      <ModalForm ref={this._modal} title="Observation">
        <div className="observation-modal">
          <Loading loading={!this.state.observation.id}>
            <div className="button-section">
              <div className="left-button-section">{leftButtonSection}</div>
              <div className="right-button-section">{rightButtonSection}</div>
            </div>
            <div className="model-evaluation-section">
              <ModelEvaluationComponent
                alertBroker={this.services.alertBroker}
                editing={this.state.editing}
                experiment={this.props.experiment}
                observation={
                  this.state.editing
                    ? this.getObservationInput()
                    : this.state.observation
                }
                onAssignmentsChange={(assignments) =>
                  this.setState({assignmentsInput: assignments})
                }
                onMetricsChange={(values, failed) =>
                  this.setState({
                    valuesInput: values,
                    failureInput: failed,
                  })
                }
                submitting={this.state.submitting}
                suggestion={this.state.suggestion}
              />
            </div>
          </Loading>
          {this.props.children}
        </div>
      </ModalForm>
    );
  }
}

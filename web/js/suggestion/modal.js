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
import ui from "../experiment/ui";
import {ModelEvaluationComponent} from "../experiment/model_evaluation";
import {promiseFinally} from "../utils";

export default class SuggestionModal extends Component {
  static propTypes = {
    canEdit: PropTypes.bool.isRequired,
    experiment: schemas.Experiment.isRequired,
    onObservationCreated: PropTypes.func,
    onSuggestionDeleted: PropTypes.func,
  };

  static defaultProps = {
    onObservationCreated: _.noop,
    onSuggestionDeleted: _.noop,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      observation: null,
      reporting: false,
      submitting: false,
      suggestion: null,
    };
    this._modal = React.createRef();
  }

  extractStateFromSuggestion = (suggestion) => ({
    failureInput: false,
    observation: null,
    reporting: false,
    submitting: false,
    suggestion,
    valuesInput: ui.getInitialValues(this.props.experiment),
  });

  extractStateFromObservation = (observation) => ({
    observation,
    reporting: false,
    submitting: false,
  });

  getObservationInput() {
    return {
      assignments: this.state.suggestion && this.state.suggestion.assignments,
      failed: this.state.failureInput,
      suggestion: this.state.suggestion && this.state.suggestion.id,
      values: this.state.valuesInput,
    };
  }

  reportObservation = () => {
    const sanitizedObservation = ui.sanitizeObservation(
      this.props.experiment,
      _.omit(this.getObservationInput(), ["assignments"]),
    );
    if (
      ui.validateObservationInput(
        this.props.experiment,
        sanitizedObservation,
        (msg) => this.services.alertBroker.show(msg),
      )
    ) {
      this.setState({submitting: true});
      const revertSubmitting = () => this.setState({submitting: false});
      promiseFinally(
        this.services.promiseApiClient
          .experiments(this.props.experiment.id)
          .observations()
          .create(sanitizedObservation)
          .then((newObservation) => {
            this.setState(this.extractStateFromObservation(newObservation));
            this.services.alertBroker.info(
              <span>
                Observation reported. You can view all obervations on the{" "}
                <a href={`/experiment/${this.props.experiment.id}/history`}>
                  history page
                </a>
                {""}.
              </span>,
            );
            this.props.onObservationCreated(newObservation);
          }, this.services.alertBroker.errorHandlerThatExpectsStatus(400, 403, 404)),
        revertSubmitting,
      );
    }
  };

  deleteSuggestion = () => {
    this.setState({submitting: true});
    return this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .suggestions(this.state.suggestion.id)
      .delete()
      .then(
        () => {
          this.services.alertBroker.info("Suggestion deleted");
          setTimeout(() => this._modal.current.hide(), 2000);
          this.props.onSuggestionDeleted(this.state.suggestion);
        },
        (err) => {
          this.setState({submitting: false});
          return this.services.alertBroker.errorHandlerThatExpectsStatus(
            400,
            403,
            404,
          )(err);
        },
      );
  };

  show(suggestion) {
    this.setState(this.extractStateFromSuggestion(suggestion), () =>
      this._modal.current.show(this.services.alertBroker.clearAlerts),
    );
  }

  render() {
    const leftButtonSection = !this.state.observation && this.props.canEdit && (
      <button
        className="btn delete-btn"
        disabled={this.state.submitting}
        onClick={this.deleteSuggestion}
        type="button"
      >
        Delete
      </button>
    );
    const rightButtonSection = this.state.reporting ? (
      <>
        <button
          className="btn cancel-btn"
          disabled={this.state.submitting}
          onClick={() =>
            this.setState((prevState) =>
              this.extractStateFromSuggestion(prevState.suggestion),
            )
          }
          type="button"
        >
          Cancel
        </button>
        <button
          className="btn finish-btn"
          disabled={this.state.submitting}
          onClick={this.reportObservation}
          type="button"
        >
          Report
        </button>
      </>
    ) : (
      !this.state.observation &&
      this.props.canEdit && (
        <button
          className="btn edit-btn"
          disabled={this.state.submitting}
          onClick={() => this.setState({reporting: true})}
          type="button"
        >
          Report Observation
        </button>
      )
    );
    return (
      <ModalForm
        ref={this._modal}
        title={this.state.observation ? "Observation" : "Suggestion"}
      >
        <div className="observation-modal">
          <Loading loading={!this.state.suggestion}>
            <div className="button-section">
              <div className="left-button-section">{leftButtonSection}</div>
              <div className="right-button-section">{rightButtonSection}</div>
            </div>
            <div className="model-evaluation-section">
              <ModelEvaluationComponent
                alertBroker={this.services.alertBroker}
                editing={this.state.reporting}
                experiment={this.props.experiment}
                observation={
                  this.state.reporting
                    ? this.getObservationInput()
                    : this.state.observation
                }
                onMetricsChange={(values, failed) =>
                  this.setState({
                    failureInput: failed,
                    valuesInput: values,
                  })
                }
                submitting={this.state.submitting}
                suggestion={this.state.suggestion}
              />
            </div>
          </Loading>
        </div>
      </ModalForm>
    );
  }
}

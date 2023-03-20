/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Component from "../react/component";
import Loading from "../component/loading";
import ModalForm from "../component/modal/form";
import schemas from "../react/schemas";
import {ModelEvaluationComponent} from "./model_evaluation";

export default class BestAssignmentModal extends Component {
  static propTypes = {
    children: PropTypes.node,
    experiment: schemas.Experiment.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      bestAssignment: null,
      observation: null,
      suggestion: null,
    };
    this._modal = React.createRef();
  }

  fetchSuggestion(suggestionId) {
    if (suggestionId) {
      this.services.promiseApiClient
        .experiments(this.props.experiment.id)
        .suggestions(suggestionId)
        .fetch()
        .then(
          (suggestion) => this.setState({suggestion}),
          this.services.alertBroker.errorHandlerThatExpectsStatus(403, 404),
        );
    }
  }

  fetchObservation(observationId) {
    if (observationId) {
      this.services.promiseApiClient
        .experiments(this.props.experiment.id)
        .observations(observationId)
        .fetch()
        .then((observation) => {
          this.setState({observation});
          this.fetchSuggestion(observation.suggestion);
        }, this.services.alertBroker.errorHandlerThatExpectsStatus(403, 404));
    }
  }

  show(bestAssignment, next) {
    this.fetchObservation(bestAssignment.id);
    this.setState({bestAssignment}, () => this._modal.current.show(next));
  }

  render() {
    const bestAssignment = this.state.bestAssignment;
    const loadingObservation =
      bestAssignment && bestAssignment.id && !this.state.observation;
    const loadingBestAssignment = !bestAssignment;
    const loading = loadingObservation || loadingBestAssignment;

    return (
      <ModalForm ref={this._modal} title="Best Observation">
        <div className="observation-modal">
          <Loading loading={loading}>
            {!loading && (
              <div className="model-evaluation-section">
                <ModelEvaluationComponent
                  experiment={this.props.experiment}
                  bestAssignment={this.state.bestAssignment}
                  observation={this.state.observation}
                  suggestion={this.state.suggestion}
                />
              </div>
            )}
          </Loading>
          {this.props.children}
        </div>
      </ModalForm>
    );
  }
}

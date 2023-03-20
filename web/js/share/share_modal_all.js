/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Modal from "../component/modal/base";
import Spinner from "../component/spinner";
import makeSubmittableComponent from "../component/make-submittable";
import schemas from "../react/schemas";
import {isUndefinedOrNull} from "../utils";

const getInitialExperiment = (props) => {
  const initialExperiment = _.first(props.experiments)
    ? _.first(props.experiments).id
    : "";
  return {
    error: null,
    selectedExperiment: initialExperiment,
  };
};

export default makeSubmittableComponent(
  class ShareExperimentListModal extends React.Component {
    static propTypes = {
      alertBroker: schemas.AlertBroker.isRequired,
      experiments: PropTypes.arrayOf(schemas.Experiment),
      onSubmitSuccess: PropTypes.func,
      promiseApiClient: schemas.PromiseApiClient.isRequired,
      submit: PropTypes.func.isRequired,
      submitting: PropTypes.bool.isRequired,
    };

    constructor(...args) {
      super(...args);
      this.state = getInitialExperiment(this.props);
      this._shareModal = React.createRef();
    }

    static getDerivedStateFromProps(props) {
      return getInitialExperiment(props);
    }

    show = () => {
      this._shareModal.current.show();
    };

    hide = () => {
      this._shareModal.current.hide();
    };

    handleExperimentChange = (e) => {
      this.setState({
        selectedExperiment: e.target.value,
      });
    };

    selector = () => {
      if (this.state.error) {
        // NOTE: The error message is shown by the alert broker,
        // so we don't have anything to do here
        return <p>This experiment could not be shared.</p>;
      }

      if (isUndefinedOrNull(this.props.experiments)) {
        return <Spinner />;
      }

      if (_.isEmpty(this.props.experiments)) {
        return (
          <div>
            You haven&rsquo;t created any <a href="/experiments">Experiments</a>{" "}
            yet.
          </div>
        );
      }

      const generateLinkButton = (
        <button
          className="btn btn-primary generate-link-btn"
          onClick={_.bind(this.generateToken, this)}
          type="button"
        >
          Generate Link
        </button>
      );
      return (
        <div>
          <label className="form-group" htmlFor="experimentSelect">
            Experiment:{" "}
          </label>
          <select
            className="form-control experiment-select"
            name="experimentSelect"
            onChange={_.bind(this.handleExperimentChange, this)}
            value={this.state.selectedExperiment}
          >
            {_.map(this.props.experiments, (experiment) => (
              <option key={experiment.id} value={experiment.id}>
                {experiment.name}
              </option>
            ))}
          </select>
          <div className="centered-button-holder">
            {this.props.submitting ? (
              <Spinner position="absolute" />
            ) : (
              generateLinkButton
            )}
          </div>
        </div>
      );
    };

    shareModalBody = () => (
      <div className="row share-experiment-row">
        <h4>Generate a link to share read-only access to your experiment:</h4>
        {this.selector()}
      </div>
    );

    generateToken = () => {
      this.props.submit(
        (s, e) =>
          this.props.promiseApiClient
            .experiments(this.state.selectedExperiment)
            .tokens()
            .create()
            .then(s, e),
        (token) => {
          this.hide();
          if (this.props.onSubmitSuccess) {
            this.props.onSubmitSuccess(token);
          }
        },
        (err) => {
          this.props.alertBroker.errorHandlerThatExpectsStatus(403, 404)(err);
          this.setState({error: err});
        },
      );
    };

    render() {
      return (
        <Modal
          alertBroker={this.props.alertBroker}
          ref={this._shareModal}
          className="share-modal"
          title="Share Experiment"
        >
          {this.shareModalBody()}
        </Modal>
      );
    }
  },
);

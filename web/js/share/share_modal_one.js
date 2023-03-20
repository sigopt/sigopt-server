/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Component from "../react/component";
import Modal from "../component/modal/base";
import ReadOnlyInput from "../component/readonly";
import Spinner from "../component/spinner";
import schemas from "../react/schemas";

class ShareExperimentModal extends Component {
  static propTypes = {
    alertBroker: PropTypes.object.isRequired,
    experiment: schemas.Experiment,
    token: PropTypes.string,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      token: null,
      error: null,
    };
    this._shareModal = React.createRef();
  }

  fetchToken = () => {
    this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .tokens()
      .create()
      .then(
        (result) => this.setState({token: result.token}),
        (err) => {
          this.services.alertBroker.errorHandlerThatExpectsStatus(
            403,
            404,
          )(err);
          this.setState({error: err});
        },
      );
  };

  get token() {
    return this.props.token || this.state.token;
  }

  show = () => {
    if (!this.token) {
      this.fetchToken();
    }
    this._shareModal.current.show();
  };

  hide = () => {
    this._shareModal.current.hide();
  };

  tokenDashboardLink = () => {
    if (!this.token) {
      return (
        <p>
          You can manage your tokens <a href="/tokens/manage">here.</a>
        </p>
      );
    }
    return null;
  };

  shareModalBody = () => {
    if (this.state.error) {
      // NOTE: The error message is shown by the alert broker,
      // so we don't have anything to do here
      return <p>This experiment could not be shared.</p>;
    }

    if (!this.token) {
      return <Spinner position="absolute" />;
    }

    // TODO(SN-1184): Is this the right host to use? If the user is behind a proxy
    // this will not be the host they see
    const host = this.services.clientsideConfigBroker.get("address.app_url");

    return (
      <div className="row share-experiment-row">
        <h4>
          Share a read-only version of your experiment with the following link:
        </h4>
        <div className="control-content">
          <ReadOnlyInput
            id="share-experiment-url-input"
            value={`${host}/guest?guest_token=${this.token}`}
          />
        </div>
        {this.tokenDashboardLink()}
      </div>
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
}

export default ShareExperimentModal;

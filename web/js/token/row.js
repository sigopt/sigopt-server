/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import DeleteTokenModal from "./delete_token_modal";
import ReadOnlyInput from "../component/readonly";
import RotateTokenModal from "./rotate_token_modal";
import ShareExperimentModal from "../share/share_modal_one";
import TriggerModalButton from "../component/modal/button";
import {DeleteButton, RotateButton, ShareButton} from "../component/buttons";
import {TokenTypes, getType} from "./types";

class TokenRow extends React.Component {
  state = {token: this.props.token};

  rotateTokenSuccess = (token) => {
    this.props.alertBroker.show("Token successfully rotated.", "info");
    this.setState({token: token});
  };

  render() {
    const experiment = this.props.experiment;
    const token = this.state.token;
    const tokenType = getType(token);

    const experimentLink = token.all_experiments ? (
      "ALL"
    ) : (
      <a href={`/experiment/${token.experiment}`}>
        {experiment ? experiment.name : token.experiment}
      </a>
    );

    return (
      <tr>
        <td className="title">{tokenType} Token</td>
        <td>
          <ReadOnlyInput value={token.token || ""} />
        </td>
        <td>{token.user}</td>
        <td>
          <code>{token.permissions}</code>
        </td>
        <td>{experimentLink}</td>
        <td className="actions">
          <span>
            <TriggerModalButton button={<RotateButton title="Rotate Token" />}>
              <RotateTokenModal
                {...this.props}
                token={token}
                success={this.rotateTokenSuccess}
              >
                <p>
                  Are you sure you want to rotate this token? This will
                  permanently invalidate the existing token, and replace it with
                  a new one.
                </p>
              </RotateTokenModal>
            </TriggerModalButton>
            {tokenType === TokenTypes.GUEST && (
              <>
                <TriggerModalButton
                  button={<ShareButton title="Share Experiment" />}
                >
                  <ShareExperimentModal
                    alertBroker={this.props.alertBroker}
                    host={this.props.host}
                    token={token.token}
                  />
                </TriggerModalButton>
                <TriggerModalButton
                  button={<DeleteButton title="Delete Guest Token" />}
                >
                  <DeleteTokenModal
                    {...this.props}
                    token={token}
                    experiment={experiment}
                    success={this.props.deleteTokenSuccess}
                  />
                </TriggerModalButton>
              </>
            )}
          </span>
        </td>
      </tr>
    );
  }
}

export default TokenRow;

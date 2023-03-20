/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import classNames from "classnames";

import Component from "../../../../react/component";
import LinkGlyph from "../../../../component/glyph/link";
import ShareExperimentModal from "../../../../share/share_modal_one";
import TriggerModalButton from "../../../../component/modal/button";

class ShareButton extends Component {
  render() {
    return (
      <TriggerModalButton
        className={classNames(
          "glyph-label share-experiment-btn",
          this.props.className,
        )}
        label={
          <>
            <LinkGlyph />
            <span className="link-label">{this.props.name}</span>
          </>
        }
      >
        <ShareExperimentModal
          alertBroker={this.services.alertBroker}
          experiment={this.props.experiment}
        />
      </TriggerModalButton>
    );
  }
}

export default ShareButton;

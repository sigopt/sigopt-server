/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/create.less";

/* eslint-disable react/jsx-no-bind */
import React from "react";

import ExperimentEditor from "../../../../experiment/editor";
import Page from "../../../../component/page";
import ui from "../../../../experiment/ui";

export default function (props) {
  return (
    <Page
      loggedIn={true}
      className="experiment-create"
      title="Create Experiment"
    >
      <div className="experiment-create-body">
        <div className="experiment-creator">
          <ExperimentEditor
            {...props}
            canEdit={true}
            create={true}
            experiment={null}
            loginState={props.loginState}
            onSuccess={(experiment) => {
              window.location.href = ui.getExperimentUrl(experiment);
            }}
            promiseApiClient={props.promiseApiClient}
            renderAlerts={true}
          />
        </div>
      </div>
    </Page>
  );
}

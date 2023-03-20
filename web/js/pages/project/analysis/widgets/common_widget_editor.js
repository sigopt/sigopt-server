/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../component/tooltip.less";

import _ from "underscore";
import React from "react";

import {unsafeSeralizationChecker} from "../lib/errors";

const ErrorList = ({errors}) => (
  <div className="flex-column full-width error-list">
    {_.map(errors, (error, i) => (
      <div className="error-list-item danger-bg mpm-border" key={i.toString()}>
        {" "}
        {error}{" "}
      </div>
    ))}
  </div>
);

export class CommonWidgetEditor extends React.Component {
  constructor(props) {
    super(props);
    const initialWidgetData = JSON.parse(
      JSON.stringify(
        this.props.editorState.widgetData,
        unsafeSeralizationChecker,
      ),
    );

    this.state = {
      valid: true,
      initialWidgetData,
      widgetData: null,
      errors: [],
    };
  }

  setWidgetData = (widgetData) => this.setState({widgetData});

  setValid = (valid, errors) => this.setState({valid, errors});

  onSumbit = () => {
    this.props.upsertWidget(this.state.widgetData);
  };

  render() {
    const {editorState} = this.props;
    const editing = Boolean(editorState.widgetId);
    const buttonText = editing ? "Save Changes" : "Create";

    return (
      <>
        <editorState.widgetDefinition.editor
          initialWidgetData={this.state.initialWidgetData}
          setValid={this.setValid}
          editing={editing}
          setWidgetData={this.setWidgetData}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 10,
          }}
        >
          <button
            onClick={this.props.cancelEditing}
            type="button"
            className="btn danger-bg mpm-border"
          >
            Cancel
          </button>

          <div style={{display: "inline-block"}} className="tooltip-trigger">
            <button
              disabled={!this.state.valid}
              onClick={this.onSumbit}
              type="button"
              className="btn basic-button-white mpm-border"
            >
              {buttonText}
            </button>
          </div>
        </div>
        <ErrorList errors={this.state.errors} />
      </>
    );
  }
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import createReactClass from "create-react-class";

import CheckGlyph from "./glyph/check";
import EditableMixin from "../mixins/editable";
import Form from "./form";
import PencilGlyph from "./glyph/pencil";
import SubmittableMixin from "../mixins/submittable";
import XmarkGlyph from "./glyph/xmark";
import schemas from "../react/schemas";

const FieldEditor = createReactClass({
  displayName: "FieldEditor",

  propTypes: {
    alertBroker: schemas.AlertBroker.isRequired,
    buttonClassOverride: PropTypes.string,
    fieldName: PropTypes.string.isRequired,
    loginState: schemas.LoginState.isRequired,
    object: PropTypes.object.isRequired,
    updateFunction: PropTypes.func.isRequired,
  },

  mixins: [SubmittableMixin, EditableMixin],

  getInitialState: function () {
    return {
      fieldText: this.props.object[this.props.fieldName],
    };
  },

  fieldChange: function (e) {
    this.setState({fieldText: e.target.value});
  },

  render: function () {
    if (this.state.editing) {
      const formSubmit = () =>
        this.stopEditingAndSubmit(
          _.partial(this.props.updateFunction, this.props.object.id, {
            [this.props.fieldName]: this.state.fieldText,
          }),
          null,
          this.props.alertBroker.errorHandlerThatExpectsStatus(400),
        );

      return (
        <div className="field-editor">
          <Form
            className="edit-form form-inline"
            onSubmit={formSubmit}
            csrfToken={this.props.loginState.csrfToken}
          >
            <input
              type="text"
              className="form-control name-input"
              value={this.state.fieldText || ""}
              onChange={this.fieldChange}
            />
            <button
              type="submit"
              className={
                this.props.buttonClassOverride
                  ? this.props.buttonClassOverride
                  : "btn btn-sm btn-primary"
              }
            >
              <CheckGlyph />
            </button>
            <a
              className={
                this.props.buttonClassOverride
                  ? this.props.buttonClassOverride
                  : "btn btn-sm btn-warning"
              }
              onClick={() => this.cancelEditing()}
            >
              <XmarkGlyph />
            </a>
          </Form>
        </div>
      );
    } else {
      return (
        <div className="field-static">
          <span>{this.state.fieldText}</span>
          <a onClick={() => this.startEditing()} className="edit-button">
            <PencilGlyph />
          </a>
        </div>
      );
    }
  },
});

export default FieldEditor;

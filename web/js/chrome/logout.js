/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Form from "../component/form";

export class LogoutForm extends React.Component {
  constructor(...args) {
    super(...args);
    this._ref = React.createRef();
  }

  submit = () => {
    this._ref.current.submit();
  };

  onSubmit = () => {
    (this.props.beforeSubmit
      ? this.props.beforeSubmit()
      : Promise.resolve()
    ).then(() => this.submit());
  };

  render() {
    return (
      <Form
        action="/logout"
        csrfToken={this.props.csrfToken}
        method="post"
        onSubmit={this.onSubmit}
        ref={this._ref}
      >
        {this.props.continue ? (
          <input type="hidden" name="continue" value={this.props.continue} />
        ) : null}
        {this.props.children}
      </Form>
    );
  }
}

export class LogoutLink extends React.Component {
  constructor(...args) {
    super(...args);
    this._ref = React.createRef();
  }

  onClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    this._ref.current.submit();
  };

  render() {
    return (
      <span>
        <span style={{display: "none"}}>
          <LogoutForm
            continue={this.props.continue}
            csrfToken={this.props.csrfToken}
            ref={this._ref}
          />
        </span>
        <a className={this.props.className} onClick={this.onClick}>
          {this.props.children}
        </a>
      </span>
    );
  }
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/login.less";

import React from "react";

import Alert from "../../../alert/alert";
import Form from "../../../component/form";
import ModalInterior from "../../../component/modal/interior";
import Page from "../../../component/page";
import {FooterTypes} from "../../../component/modal/constant";
import {SignUpLoginTitle} from "../components/login_signup";

export default class LoginPage extends React.Component {
  constructor(...args) {
    super(...args);
    this.state = {
      continueHref: this.props.continueHref,
      email: this.props.email,
      error: this.props.error && new Alert(this.props.error),
    };
  }

  componentDidMount() {
    this.props.alertBroker.registerHandler(this.alertHandler);
  }

  componentWillUnmount() {
    this.props.alertBroker.releaseHandler(this.alertHandler);
  }

  alertHandler = (error) => {
    this.setState({error: error});
  };

  render() {
    return (
      <Page loggedIn={false} className="login-page">
        <Form
          action="/login"
          className="login-form"
          csrfToken={this.props.loginState.csrfToken}
        >
          <ModalInterior
            error={this.state.error}
            footer={FooterTypes.Submit}
            showClose={false}
            title={<SignUpLoginTitle currentPage="Log In" />}
          >
            <div className="modal-form">
              <p className="modal-description">
                {this.props.showNeedsLogin
                  ? "You need to log in to see this page."
                  : "Welcome back!"}
              </p>
              <div className="form-inputs">
                <div className="form-group">
                  <label className="control-label">Email</label>
                  <input
                    className="form-control"
                    name="email"
                    type="email"
                    value={this.state.email || ""}
                    onChange={(e) =>
                      this.setState({email: e.currentTarget.value})
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="control-label">Password</label>
                  <input
                    className="form-control"
                    name="password"
                    type="password"
                    defaultValue={this.props.password}
                  />
                </div>
                {this.state.continueHref ? (
                  <input
                    type="hidden"
                    name="continue"
                    value={this.state.continueHref}
                  />
                ) : null}
              </div>
              <div className="modal-description-footer">
                <a
                  tabIndex="-1"
                  className="login-alternative"
                  href="/forgot_password"
                >
                  I forgot my password
                </a>
              </div>
            </div>
          </ModalInterior>
        </Form>
      </Page>
    );
  }
}

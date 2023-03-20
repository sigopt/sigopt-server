/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./setup.less";

import React from "react";

import Component from "../../react/component";
import Form from "../../component/form";
import Page from "../../component/page";
import Spinner from "../../component/spinner";
import {PRODUCT_NAME} from "../../brand/constant";

export default class extends Component {
  static displayName = "SetupPage";

  state = {
    submitting: false,
  };

  handleChange = (event) => {
    const name = event.target.name;
    this.setState({[name]: event.target.checked});
  };

  onSubmit = (event) => {
    event.preventDefault();
    this.setState(
      {
        submitting: true,
      },
      () =>
        this.props.promiseApiClient
          .users(this.props.loginState.userId)
          .update({
            planned_usage: {
              track: this.state.track,
              optimize: this.state.optimize,
            },
          })
          .then(() => this.props.navigator.navigateTo("/home")),
    );
  };

  onSkip = () => {
    this.props.navigator.navigateTo("/home");
  };

  render() {
    return (
      <Page title="New Account">
        <Form className="setup-form" onSubmit={this.onSubmit}>
          <h2>While we&apos;re setting up your {PRODUCT_NAME} account...</h2>
          <fieldset disabled={this.state.submitting}>
            <label className="description">
              What would you like to do with {PRODUCT_NAME}?
            </label>
            <div className="checkbox">
              <label htmlFor="optimize">
                <input
                  type="checkbox"
                  id="optimize"
                  name="optimize"
                  onChange={this.handleChange}
                  value={false}
                />{" "}
                Optimize my models
              </label>
            </div>
            <div className="checkbox">
              <label htmlFor="track">
                <input
                  type="checkbox"
                  id="track"
                  name="track"
                  onChange={this.handleChange}
                  value={false}
                />{" "}
                Track my models and collaborate with my team
              </label>
            </div>
            {this.state.submitting ? (
              <Spinner />
            ) : (
              <>
                <input
                  type="submit"
                  value="Done"
                  className="btn btn-secondary"
                />
                <a onClick={this.onSkip}>Skip</a>
              </>
            )}
          </fieldset>
        </Form>
      </Page>
    );
  }
}

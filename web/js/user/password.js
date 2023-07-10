/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../component/tooltip.less";

import _ from "underscore";
import React from "react";
import classNames from "classnames";

import CheckGlyph from "../component/glyph/check";
import EyeGlyph from "../component/glyph/eye";
import EyeSlashGlyph from "../component/glyph/eye-slash";
import XmarkGlyph from "../component/glyph/xmark";

const PASSWORD_MIN_LENGTH_CHARACTERS = 8;
const longEnough = (str) => str.length >= PASSWORD_MIN_LENGTH_CHARACTERS;
const hasLowercase = (str) => /[a-z]/u.test(str);
const hasUppercase = (str) => /[A-Z]/u.test(str);
const hasDigit = (str) => /[0-9]/u.test(str);
const hasSpecial = (str) => /[^A-Za-z0-9]/u.test(str);

const MobileFriendlyTooltip = (props) => (
  <div
    className={classNames("status-container", props.shouldShow && "active")}
    style={{zIndex: 1000 - props.priority}}
  >
    <div className="status-container-content">{props.children}</div>
  </div>
);

class StatusChecks extends React.Component {
  state = {shouldShow: false};

  componentDidMount() {
    this.componentDidUpdate({}, {});
  }

  componentDidUpdate(prevProps) {
    const checkUpdateKeys = [
      "children",
      "setPasswordValidity",
      "shouldShow",
      "validPassword",
    ];
    if (
      !_.isEqual(
        _.pick(this.props, checkUpdateKeys),
        _.pick(prevProps, checkUpdateKeys),
      )
    ) {
      const allChecksValid = _.all(
        React.Children.map(this.props.children, (c) => c.props.success),
      );
      if (this.props.validPassword !== allChecksValid) {
        this.props.setPasswordValidity(allChecksValid);
      }
      this.updateShouldShow(!allChecksValid && this.props.shouldShow);
    }
  }

  updateShouldShow(shouldShow) {
    this.setState({shouldShow});
  }

  render() {
    return (
      <MobileFriendlyTooltip
        shouldShow={this.state.shouldShow}
        priority={this.props.priority}
      >
        <ul className="status-checks">{this.props.children}</ul>
      </MobileFriendlyTooltip>
    );
  }
}

const Check = (props) => (
  <li>
    {props.success ? <CheckGlyph /> : <XmarkGlyph />}
    <span className="description">{props.children}</span>
  </li>
);

export default class NewPasswordInput extends React.Component {
  state = {
    passwordFocus: false,
    passwordVerifyFocus: false,
    validatePassword: false,
    validateVerifyPassword: false,
    validPassword: false,
    passwordVisibility: false,
  };

  onPasswordFocus = () => this.setState({passwordFocus: true});
  onPasswordVerifyFocus = () => this.setState({passwordVerifyFocus: true});
  onPasswordBlur = () =>
    this.setState({validatePassword: true, passwordFocus: false});
  onVerifyPasswordBlur = () =>
    this.setState({validateVerifyPassword: true, passwordVerifyFocus: false});

  onPasswordUpdate = (e) => this.props.onPasswordUpdate(e.target.value);
  onVerifyPasswordUpdate = (e) =>
    this.props.onVerifyPasswordUpdate(e.target.value);

  setPasswordValidity = (validPassword) => this.setState({validPassword});

  togglePasswordVisibility = () => {
    this.setState((prevState) => ({
      passwordVisibility: !prevState.passwordVisibility,
    }));
  };

  render() {
    const showInvalidPasswordWarning =
      this.state.validatePassword && !this.state.validPassword;

    return (
      <>
        <div className="form-group password-input">
          <div>
            <div className="password-title">
              <label className="control-label" htmlFor="new-password-input">
                {`${this.props.change ? "New Password" : "Password"}${
                  this.props.required ? "*" : ""
                }`}
              </label>
              <div
                onClick={this.togglePasswordVisibility}
                className="show-pw-btn"
                type="button"
              >
                {this.state.passwordVisibility ? "Hide" : "Show"}{" "}
                {this.state.passwordVisibility ? (
                  <EyeSlashGlyph />
                ) : (
                  <EyeGlyph />
                )}
              </div>
            </div>

            <div>
              <input
                className={classNames({
                  "form-control": true,
                  "outline-red": showInvalidPasswordWarning,
                })}
                id="new-password-input"
                name="new-password"
                onBlur={this.onPasswordBlur}
                onFocus={this.onPasswordFocus}
                onChange={this.onPasswordUpdate}
                type={this.state.passwordVisibility ? "text" : "password"}
                value={this.props.password}
              />
              {showInvalidPasswordWarning ? (
                <div className="password-warning-message">
                  Password does not meet requirements.
                </div>
              ) : null}
              <StatusChecks
                setPasswordValidity={this.setPasswordValidity}
                validPassword={this.state.validPassword}
                priority={1}
                shouldShow={this.state.passwordFocus}
                shouldValidate={this.state.validatePassword}
              >
                <Check success={longEnough(this.props.password)}>
                  At least {PASSWORD_MIN_LENGTH_CHARACTERS} characters
                </Check>
                <Check success={hasLowercase(this.props.password)}>
                  At least one lowercase character
                </Check>
                <Check success={hasUppercase(this.props.password)}>
                  At least one uppercase character
                </Check>
                <Check success={hasDigit(this.props.password)}>
                  At least one digit
                </Check>
                <Check success={hasSpecial(this.props.password)}>
                  At least one special character
                </Check>
              </StatusChecks>
            </div>
          </div>
        </div>
        {this.props.verify ? (
          <div className="form-group password-input verify">
            <label htmlFor="verify-password-input" className="control-label">
              Confirm Password
            </label>
            <div>
              <input
                id="verify-password-input"
                className="form-control"
                name="verify-password"
                onBlur={this.onVerifyPasswordBlur}
                onFocus={this.onPasswordVerifyFocus}
                onChange={this.onVerifyPasswordUpdate}
                type="password"
                value={this.props.verifyPassword}
              />
              <StatusChecks
                setPasswordValidity={_.noop}
                priority={2}
                shouldShow={this.state.passwordVerifyFocus}
                shouldValidate={
                  !this.state.passwordFocus && this.state.validateVerifyPassword
                }
              >
                <Check
                  success={this.props.password === this.props.verifyPassword}
                >
                  Passwords must match
                </Check>
              </StatusChecks>
            </div>
          </div>
        ) : null}
      </>
    );
  }
}

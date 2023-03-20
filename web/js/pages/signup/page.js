/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/signup.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import React from "react";

import Component from "../../react/component";
import Form from "../../component/form";
import HeroPng from "../home/components/project_analysis.png";
import ModalInterior from "../../component/modal/interior";
import NetError from "../../alert/error";
import NewPasswordInput from "../../user/password";
import Page from "../../component/page";
import ResendVerificationEmailButton from "../../user/resend";
import {PRODUCT_NAME} from "../../brand/constant";
import {SignUpLoginTitle} from "../landing/components/login_signup";
import {
  concatenateLocalPartAndDomain,
  extractDomainFromEmail,
  extractLocalPartFromEmail,
  validateEmail,
} from "../../net/email";

const maxFieldLength = "100";

const UserErrorFormatter = (err) => {
  if (
    err.message &&
    err.message.startsWith('Missing required json key "password"')
  ) {
    err.message = "Password is required.";
  }
  return err;
};

export default class extends Component {
  constructor(...args) {
    super(...args);
    this.state = {
      email: this.props.email || "",
      submitting: false,
    };
    // Note: When a token is in the URL, it is a client token
    // for an organization's signup link. In the rest of the cases,
    // there is no user yet so there is no token, so we use the
    // promiseApiClient with the token set to 'null'.
    this.promiseApiClient = this.props.hasTokenInUrl
      ? this.props.promiseApiClient
      : this.props.promiseApiClient.withApiToken(null);
  }

  singleEmailDomain = () => {
    if (
      this.props.organization &&
      this.props.organization.email_domains &&
      _.size(this.props.organization.email_domains) === 1
    ) {
      return this.props.organization.email_domains[0];
    } else {
      return null;
    }
  };

  emailInput = () => {
    const emailDomain = this.singleEmailDomain();
    // NOTE: This is props.email and not state.email because we only want to
    // freeze the field if the email was specified initially
    if (this.props.email && this.props.code) {
      return (
        <div>
          <p className="form-control-static">{this.state.email}</p>
          <input
            type="hidden"
            name="email"
            defaultValue={this.state.email}
            maxLength={maxFieldLength}
          />
        </div>
      );
    } else if (emailDomain) {
      const emailWithDomain =
        this.state.email || concatenateLocalPartAndDomain("", emailDomain);
      return (
        <div className="input-group">
          <input
            className="form-control email-local-part"
            name="email"
            value={extractLocalPartFromEmail(emailWithDomain)}
            maxLength={maxFieldLength}
            onChange={(e) =>
              this.setState({
                email: concatenateLocalPartAndDomain(
                  e.currentTarget.value,
                  emailDomain,
                ),
              })
            }
          />
          <div className="input-group-addon">@{emailDomain}</div>
        </div>
      );
    } else {
      return (
        <input
          className="form-control"
          name="email"
          type="email"
          value={this.state.email || ""}
          onChange={(e) => this.setState({email: e.currentTarget.value})}
          maxLength={maxFieldLength}
        />
      );
    }
  };

  _sanitizeEmail = (email) => {
    // Help users who double-enter their domain
    const emailDomain = this.singleEmailDomain();
    if (
      this.singleEmailDomain() &&
      extractDomainFromEmail(email) === this.singleEmailDomain() &&
      extractDomainFromEmail(extractDomainFromEmail(email)) ===
        this.singleEmailDomain()
    ) {
      return `${extractLocalPartFromEmail(email)}@${emailDomain}`;
    } else {
      return email;
    }
  };

  submitOrgSignup = (email, name, password) => {
    return this.services.promiseApiClient
      .users()
      .create({
        client_name: this.props.code ? null : email,
        client: this.props.client && this.props.client.id,
        email: email,
        invite_code: this.props.code,
        name: name,
        password: password,
      })
      .then((user) => {
        return this.services.promiseApiClient
          .sessions()
          .create({email: user.email, password: password})
          .then((session) => this.props.sessionUpdater.setSession(session))
          .then(() => this.props.navigator.navigateTo(`/setup`))
          .catch((err) => {
            if (err.status === 403) {
              err.handle();
              this.setState({verificationEmail: user.email});
              return Promise.resolve(null);
            } else {
              return Promise.reject(err);
            }
          });
      })
      .catch((err) => this.props.alertBroker.handle(UserErrorFormatter(err)))
      .then(() => this.setState({submitting: false}));
  };

  handleSubmitResponse = (email) =>
    this.setState({
      submitting: false,
      verificationEmail: email,
    });

  handleSubmitError = (email, err) => {
    if (err.status === 400 && err.message.includes("verify email")) {
      this.setState({
        submitting: false,
        verificationEmail: email,
      });
    } else {
      this.props.alertBroker.handle(UserErrorFormatter(err));
      this.setState({
        submitting: false,
      });
    }
  };

  submitSelfSignup = (email, name, password, promiseApiClient) => {
    return promiseApiClient
      .users()
      .create({
        client_name: email,
        email: email,
        password: password,
        name: name,
      })
      .then(
        () => this.handleSubmitResponse(email),
        (err) => this.handleSubmitError(email, err),
      );
  };

  clientSideValidation = () => {
    this.props.alertBroker.clearAlerts();
    const email = this._sanitizeEmail(this.state.email);

    // The input field, with type 'email' also adds
    // some small level of validation.
    if (!validateEmail(email)) {
      return this.props.alertBroker.handle(
        new NetError({
          message: "Please enter a valid email address.",
          status: 400,
        }),
      );
    }

    if (
      this.props.verifyPassword &&
      this.state.verifyPassword !== this.state.password
    ) {
      return this.props.alertBroker.handle(
        new NetError({
          message: "Please check that your passwords match.",
          status: 400,
        }),
      );
    }

    if (!this._nameInput.value) {
      return this.props.alertBroker.handle(
        new NetError({
          message: "Please enter your name.",
          status: 400,
        }),
      );
    }

    const domains =
      (this.props.organization && this.props.organization.email_domains) || [];
    if (
      !_.isEmpty(domains) &&
      !_.any(domains, (domain) => email.endsWith(`@${domain}`))
    ) {
      return this.props.alertBroker.handle(
        new NetError({
          message: `Your email must belong to one of the following domains: ${domains.join(
            ",",
          )}`,
          status: 400,
        }),
      );
    }
    return true;
  };

  onSubmit = () => {
    if (this.clientSideValidation()) {
      const name = this._nameInput && this._nameInput.value;
      const password = this.state.password;
      const email = this._sanitizeEmail(this.state.email);
      const promiseApiClient = this.props.hasTokenInUrl
        ? this.props.promiseApiClient
        : this.props.promiseApiClient.withApiToken(null);

      this.setState({submitting: true});
      const toReturn = this.props.isOrgSignup
        ? this.submitOrgSignup(email, name, password, promiseApiClient)
        : this.submitSelfSignup(email, name, password, promiseApiClient);

      return toReturn.finally(() => this.setState({submitting: false}));
    }
    return Promise.resolve(null);
  };

  render() {
    if (this.props.unclaimableInvite) {
      return (
        <Page title="Invalid invite">
          <p className="signup-description invalid-invite">
            Sorry, but it looks like this invite has expired, or is not for you.
            You may need to log out to claim this invite.
          </p>
        </Page>
      );
    } else if (this.props.isOrgSignup || this.props.allowSelfSignup) {
      return (
        <Page id="signup-page">
          <ModalInterior
            showClose={false}
            title={
              this.state.verificationEmail ? (
                "Complete Signup"
              ) : (
                <SignUpLoginTitle currentPage="Sign Up" />
              )
            }
          >
            {this.state.verificationEmail ? (
              <div className="signup-description thanks-message">
                <p style={{margin: "0 0 20px 0"}}>
                  Thanks for signing up! You must verify your email address (
                  {this.state.verificationEmail}) before using your account.
                  Check your email for further instructions.
                </p>
                <ResendVerificationEmailButton
                  email={this.state.email}
                  promiseApiClient={this.props.promiseApiClient}
                />
              </div>
            ) : (
              <div className="col-layout">
                <div className="col-1 product-info">
                  <p>Sign up to:</p>
                  <ul>
                    <li>Manage model and hyperparameter optimization</li>
                    <li>
                      Track model artifacts and collaborate with your team
                    </li>
                    <li>Visualize training and metric comparisons</li>
                    <li>Schedule your training jobs</li>
                  </ul>
                  <img
                    className="hero-img"
                    src={HeroPng}
                    alt="The SigOpt web application provides visualizations of your data."
                    style={{maxWidth: "600px"}}
                  />
                </div>
                <div className="col-1">
                  {this.props.organization ? (
                    <p className="signup-description">
                      Sign up to join {this.props.organization.name} on{" "}
                      {PRODUCT_NAME}.
                    </p>
                  ) : (
                    <p className="signup-description free-signup-description">
                      Get started with a free account, today.
                    </p>
                  )}
                  <Form
                    clientSideValidation={this.clientSideValidation}
                    {...this.props}
                    buttonText="Sign Up"
                    onSubmit={this.onSubmit}
                    className="signup-form"
                    csrfToken={this.context.loginState.csrfToken}
                    submitting={this.state.submitting}
                  >
                    <fieldset disabled={this.state.submitting}>
                      <div className="form-inputs">
                        <div className="form-group">
                          <label className="control-label">Name</label>
                          <input
                            className="form-control"
                            defaultValue={this.props.name}
                            name="name"
                            autoComplete="name"
                            maxLength={maxFieldLength}
                            ref={(c) => {
                              this._nameInput = c;
                            }}
                          />
                        </div>
                        <div className="form-group">
                          <label className="control-label">Email</label>
                          {this.emailInput()}
                        </div>
                        <NewPasswordInput
                          onPasswordUpdate={(password) =>
                            this.setState({password})
                          }
                          onVerifyPasswordUpdate={(verifyPassword) =>
                            this.setState({verifyPassword})
                          }
                          password={this.state.password || ""}
                          verifyPassword={this.state.verifyPassword || ""}
                          change={false}
                          verify={false}
                        />
                        <div>
                          <div>
                            <input
                              type="submit"
                              value="Sign Up"
                              className="btn btn-primary"
                            />
                          </div>
                        </div>
                      </div>
                    </fieldset>
                  </Form>
                </div>
              </div>
            )}
          </ModalInterior>
        </Page>
      );
    } else if (this.props.requireInvite) {
      return (
        <Page title="Sign Up Disabled">
          <p className="signup-description">
            Signup has been disabled by your administrator. Contact them to have
            an account created for you. Or, visit the{" "}
            <a href="/login">login page</a> to sign up with an existing account.
          </p>
        </Page>
      );
    } else {
      return (
        // NOTE: This shouldn't ever happen, but this is a reasonable fallback
        <Page title="Sign Up Invalid">
          <p className="signup-description">This sign up link is invalid.</p>
        </Page>
      );
    }
  }
}

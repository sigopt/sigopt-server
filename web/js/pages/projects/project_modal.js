/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../../react/component";
import ModalForm from "../../component/modal/form";
import makeEditableComponent from "../../component/make-editable";
import schemas from "../../react/schemas";
import {DOCS_URL} from "../../net/constant";
import {FooterTypes} from "../../component/modal/constant";

const ProjectModal = makeEditableComponent(
  () => ({editing: true}),
  class ProjectModal extends Component {
    static propTypes = {
      alertBroker: schemas.AlertBroker.isRequired,
      clientId: PropTypes.string,
      editing: PropTypes.bool,
      loginState: schemas.LoginState.isRequired,
      promiseApiClient: schemas.PromiseApiClient.isRequired,
      stopEditingAndSubmit: PropTypes.func.isRequired,
    };

    constructor(...args) {
      super(...args);
      this.state = {};
      this._projectModal = React.createRef();
    }

    show = () => {
      this.setState({
        idInput: "",
        nameInput: "",
        idChangedByUser: false,
      });
      if (this._projectModal.current) {
        this._projectModal.current.show();
      }
    };

    filterStringForId = (str) => {
      const lowerWithoutSpaces = str.toLowerCase().replace(/ /gu, "-");
      return (lowerWithoutSpaces.match(/[a-z0-9\-_.]/gu) || []).join("");
    };

    debounceIdUniquenessCheck = _.debounce(() => {
      const showExistingProjectAlert = () =>
        this.props.alertBroker.show(
          "A project with this id already exists. Please choose a unique ID.",
          "danger",
        );
      this.services.promiseApiClient
        .clients(this.props.loginState.clientId)
        .projects(this.state.idInput)
        .fetch()
        .then(showExistingProjectAlert, (err) => {
          if (err && err.status && _.contains([403, 404], err.status)) {
            err.handle();
            if (err.status === 403) {
              showExistingProjectAlert();
            } else if (err.status === 404) {
              this.props.alertBroker.clearAlerts();
            }
            return Promise.resolve();
          }
          return Promise.reject(err);
        });
    }, 300);

    setId = (newId) => {
      this.setState({idInput: newId}, () => {
        this.props.alertBroker.clearAlerts();
        this.debounceIdUniquenessCheck();
      });
    };

    handleIdInputChange = (e) => {
      this.setId(this.filterStringForId(e.target.value));
      this.setState({
        idChangedByUser: true,
      });
    };

    handleNameInputChange = (e) => {
      e.persist();
      this.setState({nameInput: e.target.value}, () => {
        if (!this.state.idChangedByUser) {
          this.setId(this.filterStringForId(this.state.nameInput));
        }
      });
    };

    createProject = (success, error) => {
      if (this.props.editing) {
        this.props.stopEditingAndSubmit(
          (s, e) =>
            this.props.promiseApiClient
              .clients(this.props.loginState.clientId)
              .projects()
              .create({name: this.state.nameInput, id: this.state.idInput})
              .then((p) => s(p.id), e),
          success,
          error,
        );
      }
    };

    afterCreateProject = () =>
      this.services.navigator.navigateTo(
        `/client/${this.props.loginState.clientId}/project/${this.state.idInput}`,
      );

    apiError = (error) => {
      if (
        error.status === 400 ||
        error.status === 403 ||
        error.status === 409
      ) {
        if (error.message.indexOf("Missing required json key") > -1) {
          error.message = "Please fill in all required values.";
        }
        this.props.alertBroker.handle(error);
      }
    };

    render() {
      return (
        <ModalForm
          closeDelay={0}
          error={this.apiError}
          footer={FooterTypes.SubmitAndCancel}
          onSubmit={this.createProject}
          ref={this._projectModal}
          success={this.afterCreateProject}
          title="Create Project"
        >
          <p>
            A project is a way to group related experiments for easier viewing
            and organization. <br />
            {""}
            You can set the <code>project</code> field when creating an
            experiment via the API.{" "}
            <a
              href={`${DOCS_URL}/ai-module-api-references/tutorial/project-tutorial`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn more.
            </a>
          </p>
          <div className="project-modal">
            <label htmlFor="project-name-input">Project Name:</label>
            <input
              id="project-name-input"
              onChange={this.handleNameInputChange}
              value={this.state.nameInput || ""}
            />
            <div className="project-id-label">
              <label htmlFor="project-id-input">Project ID:</label>
              <p>
                This ID is used in experiment creation code to assign an
                experiment to a project.
              </p>
              <p className="input-tip">
                ID must be lowercase, without spaces. Only <code>a-z</code>
                {", "}
                <code>0-9</code>
                {", "}
                <code>.</code>
                {", "}
                <code>_</code>
                {", "}
                <code>-</code>
              </p>
            </div>
            <input
              id="project-id-input"
              onChange={this.handleIdInputChange}
              value={this.state.idInput || ""}
            />
          </div>
        </ModalForm>
      );
    }
  },
);

export default ProjectModal;

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Component from "../react/component";
import PencilGlyph from "./glyph/pencil";
import TextEditor from "./text_editor";
import makeEditable from "./make-editable";
import schemas from "../react/schemas";
import {DeleteButton, TextButton} from "./buttons";
import {RelativeTime} from "../render/format_times";
import {
  isDefinedAndNotNull,
  withPreventDefaultAndStopPropagation,
} from "../utils";

export class EditInfo extends React.Component {
  static propTypes = {
    lastEditedBy: PropTypes.string,
    lastUpdated: PropTypes.number,
  };

  // NOTE: Makes it so that last updated time doesn't get rerendered
  // with every little state change from the parent `NotesEditor`
  shouldComponentUpdate(nextProps) {
    const initialUpdate = !this.props.lastUpdated && nextProps.lastUpdated;
    const updatedAgain =
      this.props.lastUpdated &&
      nextProps.lastUpdated &&
      this.props.lastUpdated !== nextProps.lastUpdated;

    return Boolean(initialUpdate || updatedAgain);
  }

  render() {
    const {lastEditedBy, lastUpdated} = this.props;

    return (
      <div className="edit-info">
        <div className="title">Last Updated</div>
        {isDefinedAndNotNull(lastEditedBy) &&
        isDefinedAndNotNull(lastUpdated) ? (
          <>
            <RelativeTime time={lastUpdated} />
            {` by ${lastEditedBy}`}
          </>
        ) : (
          "--"
        )}
      </div>
    );
  }
}

export class NotesEditor extends Component {
  static propTypes = {
    cancelEditing: PropTypes.func.isRequired,
    currentUser: schemas.User.isRequired,
    editing: PropTypes.bool.isRequired,
    note: schemas.Note,
    onSubmit: PropTypes.func.isRequired,
    startEditing: PropTypes.func.isRequired,
    stopEditingAndSubmit: PropTypes.func.isRequired,
  };

  state = {
    contents: "",
    lastEditedBy: null,
    lastUpdated: null,
  };

  componentDidMount() {
    const {note} = this.props;
    if (isDefinedAndNotNull(note)) {
      this.getUserName(note.user).then((userName) => {
        this.setState({
          contents: note.contents,
          lastEditedBy: userName,
          lastUpdated: note.created,
        });
      });
    }
  }

  getUserName = (userId) => {
    if (userId === this.props.currentUser.id) {
      return Promise.resolve(this.props.currentUser.name);
    }

    return this.services.promiseApiClient
      .users(userId)
      .fetch()
      .then((user) => user.name);
  };

  handleChange = (contents) => {
    this.setState({contents});
  };

  handleSuccess = (note) => {
    this.getUserName(note.user).then((userName) => {
      this.setState({
        lastEditedBy: userName,
        lastUpdated: note.created,
      });
    });
  };

  handleSubmit = (success, error) => {
    this.props.onSubmit({contents: this.state.contents}).then(success, error);
  };

  handleFailure = (err) => {
    throw err;
  };

  startEditing = withPreventDefaultAndStopPropagation(() => {
    this.props.startEditing(this.state);
  });

  cancelEditing = withPreventDefaultAndStopPropagation(() => {
    this.props.cancelEditing((recoveryState) => {
      this.setState(recoveryState);
    });
  });

  stopEditingAndSubmit = withPreventDefaultAndStopPropagation(() => {
    this.props.stopEditingAndSubmit(
      this.handleSubmit,
      this.handleSuccess,
      this.handleFailure,
    );
  });

  render() {
    return (
      <div className="notes-editor">
        <div className="top-bar">
          <EditInfo
            lastEditedBy={this.state.lastEditedBy}
            lastUpdated={this.state.lastUpdated}
          />
          <div className="action-buttons">
            {this.props.editing ? (
              <>
                <DeleteButton onClick={this.cancelEditing} />
                <TextButton
                  onClick={this.stopEditingAndSubmit}
                  text="Save Changes"
                />
              </>
            ) : (
              <TextButton
                onClick={this.startEditing}
                text={
                  <>
                    <PencilGlyph className="btn-glyph" />
                    Edit Note
                  </>
                }
              />
            )}
          </div>
        </div>
        <TextEditor
          editing={this.props.editing}
          onChange={this.handleChange}
          value={this.state.contents}
        />
      </div>
    );
  }
}

export default makeEditable(NotesEditor);

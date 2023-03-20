/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import makeSubmittableComponent from "./make-submittable";
import {deepCopyJson} from "../utils";

/**
 * A Higher-Order component that grants a component the ability to edit content, and
 * either submit those edits, or cancel and restore the original state.
 *
 * The most common usage will look like
 *
 * const Editor = makeEditableComponent(class extends React.Component {
 *   render() {
 *     return [
 *       {this.props.editing ? <input placeholder="Name"/> : <label>Your name</label>},
 *       {this.props.submitting && <Spinner/>},
 *       <button label="Edit" onClick={this.props.startEditing(this.state)}/>,
 *       <button label="Cancel" onClick={this.props.cancelEditing((recoveryState) => this.setState(recoveryState))}/>,
 *       <button label="Submit" onClick={this.props.stopEditingAndSubmit(submitter, success, error)}/>,
 *     ]
 *   }
 * }
 *
 * The HOC provides the following props to the WrappedComponent:
 *   cancelEditing: A function the WrappedComponent can call to stop editing. The function will be provided
 *     the recovery state that was provided to startEditing. This can be used to restore the initial state
 *   editing: True if the component is being edited. False otherwise
 *   editingRecoveryState: The state that will be recovered if editing is cancelled
 *   startEditing: A function the WrappedComponent can call to start editing. It accepts a recovery state
 *     as the argument, which can be restored upon cancellation.
 *   stopEditingAndSubmit: A function the WrappedComponent can call to stop editing and submit.
 *     Accepts `submitter`, `success`, and `error` args as in the submittable HOC.
 *
 * The HOC also provides all the props from `makeSubmittableComponent`. See make-submittable.js for those docs.
 * In particular, the `submitting` props may be convenient for showing a loading state.
 * You typically will not need to call the `submit` function directly, since the editable HOC will handle that
 * for you.
 */
export default function makeEditableComponent(...editableArgs) {
  const getInitialState =
    editableArgs.length > 1 ? editableArgs[0] : () => ({});
  const WrappedComponent = editableArgs[1] || editableArgs[0];
  const EditableComponent = class extends React.Component {
    static displayName = `Editable(${WrappedComponent.displayName})`;

    static propTypes = {
      editing: PropTypes.bool,
      fref: PropTypes.func,
      resetSubmissionState: PropTypes.func.isRequired,
      submit: PropTypes.func.isRequired,
    };

    static defaultProps = _.extend({
      editing: false,
    });

    state = _.extend(
      {
        editing: this.props.editing,
        editingRecoveryState: null,
      },
      getInitialState(this.props),
    );

    cancelEditing = (callback) => {
      let recoveryState = {};
      if (this.state.editing) {
        recoveryState = this.state.editingRecoveryState;
        this.setState({
          editing: false,
          editingRecoveryState: null,
        });
      }
      this.props.resetSubmissionState();
      if (callback) {
        callback(recoveryState);
        return;
      }
    };

    startEditing = (recoveryState) => {
      if (!this.state.editing) {
        this.setState((prevState) => {
          const newState = {editing: true};
          if (!prevState.editing && !prevState.editingRecoveryState) {
            newState.editingRecoveryState = deepCopyJson(recoveryState);
          }
          return newState;
        });
      }
    };

    stopEditingAndSubmit = (submitter, success, error) => {
      if (this.state.editing) {
        this.props.submit(
          submitter,
          (...args) => {
            this.setState({
              editing: false,
              editingRecoveryState: null,
            });
            return success && success(...args);
          },
          error,
        );
      }
    };

    render() {
      const {fref} = this.props;
      return (
        <WrappedComponent
          {..._.omit(this.props, ["fref"])}
          {...this.state}
          ref={fref}
          cancelEditing={this.cancelEditing}
          startEditing={this.startEditing}
          stopEditingAndSubmit={this.stopEditingAndSubmit}
        />
      );
    }
  };
  const forwarded = React.forwardRef((props, ref) => (
    <EditableComponent {...props} fref={ref} />
  ));
  return makeSubmittableComponent(forwarded);
}

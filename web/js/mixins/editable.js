/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {deepCopyJson} from "../utils";

// A utility mixin for forms that become editable prior to submission.
// NOTE: Requires Submittable to also be mixed in
// NOTE: Requires state to be serializeable as JSON
const EditableMixin = {
  getInitialState: function () {
    return {
      editing: false,
      editingRecoveryState: null,
    };
  },

  toggleEditingAndSubmit: function (submitter, success, error) {
    if (this.state.editing) {
      this.stopEditingAndSubmit(submitter, success, error);
    } else {
      this.startEditing();
    }
  },

  stopEditingAndSubmit: function (submitter, success, error) {
    if (this.state.editing) {
      const ourSuccess = (...args) => {
        this.setState({
          editing: false,
          editingRecoveryState: null,
        });
        if (success) {
          success(...args);
          return;
        }
      };
      this.submit(submitter, ourSuccess, error);
    }
  },

  cancelEditing: function () {
    if (this.state.editing) {
      const newState = this.state.editingRecoveryState || {};
      newState.editing = false;
      newState.editingRecoveryState = null;
      this.setState(newState);
    }
  },

  startEditing: function () {
    if (!this.state.editing) {
      this.setState((prevState) => ({
        editing: true,
        editingRecoveryState: deepCopyJson(prevState),
      }));
    }
  },
};
export default EditableMixin;

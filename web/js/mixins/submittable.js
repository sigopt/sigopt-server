/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

const SubmittableMixin = {
  getInitialState: function () {
    return {
      submitting: false,
      submitted: false,
    };
  },

  submit: function (submitter, success, error) {
    if (!this.state.submitting) {
      const onSuccess = (...args) => {
        this.setState({
          submitting: false,
          submitted: true,
        });
        if (success) {
          success(...args);
          return;
        }
      };

      const onError = (...args) => {
        this.setState({submitting: false});
        if (error) {
          error(...args);
          return;
        }
      };

      this.setState({submitting: true});
      submitter(onSuccess, onError);
    }
  },
};
export default SubmittableMixin;

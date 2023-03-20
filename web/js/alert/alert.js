/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

class Alert {
  constructor(options) {
    this.options = options;
    this.type = this.options.type;
    this.__htmlMessage = this.options["__htmlMessage"];
    this.message = this.options.message || this.__htmlMessage;
    this._handled = false;
    this._status = options.status;
    this.onDismiss = options.onDismiss;
  }

  toJson() {
    return this.options;
  }

  dangerousHtml() {
    return (
      this.__htmlMessage && {
        __html: this.__htmlMessage,
      }
    );
  }

  handle() {
    this._handled = true;
  }

  get hasBeenHandled() {
    return this._handled;
  }
}

export default Alert;

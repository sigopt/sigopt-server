/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

class ReadOnlyInput extends React.Component {
  highlightText = (e) => {
    e.target.select();
  };

  render() {
    return (
      <input
        className={this.props.className || "form-control"}
        id={this.props.id}
        onClick={this.highlightText}
        readOnly={true}
        name={this.props.name}
        value={this.props.value}
      />
    );
  }
}

export default ReadOnlyInput;

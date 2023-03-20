/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

export default class TextEditor extends React.Component {
  static propTypes = {
    editing: PropTypes.bool,
    onChange: PropTypes.func.isRequired,
    value: PropTypes.string.isRequired,
  };

  static defaultProps = {
    editing: true,
  };

  componentDidUpdate(prevProps) {
    if (!prevProps.editing && this.props.editing) {
      this.ref.current.focus();
    }
  }

  ref = React.createRef();

  render() {
    const {editing, onChange, value} = this.props;

    return (
      <textarea
        className="text-editor"
        disabled={!editing}
        onChange={(event) => onChange(event.currentTarget.value)}
        ref={this.ref}
        value={value}
      />
    );
  }
}

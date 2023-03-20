/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

/**
 * Updates a component so that all rerenders will manifest as an
 * unmount followed by a mount.
 * This is useful when your componentDidMount and componentWillUnmount
 * have critical logic that must remain consistent between updates.
 *
 * This is implemented by creating a `key` property which is updated
 * on every render.
 *
 * This does incur a performance penalty, so should not be used on
 * components that will be rendered many times.
 */
const forceRemountOnUpdate = (Component) =>
  class ForcedRemountComponent extends React.Component {
    constructor(...args) {
      super(...args);
      this.state = {key: 0};
    }

    static getDerivedStateFromProps(props, state) {
      return {key: state.key + 1};
    }

    render() {
      return <Component key={this.state.key.toString()} {...this.props} />;
    }
  };

export default forceRemountOnUpdate;

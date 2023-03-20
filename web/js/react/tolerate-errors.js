/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

/**
 * Renders the provided empty state (by default, nothing) if an error occurs in the component.
 * The error is propogated by React and will be caught and logged as normal.
 *
 * Sample usage:
 *
 * <Page>
 *   // ...
 *   <TolerateErrors errorState="Something went wrong!">
 *     <SomeSketchyComponent/>
 *   </TolerateErrors>
 *   // ...
 * </Page>
 *
 * Implementation is based on getDerivedStateFromError and componentDidCatch
 * from the React lifecycle.
 * https://reactjs.org/docs/react-component.html
 */
export default class TolerateErrors extends React.Component {
  static getDerivedStateFromError() {
    return {error: true};
  }

  state = {error: false};

  render() {
    if (this.state.error) {
      return this.props.errorState || null;
    }
    return this.props.children;
  }
}

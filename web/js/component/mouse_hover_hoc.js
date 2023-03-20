/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

export default function makeMouseHover(WrappedComponent) {
  return class MouseHoverWrapper extends React.Component {
    state = {mouseHovered: false};

    setHovered = () => this.setState({mouseHovered: true});
    setUnhovered = () => this.setState({mouseHovered: false});

    mouseEventHandlers = {
      onMouseEnter: this.setHovered,
      onMouseMove: this.setHovered,
      onMouseLeave: this.setUnhovered,
    };

    render() {
      return (
        <WrappedComponent
          mouseHovered={this.state.mouseHovered}
          mouseEventHandlers={this.mouseEventHandlers}
          {...this.props}
        />
      );
    }
  };
}

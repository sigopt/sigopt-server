/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

class Chiclets extends React.Component {
  render() {
    return (
      <div className="chiclets">
        {_.map(this.props.chiclets, ([info, subtitle]) => (
          <div className="chiclet" key={subtitle}>
            <div className="data">{info}</div>
            <div className="source">{subtitle}</div>
          </div>
        ))}
      </div>
    );
  }
}

export default Chiclets;

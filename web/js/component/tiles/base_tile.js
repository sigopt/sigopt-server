/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import MaybeLink from "../link";
import Spinner from "../spinner";
import Tooltip from "../tooltip";
import TriangleExclamationGlyph from "../glyph/triangle-exclamation";

class BaseTile extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    error: PropTypes.bool,
    header: PropTypes.node,
    href: PropTypes.string,
    loading: PropTypes.bool,
    tileClass: PropTypes.string,
    tooltip: PropTypes.string,
  };

  render() {
    return (
      <MaybeLink href={this.props.href}>
        <div className={classNames("info-tile", this.props.tileClass)}>
          <div className="info-tile-content">
            <div className="header">
              <Spinner size={6} loading={this.props.loading} />
              {this.props.error && (
                <TriangleExclamationGlyph className="alert-glyph" />
              )}
              {this.props.tooltip ? (
                <Tooltip tooltip={this.props.tooltip}>
                  {this.props.header}
                </Tooltip>
              ) : (
                this.props.header
              )}
            </div>
            {this.props.children}
          </div>
        </div>
      </MaybeLink>
    );
  }
}

export default BaseTile;

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../render/bootstrap";

/* eslint-disable react/jsx-no-bind */
import React from "react";
import classNames from "classnames";
import {UID as Uid} from "react-uid";

import AngleDownGlyph from "./glyph/angle-down";

export default class Section extends React.Component {
  // This section class collapses into 2 columns when the screen size is sufficiently large.
  // The fullWidth prop forces the section to always take up the full width of the page.
  // NOTE: the parent component must have display: flex

  onClickToggle = () => {
    if (this.props.setCollapsed) {
      this.props.setCollapsed(!this.props.collapsed);
    }
  };

  render() {
    const {children, className, collapsable, collapsed, fullWidth, title} =
      this.props;
    return (
      <Uid>
        {(uid) => (
          <div
            className={classNames("section", className, {
              collapsed,
              "full-width": fullWidth,
            })}
          >
            <div className="section-title">
              {collapsable && (
                <button
                  className="toggler"
                  type="button"
                  data-toggle="collapse"
                  data-target={`#section-${uid}`}
                  aria-controls={`section-${uid}`}
                  aria-expanded="false"
                  aria-label="Toggle navigation"
                  onClick={this.onClickToggle}
                >
                  <AngleDownGlyph className={classNames({collapsed})} />
                </button>
              )}
              <h2 className="text">{title}</h2>
              <div className="hline" />
            </div>
            <div
              className={classNames("section-content", {collapse: collapsable})}
              id={`section-${uid}`}
            >
              {children}
            </div>
          </div>
        )}
      </Uid>
    );
  }
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./tabs.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

export class Tab extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    label: PropTypes.string.isRequired,
  };

  render() {
    return (
      <div name={this.props.label} className="tab">
        {this.props.children}
      </div>
    );
  }
}

export class Tabs extends React.Component {
  static propTypes = {
    active: PropTypes.string,
    // TODO: Validate that all children are Tabs
    children: PropTypes.node,
    className: PropTypes.string,
    onTabClick: PropTypes.func,
  };

  render() {
    const children = React.Children.toArray(this.props.children);
    const content = _.find(
      children,
      (tab) => tab.props.label === this.props.active,
    );
    return (
      <div className={this.props.className}>
        <ul className="tablist" role="tablist">
          {_.map(_.compact(children), (tab) => (
            <li
              className={tab.props.label === this.props.active ? "active" : ""}
              key={tab.props.label}
              role="presentation"
            >
              <a
                className="clickable-tab"
                href={tab.props.href}
                onClick={() =>
                  this.props.onTabClick &&
                  this.props.onTabClick(tab.props.label)
                }
              >
                {tab.props.header || tab.props.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="tab-content active">{content}</div>
      </div>
    );
  }
}

export class ClickableTabs extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    className: PropTypes.string,
  };

  constructor(props) {
    super(props);
    const active = React.Children.toArray(props.children)[0];

    this.state = {
      active: active && active.props.label,
    };
  }

  setTab = (tab) => {
    this.setState({active: tab});
  };

  render() {
    return (
      <Tabs
        active={this.state.active}
        className={this.props.className}
        onTabClick={this.setTab}
      >
        {this.props.children}
      </Tabs>
    );
  }
}

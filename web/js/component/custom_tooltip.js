/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../render/bootstrap";
import "./tooltip.less";

import $ from "jquery";
import PropTypes from "prop-types";
import React from "react";

import {coalesce} from "../utils";

// Fixes popovers so they don't hide when you hover over their content
// http://jsfiddle.net/WojtekKruszewski/Zf3m7/22/
const overrideLeaveMethod = function ($node) {
  const originalLeave = $node.popover.Constructor.prototype.leave;
  $node.popover.Constructor.prototype.leave = function (obj) {
    const self =
      obj instanceof this.constructor
        ? obj
        : $(obj.currentTarget)
            [this.type](this.getDelegateOptions())
            .data(`bs.${this.type}`);

    originalLeave.call(this, obj);
    if (obj.currentTarget) {
      // TODO(SN-1155): This should be scoped to the node, right now it affects all the popovers
      // on the page.
      const popover = $(".popover");
      const timeout = self.timeout;
      popover.one("mouseenter", function () {
        clearTimeout(timeout);
        popover.one("mouseleave", function () {
          $node.popover.Constructor.prototype.leave.call(self, self);
        });
      });
    }
  };
};

class CustomTooltip extends React.Component {
  static propTypes = {
    allowHoverOnPopover: PropTypes.bool,
    children: PropTypes.node.isRequired,
    container: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]),
    hideDelay: PropTypes.number,
    html: PropTypes.bool,
    placement: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
    showDelay: PropTypes.number,
    tooltip: PropTypes.node.isRequired,
    trigger: PropTypes.string,
  };

  static defaultProps = {
    allowHoverOnPopover: true,
    container: "body",
    hideDelay: 200,
    showDelay: 0,
  };

  constructor(...args) {
    super(...args);
    this._node = React.createRef();
  }

  componentDidMount() {
    this.initializePopovers();
  }

  dynamicPopoverDirection = (context, source) => {
    const offset = $(source).offset();
    const topOfWindow = offset.top - $(window).scrollTop();
    const bottomOfWindow = $(window).height() - topOfWindow;
    const leftOfWindow = offset.left - $(window).scrollLeft();
    const rightOfWindow = $(window).width() - leftOfWindow;

    if (rightOfWindow > 250) {
      return "right";
    }

    if (bottomOfWindow > 200) {
      return "bottom";
    }

    return "auto right";
  };

  initializePopovers = () => {
    const $thisNode = $(this._node.current);
    const $contentHolder = $thisNode.find(".popover-content-holder");
    const $tooltip = $thisNode.find(".tooltip-trigger");
    const content = this.props.html
      ? $contentHolder.html()
      : $contentHolder.text();
    if (this.props.allowHoverOnPopover) {
      overrideLeaveMethod($thisNode);
    }
    $tooltip.popover({
      container: this.props.container,
      content: content,
      delay: {show: this.props.showDelay, hide: this.props.hideDelay},
      html: coalesce(this.props.html, false),
      placement: this.props.placement || this.dynamicPopoverDirection,
      trigger: this.props.trigger || "hover focus",
    });
  };

  render() {
    return (
      <span ref={this._node}>
        <span className="popover-holder">{this.props.children}</span>
        <span style={{display: "none"}} className="popover-content-holder">
          {this.props.tooltip}
        </span>
      </span>
    );
  }
}

export default CustomTooltip;

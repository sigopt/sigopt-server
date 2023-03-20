/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import date from "date-and-time";
import englishLocale from "date-and-time/locale/en";
import pluralize from "pluralize";

import Component from "../react/component";
import {fromNow, lookPretty} from "./nice-times";

date.locale(englishLocale);

const formatTime = function (text, now, renderer) {
  // NOTE: Include raw unix time, useful for debugging
  const seconds = parseInt(text, 10);
  const title = date.format(new Date(seconds * 1000), "MMM D YYYY, H:mm:ss");
  return (
    <span title={title}>
      {seconds ? renderer(seconds, now || new Date().getTime() / 1000) : ""}
    </span>
  );
};

export class RelativeTime extends Component {
  render() {
    return formatTime(this.props.time, this.context.pageRenderTime, fromNow);
  }
}

export const Duration = ({endTime, startTime}) => {
  const diffTime = endTime - startTime;
  const days = Math.floor(diffTime / 86400);
  const daysString = `${pluralize("day", days, true)}, `;
  return (
    <span
      title={`${days > 0 ? daysString : ""}${date.format(
        new Date(diffTime * 1000),
        "HH:mm:ss",
        true,
      )}`}
    >
      {lookPretty(diffTime)}
    </span>
  );
};

export class AbsoluteTime extends Component {
  defaultRenderer = (s) =>
    date.format(new Date(s * 1000), "MMM D YYYY, h:mm A");
  render() {
    return formatTime(
      this.props.time,
      this.context.pageRenderTime,
      this.props.renderer || this.defaultRenderer,
    );
  }
}

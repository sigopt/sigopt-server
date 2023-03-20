/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import formatDistance from "date-fns/distance_in_words_strict";

import {isDefinedAndNotNull} from "../utils";

export const lookPretty = function (seconds) {
  if (seconds < 0) {
    return null;
  }
  if (seconds < 1) {
    return "less than one second";
  }
  const now = Date.now();
  return formatDistance(new Date(now), new Date(now - seconds * 1000), {
    includeSeconds: true,
  });
};

export const fromNow = function (seconds, now) {
  // allow for setting now manually for testing
  if (Math.abs(now - seconds) < 1) {
    if (now < seconds) {
      return "in less than one second";
    } else {
      return "less than one second ago";
    }
  }
  const previous = new Date(seconds * 1000);
  const current = new Date(isDefinedAndNotNull(now) ? now * 1000 : null);
  return formatDistance(current, previous, {
    addSuffix: true,
    includeSeconds: true,
  });
};

export const compactDuration = (duration) => {
  // Formats durations comma separated keeping only the 2 most significant parts, ex.
  // 1d, 0h
  // 3d, 32m
  // 10m, 12s
  // 3s
  let seconds = Math.floor(duration);
  let minutes = Math.floor(seconds / 60);
  seconds %= 60;
  let hours = Math.floor(minutes / 60);
  minutes %= 60;
  const days = Math.floor(hours / 24);
  hours %= 24;
  const durationParts = [
    [days, "d"],
    [hours, "h"],
    [minutes, "m"],
    [seconds, "s"],
  ];
  let firstNonZeroDurationIndex = _.findIndex(durationParts, ([v]) => v > 0);
  if (firstNonZeroDurationIndex < 0) {
    firstNonZeroDurationIndex = _.size(durationParts) - 1;
  }
  const renderParts = durationParts.slice(
    firstNonZeroDurationIndex,
    firstNonZeroDurationIndex + 2,
  );
  return _.map(renderParts, (part) => part.join("")).join(", ");
};

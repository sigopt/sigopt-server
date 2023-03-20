/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import dateFormat from "date-fns/format";

import Chart from "./chart";

export default class UsageChart extends Chart {
  getChartArgs(history) {
    const type_of_usage = this.args.is_runs ? "Runs" : "Experiments";

    const xLabel = (h) => dateFormat(new Date(h.start * 1000), "MM/DD/YYYY");
    const DATE_FORMAT = "MMM";
    const x = _.map(history, xLabel);
    const y = _.map(history, (h) => h.count);
    const text = _.map(history, (h) => {
      const startDateString = dateFormat(new Date(h.start * 1000), DATE_FORMAT);
      const endDateString = dateFormat(new Date(h.end * 1000), DATE_FORMAT);
      return `${
        h.count
      } ${type_of_usage.toLocaleLowerCase()} from ${startDateString} to ${endDateString}`;
    });

    const data = [
      {
        x: x,
        y: y,
        text: text,
        type: "bar",
        hoverinfo: "text",
      },
    ];

    return {
      data: data,
      layout: {
        xaxis: {
          title: "Month",
        },
        yaxis: {
          title: `# of ${type_of_usage}`,
        },
        height: 400,
      },
    };
  }
}

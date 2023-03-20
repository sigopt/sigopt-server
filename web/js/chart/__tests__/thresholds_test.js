/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {AxisTypes} from "../constants";
import {updateLayoutForThresholds} from "../thresholds";

describe("updateLayoutForThresholds", () => {
  it("does nothing for experiments without thresholds", () => {
    const experiment = {
      metrics: [
        {name: "m1", objective: "maximize"},
        {name: "m2", objective: "maximize"},
      ],
    };
    const observations = [];
    const layout = {};
    updateLayoutForThresholds(
      experiment,
      observations,
      {
        xAxis: {key: "m1", type: AxisTypes.OPTIMIZED_METRIC},
        yAxis: {key: "m2", type: AxisTypes.OPTIMIZED_METRIC},
      },
      layout,
    );
    expect(layout).toEqual({shapes: []});
  });

  it("does nothing for non-metric axes", () => {
    const experiment = {
      metrics: [
        {name: "m1", objective: "maximize", threshold: 0},
        {name: "m2", objective: "maximize", threshold: 0},
      ],
      parameters: [{name: "p1"}, {name: "p2"}],
    };
    const observations = [];
    const layout = {};
    updateLayoutForThresholds(
      experiment,
      observations,
      {
        xAxis: {key: "p1", type: AxisTypes.PARAMETER},
        yAxis: {key: "p2", type: AxisTypes.PARAMETER},
      },
      layout,
    );
    expect(layout).toEqual({shapes: []});
  });

  it("works with experiments with 1 threshold", () => {
    const threshold = 0;
    const experiment = {
      metrics: [
        {name: "m1", objective: "maximize"},
        {name: "m2", objective: "maximize", threshold},
      ],
    };
    const observations = [];
    const layout = {};
    updateLayoutForThresholds(
      experiment,
      observations,
      {
        xAxis: {key: "m1", type: AxisTypes.OPTIMIZED_METRIC},
        yAxis: {key: "m2", type: AxisTypes.OPTIMIZED_METRIC},
      },
      layout,
    );

    expect(layout.shapes).toHaveLength(2);

    const lineShape = layout.shapes[0];
    expect(lineShape.xref).toEqual("paper");
    expect(lineShape.x0).toEqual(0);
    expect(lineShape.x1).toEqual(1);
    expect(lineShape.yref).toEqual("y");
    expect(lineShape.y0).toEqual(threshold);
    expect(lineShape.y1).toEqual(threshold);

    const boxShape = layout.shapes[1];
    expect(boxShape.xref).toEqual("paper");
    expect(boxShape.x0).toEqual(0);
    expect(boxShape.x1).toEqual(1);
    expect(boxShape.yref).toEqual("y");
    expect(boxShape.y0).toEqual(threshold);
    expect(boxShape.y1).toBeLessThan(threshold);

    expect(layout.xaxis).toBe(undefined);
    expect(layout.yaxis.autorange).toBe(false);
    expect(layout.yaxis.range[0]).toBeLessThan(threshold);
    expect(layout.yaxis.range[1]).toBeGreaterThan(threshold);
  });

  it("works with experiments that have 2 thresholds", () => {
    const m1Threshold = -1.23;
    const m2Threshold = 1.23;
    const experiment = {
      metrics: [
        {name: "m1", objective: "maximize", threshold: m1Threshold},
        {name: "m2", objective: "maximize", threshold: m2Threshold},
      ],
    };
    const observations = [];
    const layout = {};
    updateLayoutForThresholds(
      experiment,
      observations,
      {
        xAxis: {key: "m1", type: AxisTypes.OPTIMIZED_METRIC},
        yAxis: {key: "m2", type: AxisTypes.OPTIMIZED_METRIC},
      },
      layout,
    );

    expect(layout.shapes).toHaveLength(5);

    const xLineShape = layout.shapes[0];
    expect(xLineShape.xref).toEqual("x");
    expect(xLineShape.x0).toEqual(m1Threshold);
    expect(xLineShape.x1).toEqual(m1Threshold);
    expect(xLineShape.yref).toEqual("y");
    expect(xLineShape.y0).toEqual(m2Threshold);
    expect(xLineShape.y1).toBeGreaterThan(m2Threshold);

    const yLineShape = layout.shapes[1];
    expect(yLineShape.xref).toEqual("x");
    expect(yLineShape.x0).toEqual(m1Threshold);
    expect(yLineShape.x1).toBeGreaterThan(m1Threshold);
    expect(yLineShape.yref).toEqual("y");
    expect(yLineShape.y0).toEqual(m2Threshold);
    expect(yLineShape.y1).toEqual(m2Threshold);

    const lrBoxShape = layout.shapes[2];
    expect(lrBoxShape.xref).toEqual("x");
    expect(lrBoxShape.x0).toEqual(m1Threshold);
    expect(lrBoxShape.x1).toBeGreaterThan(m1Threshold);
    expect(lrBoxShape.yref).toEqual("y");
    expect(lrBoxShape.y0).toEqual(m2Threshold);
    expect(lrBoxShape.y1).toBeLessThan(m2Threshold);

    const llBoxShape = layout.shapes[3];
    expect(llBoxShape.xref).toEqual("x");
    expect(llBoxShape.x0).toEqual(m1Threshold);
    expect(llBoxShape.x1).toBeLessThan(m1Threshold);
    expect(llBoxShape.yref).toEqual("y");
    expect(llBoxShape.y0).toEqual(m2Threshold);
    expect(llBoxShape.y1).toBeLessThan(m2Threshold);

    const ulBoxShape = layout.shapes[4];
    expect(ulBoxShape.xref).toEqual("x");
    expect(ulBoxShape.x0).toEqual(m1Threshold);
    expect(ulBoxShape.x1).toBeLessThan(m1Threshold);
    expect(ulBoxShape.yref).toEqual("y");
    expect(ulBoxShape.y0).toEqual(m2Threshold);
    expect(ulBoxShape.y1).toBeGreaterThan(m2Threshold);

    expect(lrBoxShape.y1).toEqual(llBoxShape.y1);
    expect(ulBoxShape.x1).toEqual(llBoxShape.x1);
  });

  it("reverses minimized metrics", () => {
    const m1Threshold = -1.23;
    const m2Threshold = 1.23;
    const experiment = {
      metrics: [
        {name: "m1", objective: "maximize", threshold: m1Threshold},
        {name: "m2", objective: "minimize", threshold: m2Threshold},
      ],
    };
    const observations = [];
    const layout = {};
    updateLayoutForThresholds(
      experiment,
      observations,
      {
        xAxis: {key: "m1", type: AxisTypes.OPTIMIZED_METRIC},
        yAxis: {key: "m2", type: AxisTypes.OPTIMIZED_METRIC},
      },
      layout,
    );

    expect(layout.shapes).toHaveLength(5);

    const xLineShape = layout.shapes[0];
    expect(xLineShape.yref).toEqual("y");
    expect(xLineShape.y1).toBeLessThan(m2Threshold);

    const yLineShape = layout.shapes[1];
    expect(yLineShape.xref).toEqual("x");
    expect(yLineShape.x1).toBeGreaterThan(m1Threshold);

    const urBoxShape = layout.shapes[2];
    expect(urBoxShape.xref).toEqual("x");
    expect(urBoxShape.x1).toBeGreaterThan(m1Threshold);
    expect(urBoxShape.yref).toEqual("y");
    expect(urBoxShape.y1).toBeGreaterThan(m2Threshold);

    const ulBoxShape = layout.shapes[3];
    expect(ulBoxShape.xref).toEqual("x");
    expect(ulBoxShape.x1).toBeLessThan(m1Threshold);
    expect(ulBoxShape.yref).toEqual("y");
    expect(ulBoxShape.y1).toBeGreaterThan(m2Threshold);

    const llBoxShape = layout.shapes[4];
    expect(llBoxShape.xref).toEqual("x");
    expect(llBoxShape.x1).toBeLessThan(m1Threshold);
    expect(llBoxShape.yref).toEqual("y");
    expect(llBoxShape.y1).toBeLessThan(m2Threshold);
  });

  it("handles single non-metric axis", () => {
    const m1Threshold = -1.23;
    const m2Threshold = 1.23;
    const experiment = {
      metrics: [
        {name: "m1", objective: "maximize", threshold: m1Threshold},
        {name: "m2", objective: "maximize", threshold: m2Threshold},
      ],
      parameters: [{name: "param"}],
    };
    const observations = [];
    const layout = {};
    updateLayoutForThresholds(
      experiment,
      observations,
      {
        xAxis: {key: "m2", type: AxisTypes.OPTIMIZED_METRIC},
        yAxis: {key: "param", type: AxisTypes.PARAMETER},
      },
      layout,
    );

    expect(layout.shapes).toHaveLength(2);

    const lineShape = layout.shapes[0];
    expect(lineShape.xref).toEqual("x");
    expect(lineShape.x0).toEqual(m2Threshold);
    expect(lineShape.x1).toEqual(m2Threshold);
    expect(lineShape.yref).toEqual("paper");
    expect(lineShape.y0).toEqual(0);
    expect(lineShape.y1).toEqual(1);

    const boxShape = layout.shapes[1];
    expect(boxShape.xref).toEqual("x");
    expect(boxShape.x0).toEqual(m2Threshold);
    expect(boxShape.x1).toBeLessThan(m2Threshold);
    expect(boxShape.yref).toEqual("paper");
    expect(boxShape.y0).toEqual(0);
    expect(boxShape.y1).toEqual(1);

    expect(layout.xaxis.autorange).toBe(false);
    expect(layout.xaxis.range[0]).toBeLessThan(m2Threshold);
    expect(layout.xaxis.range[1]).toBeGreaterThan(m2Threshold);
    expect(layout.yaxis).toBe(undefined);
  });
});

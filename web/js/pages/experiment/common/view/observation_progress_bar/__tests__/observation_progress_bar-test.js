/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Adapter from "enzyme-adapter-react-16";
import React from "react";
import {configure, shallow} from "enzyme";

import FlagCheckeredGlyph from "../../../../../../component/glyph/flag-checkered";
import ProgressBar from "../../../../../../component/progress_bar";
import {
  CompactObservationsProgressBar,
  ObservationsProgressBar,
} from "../index";
import {LongLabel, ShortLabel} from "../labels";

configure({adapter: new Adapter()});

describe("ObservationsProgressBar", () => {
  const experiment = {
    progress: {
      observation_budget_consumed: 3,
    },
    observation_budget: 100,
  };

  const multitaskExperiment = {
    tasks: true,
    progress: {
      observation_budget_consumed: 5.5,
      observation_count: 20,
    },
    observation_budget: 100,
  };

  it("requires an observation budget", () => {
    const noBudget = shallow(<ObservationsProgressBar experiment={{}} />);
    expect(noBudget.find("div").exists()).toBe(false);
    const zeroBudget = shallow(
      <ObservationsProgressBar experiment={{observation_budget: 0}} />,
    );
    expect(zeroBudget.find("div").exists()).toBe(false);
  });

  it("handles completion", () => {
    experiment.progress = {
      observation_budget_consumed: experiment.observation_budget,
    };
    const bar = shallow(<ObservationsProgressBar experiment={experiment} />);
    expect(bar.find(LongLabel)).toHaveLength(1);
    expect(bar.find(ShortLabel).exists()).toBe(false);
    expect(
      bar.find(ProgressBar).matchesElement(<ProgressBar width={1} />),
    ).toBe(true);
    expect(bar.find(FlagCheckeredGlyph).exists()).toBe(false);
  });

  it("handles multitask", () => {
    const bar = shallow(
      <ObservationsProgressBar experiment={multitaskExperiment} />,
    );
    expect(bar.find(LongLabel)).toHaveLength(1);
    expect(bar.find(ShortLabel).exists()).toBe(false);
  });

  it("can pass completion", () => {
    experiment.progress = {
      observation_budget_consumed: experiment.observation_budget * 2,
    };
    const bar = shallow(<ObservationsProgressBar experiment={experiment} />);
    expect(bar.find(LongLabel)).toHaveLength(1);
    expect(bar.find(ShortLabel).exists()).toBe(false);
    expect(
      bar.find(ProgressBar).matchesElement(<ProgressBar width={1} />),
    ).toBe(true);
    expect(bar.find(FlagCheckeredGlyph).exists()).toBe(false);
  });

  it("can display reduced info", () => {
    experiment.progress = {
      observation_budget_consumed: experiment.observation_budget - 1,
    };
    const bar = shallow(
      <CompactObservationsProgressBar experiment={experiment} />,
    );
    expect(bar.find(FlagCheckeredGlyph).exists()).toBe(false);
  });

  it("can display reduced info for multitask", () => {
    const bar = shallow(
      <CompactObservationsProgressBar experiment={multitaskExperiment} />,
    );
    expect(bar.find(FlagCheckeredGlyph).exists()).toBe(false);
    expect(bar.find(ShortLabel)).toHaveLength(1);
    expect(bar.find(LongLabel).exists()).toBe(false);
  });
});

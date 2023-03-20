/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import {configure, mount} from "enzyme";

import {ClickableTabs, Tab, Tabs} from "../tabs";

configure({adapter: new Adapter()});

_.each([Tabs, ClickableTabs], (TabsCls) => {
  describe(`${TabsCls.displayName}`, () => {
    it("can be empty", () => {
      const tabs = mount(<TabsCls />);
      expect(tabs.find(".tablist")).toHaveLength(1);
      expect(tabs.find(".tab-content")).toHaveLength(1);
      expect(tabs.find(".tab")).toHaveLength(0);
    });

    it("maintains classes", () => {
      const tabs = mount(
        <TabsCls className="myclass">
          <Tab label="alabel">
            <div className="a" />
          </Tab>
          <Tab label="blabel">
            <div className="b" />
          </Tab>
        </TabsCls>,
      );
      expect(tabs.find("div.myclass")).toHaveLength(1);
    });

    it("renders tabs", () => {
      const tabs = mount(
        <TabsCls active="alabel">
          <Tab label="alabel">
            <div className="a" />
          </Tab>
          <Tab label="blabel">
            <div className="b" />
          </Tab>
        </TabsCls>,
      );
      expect(tabs.find(".tablist")).toHaveLength(1);
      expect(tabs.find(".tab-content")).toHaveLength(1);
      expect(tabs.find(".tab")).toHaveLength(1);
      expect(tabs.find(".clickable-tab")).toHaveLength(2);
      expect(tabs.find(".tablist .active")).toHaveLength(1);
      expect(tabs.find(".tab-content.active")).toHaveLength(1);
      expect(tabs.find(".a")).toHaveLength(1);
      expect(tabs.find(".b")).toHaveLength(0);
    });

    it("skips falsy elements", () => {
      const tabs = mount(
        <TabsCls active="alabel">
          <Tab label="alabel">
            <div className="a" />
          </Tab>
          {false}
          {undefined}
          {null}
          <Tab label="blabel">
            <div className="b" />
          </Tab>
        </TabsCls>,
      );
      expect(tabs.find(".tablist")).toHaveLength(1);
      expect(tabs.find(".tab-content")).toHaveLength(1);
      expect(tabs.find(".tab")).toHaveLength(1);
      expect(tabs.find(".clickable-tab")).toHaveLength(2);
      expect(tabs.find(".tablist .active")).toHaveLength(1);
      expect(tabs.find(".tab-content.active")).toHaveLength(1);
      expect(tabs.find(".a")).toHaveLength(1);
      expect(tabs.find(".b")).toHaveLength(0);
    });
  });
});

describe("Tabs", () => {
  it("can be controlled", () => {
    const tabs = mount(
      <Tabs active="blabel">
        <Tab label="alabel">
          <div className="a" />
        </Tab>
        <Tab label="blabel">
          <div className="b" />
        </Tab>
      </Tabs>,
    );
    expect(tabs.find(".a")).toHaveLength(0);
    expect(tabs.find(".b")).toHaveLength(1);
  });
});

describe("ClickableTabs", () => {
  it("doesnt change when you click on active tab", () => {
    const tabs = mount(
      <ClickableTabs>
        <Tab label="alabel">
          <div className="a" />
        </Tab>
        <Tab label="blabel">
          <div className="b" />
        </Tab>
      </ClickableTabs>,
    );
    tabs.find(".clickable-tab").first().simulate("click");
    expect(tabs.find(".tablist")).toHaveLength(1);
    expect(tabs.find(".tab-content")).toHaveLength(1);
    expect(tabs.find(".tab")).toHaveLength(1);
    expect(tabs.find(".clickable-tab")).toHaveLength(2);
    expect(tabs.find(".tablist .active")).toHaveLength(1);
    expect(tabs.find(".tab-content.active")).toHaveLength(1);
    expect(tabs.find(".a")).toHaveLength(1);
    expect(tabs.find(".b")).toHaveLength(0);
  });

  it("can click to switch tabs", () => {
    const tabs = mount(
      <ClickableTabs>
        <Tab label="alabel">
          <div className="a" />
        </Tab>
        <Tab label="blabel">
          <div className="b" />
        </Tab>
      </ClickableTabs>,
    );
    tabs.find(".clickable-tab").last().simulate("click");
    expect(tabs.find(".tablist")).toHaveLength(1);
    expect(tabs.find(".tab-content")).toHaveLength(1);
    expect(tabs.find(".tab")).toHaveLength(1);
    expect(tabs.find(".clickable-tab")).toHaveLength(2);
    expect(tabs.find(".tablist .active")).toHaveLength(1);
    expect(tabs.find(".tab-content.active")).toHaveLength(1);
    expect(tabs.find(".a")).toHaveLength(0);
    expect(tabs.find(".b")).toHaveLength(1);
  });
});

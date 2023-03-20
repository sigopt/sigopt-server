/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import {configure, mount, shallow} from "enzyme";

import {Dropdown, DropdownHeader, DropdownItem} from "../dropdown";

configure({adapter: new Adapter()});

_.each({DropdownItem, DropdownHeader}, (DropdownComponent, name) =>
  describe(`${name}`, () => {
    it("renders children", () => {
      const item = mount(
        <DropdownComponent active={false}>
          <div id="child" />
        </DropdownComponent>,
      );
      expect(item.contains(<div id="child" />)).toBe(true);
    });

    it("can be inactive", () => {
      const item = mount(
        <DropdownComponent active={false}>
          <span />
        </DropdownComponent>,
      );
      expect(item.find("li").hasClass("active")).toBe(false);
    });

    it("can be active", () => {
      const item = mount(
        <DropdownComponent active={true}>
          <span />
        </DropdownComponent>,
      );
      expect(item.find("li").hasClass("active")).toBe(true);
    });
  }),
);

describe(`${DropdownHeader.displayName}`, () => {
  it("has the dropdown-header class", () => {
    const header = shallow(
      <DropdownHeader active={false}>
        <a />
      </DropdownHeader>,
    );
    expect(header.find(".dropdown-header")).toHaveLength(1);
  });
});

describe("Dropdown", () => {
  it("has a default button", () => {
    const dropdown = shallow(
      <Dropdown>
        <DropdownItem>
          <a />
        </DropdownItem>
      </Dropdown>,
      {disableLifecycleMethods: true},
    );
    expect(dropdown.find("button").hasClass("btn")).toBe(true);
    expect(dropdown.find("button").hasClass("btn-default")).toBe(true);
    expect(dropdown.find("button").hasClass("dropdown-toggle")).toBe(true);
  });

  it("accepts custom buttons", () => {
    const customButton = <a className="custom-button dropdown-toggle" />;
    const dropdown = shallow(
      <Dropdown button={customButton}>
        <DropdownItem>
          <a />
        </DropdownItem>
      </Dropdown>,
      {disableLifecycleMethods: true},
    );
    expect(dropdown.find(".custom-button")).toHaveLength(1);
    expect(dropdown.find(".custom-button").hasClass("dropdown-toggle")).toBe(
      true,
    );
  });

  it("can be disabled", () => {
    const enabledDropdown = shallow(
      <Dropdown>
        <DropdownItem>
          <a />
        </DropdownItem>
      </Dropdown>,
      {disableLifecycleMethods: true},
    );
    const disabledDropdown = shallow(
      <Dropdown disabled={true}>
        <DropdownItem>
          <a />
        </DropdownItem>
      </Dropdown>,
      {disableLifecycleMethods: true},
    );
    expect(enabledDropdown.find("button").prop("disabled")).toBe(false);
    expect(disabledDropdown.find("button").prop("disabled")).toBe(true);
  });
});

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import {configure, mount, shallow} from "enzyme";

import TextEditor from "../text_editor";

configure({adapter: new Adapter()});

describe("TextEditor", () => {
  let component;
  const props = {onChange: jest.fn(), value: ""};

  beforeEach(() => {
    component = shallow(<TextEditor {...props} />);
  });

  it("is disabled when not being edited", () => {
    expect(component.find("textarea").prop("disabled")).toBe(false);

    component.setProps({editing: false});
    expect(component.find("textarea").prop("disabled")).toBe(true);
  });

  it("sets focus in the textarea when switched to being edited", () => {
    component = mount(<TextEditor {...props} />);
    const {ref} = component.instance();
    jest.spyOn(ref.current, "focus");

    expect(ref.current.focus).not.toHaveBeenCalled();

    component.setProps({editing: true});
    // NOTE: done because .setProps() doesn't seem to be calling componentDidUpdate
    component.instance().componentDidUpdate({...props});
    expect(ref.current.focus).toHaveBeenCalled();
  });

  it("takes a value to fill the textarea with", () => {
    component = mount(<TextEditor {...props} />);

    expect(component.text()).toBe("");

    component.setProps({value: "ayy lmao"});
    expect(component.text()).toBe("ayy lmao");
  });

  it("calls its parent's onChange handler when its value changes", () => {
    expect(props.onChange).not.toHaveBeenCalled();

    const event = {
      preventDefault: _.noop,
      currentTarget: {value: "ayy lmao"},
    };
    component.find("textarea").simulate("change", event);
    expect(props.onChange).toHaveBeenCalledWith(event.currentTarget.value);
  });
});

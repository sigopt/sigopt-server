/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Adapter from "enzyme-adapter-react-16";
import React from "react";
import {configure, mount, shallow} from "enzyme";

import Modal from "../base";
import TriggerModalButton from "../button";

configure({adapter: new Adapter()});

describe("TriggerModalButton", () => {
  const defaultModal = (
    <Modal>
      <p className="rendered">Hello</p>
    </Modal>
  );

  const MockModal = class extends React.Component {
    show() {
      this.props.show();
    }
    render() {
      return null;
    }
  };

  /* eslint-disable no-console */
  console.error = (...args) => {
    throw new Error(...args);
  };

  it("wraps a modal", () => {
    const wrapper = shallow(
      <TriggerModalButton label="Text">{defaultModal}</TriggerModalButton>,
    );
    expect(wrapper.find("a")).toHaveLength(1);
    expect(wrapper.find(Modal)).toHaveLength(1);
  });

  it("can trigger a show", () => {
    const show = jest.fn();
    const modal = <MockModal show={show} />;
    const wrapper = mount(
      <TriggerModalButton label="Text">{modal}</TriggerModalButton>,
    );
    expect(show.mock.calls).toHaveLength(0);
    wrapper.find("a").simulate("click");
    wrapper.update();
    expect(show.mock.calls).toHaveLength(1);
  });

  it("allows custom buttons", () => {
    const myButton = <button type="button" />;
    const show = jest.fn();
    const modal = <MockModal show={show} />;
    const wrapper = mount(
      <TriggerModalButton button={myButton}>{modal}</TriggerModalButton>,
    );
    expect(show.mock.calls).toHaveLength(0);
    wrapper.find("button").simulate("click");
    wrapper.update();
    expect(show.mock.calls).toHaveLength(1);
  });

  it("handles onClick properly", () => {
    const show = jest.fn();
    const modal = <MockModal show={show} />;
    const onClick = jest.fn();
    const wrapper = mount(
      <TriggerModalButton label="Text" onClick={onClick}>
        {modal}
      </TriggerModalButton>,
    );
    wrapper.find("a").simulate("click");
    wrapper.update();
    expect(show.mock.calls).toHaveLength(1);
    expect(onClick.mock.calls).toHaveLength(1);
  });

  it("handles refs properly", () => {
    const modalRef = jest.fn();
    const buttonRef = jest.fn();
    const modal = React.cloneElement(defaultModal, {ref: modalRef});
    // NOTE: Needs to be wrapped in a root element. See https://github.com/airbnb/enzyme/issues/1504
    mount(
      <div>
        <TriggerModalButton label="Text" ref={buttonRef}>
          {modal}
        </TriggerModalButton>
      </div>,
    );
    expect(buttonRef.mock.calls).toHaveLength(1);
    expect(modalRef.mock.calls).toHaveLength(1);
  });

  it("requires a modal", () => {
    expect(() => shallow(<TriggerModalButton label="Text" />)).toThrow();
  });

  it("requires a label or button", () => {
    expect(() =>
      shallow(
        <TriggerModalButton>
          <Modal />
        </TriggerModalButton>,
      ),
    ).toThrow();
  });
});

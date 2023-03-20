/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import createReactClass from "create-react-class";
import {configure, mount} from "enzyme";

import SubmittableMixin from "../submittable";
import makeSubmittableComponent from "../../component/make-submittable";

configure({adapter: new Adapter()});

const MixinImpl = createReactClass({
  displayName: "SubmittableImpl",
  mixins: [SubmittableMixin],

  doSubmit: function () {
    this.submit(this.props.submitter, this.props.success, this.props.error);
  },

  render: function () {
    return (
      <div>
        <button className="submit" onClick={this.doSubmit} type="submit" />
        {this.state.submitting && <div className="submitting" />}
        {this.state.submitted && <div className="submitted" />}
      </div>
    );
  },
});

const HOCImpl = makeSubmittableComponent(
  class extends React.Component {
    doSubmit = () => {
      this.props.submit(
        this.props.submitter,
        this.props.success,
        this.props.error,
      );
    };

    render() {
      return (
        <div>
          <button className="submit" onClick={this.doSubmit} type="submit" />
          {this.props.submitting && <div className="submitting" />}
          {this.props.submitted && <div className="submitted" />}
        </div>
      );
    }
  },
);

_.each([MixinImpl, HOCImpl], (SubmittableImpl) => {
  describe(`Submittable: ${SubmittableImpl.constructor.name}`, () => {
    const callSuccess = (success) => success();
    const callSuccessWithArgs =
      (...args) =>
      (success) =>
        success(...args);
    const callError = (success, error) => error();
    const callErrorWithArgs =
      (...args) =>
      (success, error) =>
        error(...args);

    it("renders", () => {
      const wrapper = mount(<SubmittableImpl />);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
    });

    it("doesnt need args for success", () => {
      const wrapper = mount(<SubmittableImpl submitter={callSuccess} />);
      wrapper.find(".submit").simulate("click");
      wrapper.update();
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(1);
    });

    it("doesnt need args for error", () => {
      const wrapper = mount(<SubmittableImpl submitter={callError} />);
      wrapper.find(".submit").simulate("click");
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
    });

    it("succeeds synchronously", () => {
      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(
        <SubmittableImpl
          submitter={callSuccessWithArgs(1, 2)}
          success={success}
          error={error}
        />,
      );
      wrapper.find(".submit").simulate("click");
      expect(success.mock.calls).toEqual([[1, 2]]);
      expect(error.mock.calls).toEqual([]);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(1);
    });

    it("succeeds asynchronously", () => {
      let successHolder;
      const submitter = function (success) {
        successHolder = success;
      };

      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(
        <SubmittableImpl
          submitter={submitter}
          success={success}
          error={error}
        />,
      );
      wrapper.find(".submit").simulate("click");
      expect(wrapper.find(".submitting")).toHaveLength(1);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([]);

      successHolder(1, 2);
      wrapper.update();

      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(1);
      expect(success.mock.calls).toEqual([[1, 2]]);
      expect(error.mock.calls).toEqual([]);
    });

    it("errors synchronously", () => {
      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(
        <SubmittableImpl
          submitter={callErrorWithArgs(1, 2)}
          success={success}
          error={error}
        />,
      );
      wrapper.find(".submit").simulate("click");
      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([[1, 2]]);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
    });

    it("errors asynchronously", () => {
      let errorHolder;
      const submitter = function (success, error) {
        errorHolder = error;
      };

      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(
        <SubmittableImpl
          submitter={submitter}
          success={success}
          error={error}
        />,
      );
      wrapper.find(".submit").simulate("click");

      errorHolder(1, 2);
      wrapper.update();

      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(success.mock.calls).toEqual([]);
      expect(error.mock.calls).toEqual([[1, 2]]);
    });

    it("handles concurrent submits", () => {
      let submitterCalls = 0;
      const submitter = function () {
        submitterCalls += 1;
      };

      const success = jest.fn();
      const wrapper = mount(
        <SubmittableImpl submitter={submitter} success={success} />,
      );
      wrapper.find(".submit").simulate("click");
      wrapper.find(".submit").simulate("click");
      wrapper.find(".submit").simulate("click");
      expect(submitterCalls).toEqual(1);
    });
  });
});

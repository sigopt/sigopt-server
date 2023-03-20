/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import createReactClass from "create-react-class";
import {configure, mount} from "enzyme";

import EditableMixin from "../editable";
import SubmittableMixin from "../submittable";
import makeEditableComponent from "../../component/make-editable";

configure({adapter: new Adapter()});

const MixinImpl = createReactClass({
  displayName: "EditableImpl",
  mixins: [SubmittableMixin, EditableMixin],

  getInitialState: function () {
    return {
      // eslint-disable-next-line react/no-unused-state
      field: 0,
    };
  },

  render: function () {
    return (
      <div>
        {this.state.editing && <div className="editing" />}
        {this.state.submitting && <div className="submitting" />}
        {this.state.submitted && <div className="submitted" />}
      </div>
    );
  },
});

const HOCImpl = makeEditableComponent(
  class extends React.Component {
    constructor() {
      super();
      this.state = {field: 0};
    }

    startEditing = () => this.props.startEditing(this.state);
    stopEditingAndSubmit = (...args) =>
      this.props.stopEditingAndSubmit(...args);
    cancelEditing = () =>
      this.props.cancelEditing((recoveryState) => this.setState(recoveryState));

    render() {
      return (
        <div>
          {this.props.editing && <div className="editing" />}
          {this.props.submitting && <div className="submitting" />}
          {this.props.submitted && <div className="submitted" />}
        </div>
      );
    }
  },
);

_.each([MixinImpl, HOCImpl], (EditableImpl) => {
  const getEditable = (wrapper) => {
    if (EditableImpl === MixinImpl) {
      return wrapper.instance();
    } else {
      return wrapper.childAt(0).childAt(0).childAt(0).childAt(0).instance();
    }
  };

  describe(`Editable: ${EditableMixin.constructor.name}`, () => {
    const callSuccess = (success) => success();
    const callError = (success, error) => error();

    it("renders", () => {
      const wrapper = mount(<EditableImpl />);
      expect(wrapper.find(".editing")).toHaveLength(0);
    });

    it("can succeed synchronously", () => {
      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(<EditableImpl />);

      getEditable(wrapper).startEditing();
      getEditable(wrapper).setState({field: 1});
      getEditable(wrapper).stopEditingAndSubmit(callSuccess, success, error);
      wrapper.update();

      expect(success.mock.calls).toHaveLength(1);
      expect(error.mock.calls).toHaveLength(0);
      expect(wrapper.find(".editing")).toHaveLength(0);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(1);
      expect(getEditable(wrapper).state.field).toEqual(1);
    });

    it("can succeed asynchronously", () => {
      let successHolder;
      const submitter = function (success) {
        successHolder = success;
      };

      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(<EditableImpl />);

      getEditable(wrapper).startEditing();
      getEditable(wrapper).setState({field: 1});
      getEditable(wrapper).stopEditingAndSubmit(submitter, success, error);
      wrapper.update();

      expect(success.mock.calls).toHaveLength(0);
      expect(error.mock.calls).toHaveLength(0);
      expect(wrapper.find(".editing")).toHaveLength(1);
      expect(wrapper.find(".submitting")).toHaveLength(1);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(getEditable(wrapper).state.field).toEqual(1);

      successHolder();
      wrapper.update();

      expect(success.mock.calls).toHaveLength(1);
      expect(error.mock.calls).toHaveLength(0);
      expect(wrapper.find(".editing")).toHaveLength(0);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(1);
      expect(getEditable(wrapper).state.field).toEqual(1);
    });

    it("can error synchronously", () => {
      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(<EditableImpl />);

      getEditable(wrapper).startEditing();
      getEditable(wrapper).setState({field: 1});
      getEditable(wrapper).stopEditingAndSubmit(callError, success, error);
      wrapper.update();

      expect(success.mock.calls).toHaveLength(0);
      expect(error.mock.calls).toHaveLength(1);
      expect(wrapper.find(".editing")).toHaveLength(1);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(getEditable(wrapper).state.field).toEqual(1);
    });

    it("can error asynchronously", () => {
      let errorHolder;
      const submitter = function (success, error) {
        errorHolder = error;
      };

      const success = jest.fn();
      const error = jest.fn();
      const wrapper = mount(<EditableImpl />);

      getEditable(wrapper).startEditing();
      getEditable(wrapper).setState({field: 1});
      getEditable(wrapper).stopEditingAndSubmit(submitter, success, error);
      wrapper.update();

      expect(success.mock.calls).toHaveLength(0);
      expect(error.mock.calls).toHaveLength(0);
      expect(wrapper.find(".editing")).toHaveLength(1);
      expect(wrapper.find(".submitting")).toHaveLength(1);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(getEditable(wrapper).state.field).toEqual(1);

      errorHolder();
      wrapper.update();

      expect(success.mock.calls).toHaveLength(0);
      expect(error.mock.calls).toHaveLength(1);
      expect(wrapper.find(".editing")).toHaveLength(1);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(getEditable(wrapper).state.field).toEqual(1);
    });

    it("can cancel editing", () => {
      const wrapper = mount(<EditableImpl />);

      getEditable(wrapper).startEditing();
      wrapper.update();

      expect(wrapper.find(".editing")).toHaveLength(1);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(getEditable(wrapper).state.field).toEqual(0);

      getEditable(wrapper).setState({field: 1});
      getEditable(wrapper).cancelEditing();
      wrapper.update();

      expect(wrapper.find(".editing")).toHaveLength(0);
      expect(wrapper.find(".submitting")).toHaveLength(0);
      expect(wrapper.find(".submitted")).toHaveLength(0);
      expect(getEditable(wrapper).state.field).toEqual(0);
    });
  });
});

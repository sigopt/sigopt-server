/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Adapter from "enzyme-adapter-react-16";
import React from "react";
import {configure, shallow} from "enzyme";

import {EditInfo, NotesEditor} from "../notes_editor";

configure({adapter: new Adapter()});

describe("EditInfo", () => {
  let component;
  const props = {
    lastEditedBy: "SigOpt User",
    lastUpdated: 1583859664094,
  };

  beforeEach(() => {
    component = shallow(<EditInfo />);
  });

  it("handles when no date or author is provided", () => {
    expect(component.text()).toMatch("--");
  });

  it("handles when no date is provided", () => {
    component.setProps({lastEditedBy: props.lastEditedBy});
    expect(component.text()).toMatch("--");
  });

  it("handles when no author is provided", () => {
    component.setProps({lastUpdated: props.lastUpdated});
    expect(component.text()).toMatch("--");
  });

  it("displays time and author of last edit when they are both provided", () => {
    component.setProps(props);
    expect(component.text()).not.toMatch("--");
    expect(component.text()).toMatch(`by ${props.lastEditedBy}`);
  });

  it("rerenders only when lastUpdated is updated or initially set", () => {
    jest.spyOn(component.instance(), "shouldComponentUpdate");

    component.setProps({});
    expect(component.instance().shouldComponentUpdate).toHaveReturnedWith(
      false,
    );

    component.setProps(props);
    expect(component.instance().shouldComponentUpdate).toHaveReturnedWith(true);

    component.setProps(props);
    expect(component.instance().shouldComponentUpdate).toHaveReturnedWith(
      false,
    );

    component.setProps({lastUpdated: 1583859664095});
    expect(component.instance().shouldComponentUpdate).toHaveReturnedWith(true);
  });
});

describe("NotesEditor", () => {
  let component;
  const note = {
    client: "1",
    contents: "abc",
    created: 1583881628,
    object: "project_note",
    project: "example-project",
    user: "1",
  };
  const fetch = jest.fn(() => Promise.resolve({name: "Not SigOpt User"}));
  const props = {
    alertBroker: {handle: jest.fn()},
    cancelEditing: jest.fn(),
    currentUser: {id: "1", name: "SigOpt User", object: "user"},
    editing: false,
    onSubmit: jest.fn().mockResolvedValue(null),
    startEditing: jest.fn(),
    stopEditingAndSubmit: jest.fn(),
  };
  const context = {
    services: {
      promiseApiClient: {users: () => ({fetch})},
    },
  };

  const emptyState = {
    contents: "",
    lastEditedBy: null,
    lastUpdated: null,
  };

  // NOTE: for waiting on async functions that aren't called directly
  const flushPromises = () => new Promise(process.nextTick);

  beforeEach(() => {
    component = shallow(<NotesEditor {...props} />, {context});
  });

  it("sets default state from passed-in note if provided", async () => {
    expect(component.state()).toEqual(emptyState);

    component = shallow(<NotesEditor note={note} {...props} />);
    await flushPromises();
    expect(component.state()).toEqual({
      contents: note.contents,
      lastEditedBy: props.currentUser.name,
      lastUpdated: note.created,
    });
  });

  it("updates its state when the contents of the text editor are changed", () => {
    expect(component.state("contents")).toBe("");

    component.instance().handleChange("abc");
    expect(component.state("contents")).toBe("abc");
  });

  it("calls its parent's onSubmit handler with note's contents when submitted", async () => {
    expect(props.onSubmit).not.toHaveBeenCalled();

    await component.instance().handleSubmit(_.noop, _.noop);
    expect(props.onSubmit).toHaveBeenCalledWith({
      contents: component.state("contents"),
    });
  });

  it("delegates to respective handlers on successful and failed submission", async () => {
    const successMock = jest.fn();
    const errorMock = jest.fn();

    props.onSubmit.mockResolvedValueOnce({});
    await component.instance().handleSubmit(successMock, errorMock);
    expect(successMock).toHaveBeenCalled();
    expect(errorMock).not.toHaveBeenCalled();

    successMock.mockReset();
    errorMock.mockReset();

    props.onSubmit.mockRejectedValueOnce(new Error());
    await component.instance().handleSubmit(successMock, errorMock);
    expect(successMock).not.toHaveBeenCalled();
    expect(errorMock).toHaveBeenCalled();
  });

  it("updates state when submission succeeds", async () => {
    expect(component.state("lastEditedBy")).toBeNull();
    expect(component.state("lastUpdated")).toBeNull();

    await component.instance().handleSuccess(note);
    expect(component.state("lastEditedBy")).toBe(props.currentUser.name);
    expect(component.state("lastUpdated")).toEqual(note.created);
  });

  it("rethrows the incoming error when submission fails", () => {
    const err = new Error("Oh no!");
    expect(() => {
      component.instance().handleFailure(err);
    }).toThrow(err);
  });

  it("short-circuits fetching name of user who last edited the note if it is the current user", async () => {
    expect(fetch).not.toHaveBeenCalled();

    await component.instance().getUserName(props.currentUser.id);
    expect(fetch).not.toHaveBeenCalled();

    await component.instance().getUserName("2");
    expect(fetch).toHaveBeenCalled();
  });

  it("calls its parent's startEditing handler with current state when editing is started", () => {
    expect(props.startEditing).not.toHaveBeenCalled();

    component.instance().startEditing();
    expect(props.startEditing).toHaveBeenCalledWith(emptyState);
  });

  it("calls its parent's cancelEditing handler with callback when editing is cancelled", () => {
    expect(props.cancelEditing).not.toHaveBeenCalled();

    component.instance().cancelEditing();
    expect(props.cancelEditing).toHaveBeenCalledWith(expect.any(Function));
  });

  it("calls its parent's stopEditingAndSubmit handler with handlers when editing is saved", () => {
    expect(props.stopEditingAndSubmit).not.toHaveBeenCalled();

    component.instance().stopEditingAndSubmit();
    expect(props.stopEditingAndSubmit).toHaveBeenCalledWith(
      expect.any(Function),
      expect.any(Function),
      expect.any(Function),
    );
  });

  it("shows different buttons depending on if editing is active or not", () => {
    expect(component.find(".action-buttons").children()).toHaveLength(1);

    component.setProps({editing: true});
    expect(component.find(".action-buttons").children()).toHaveLength(2);
  });
});

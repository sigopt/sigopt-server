/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../styles/caret_glyph.less";
import "../styles/tools_glyph.less";

import $ from "jquery";
import _ from "underscore";
import React from "react";

import AngleDownGlyph from "../../../component/glyph/angle-down";
import EyeGlyph from "../../../component/glyph/eye";
import XmarkGlyph from "../../../component/glyph/xmark";
import {Dropdown} from "../../../component/dropdown";

class ViewListItem extends React.Component {
  deleteView = () => this.props.deleteView(this.props.view.id);

  render() {
    const {view, activateView, showDelete} = this.props;
    return (
      <div className="list-item" key={view.id}>
        <span
          className="view-name"
          onClick={activateView.bind(null, view.payload)}
        >
          {view.display_name}
        </span>

        {showDelete ? (
          <XmarkGlyph onClick={this.deleteView} className="close-glyph" />
        ) : null}
      </div>
    );
  }
}

const ViewsList = ({views, deleteView, activateView}) => {
  const showProjectViews = views.restViews && views.restViews.length > 0;
  return (
    <div className="views-list">
      <div className="title-row">
        {" "}
        <h3 className="title"> My Views </h3>{" "}
      </div>
      {_.map(views.currentUserViews, (view) => (
        <ViewListItem
          key={view.id}
          view={view}
          deleteView={deleteView}
          activateView={activateView}
          showDelete={true}
        />
      ))}
      {showProjectViews ? (
        <div className="title-row">
          {" "}
          <h3 className="title"> Team Views </h3>{" "}
        </div>
      ) : null}
      {showProjectViews
        ? _.map(views.restViews, (view) => (
            <ViewListItem
              key={view.id}
              view={view}
              deleteView={deleteView}
              activateView={activateView}
              showDelete={false}
            />
          ))
        : null}
    </div>
  );
};

const CreateNewViewTextInput = ({newViewInputText, onViewNameInputChange}) => (
  <input
    className="text-input mpm-border"
    placeholder="New view name..."
    value={newViewInputText}
    onChange={onViewNameInputChange}
  />
);

const CreateNewViewButton = ({createView}) => (
  <button
    type="button"
    className="btn basic-button-white mpm-border"
    onClick={createView}
  >
    Save Current View
  </button>
);

export class ViewsDropdown extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      newViewInputText: "",
    };
  }

  componentDidMount() {
    // Hack for bootstrap dropdowns to prevent closing
    // Should likely be moved to an option for in <Dropdown />
    $(document).on("click", ".views-dropdown", (e) => e.stopPropagation());
  }

  createView = () => {
    this.props.createView(this.state.newViewInputText);
  };

  onViewNameInputChange = (e) => {
    this.setState({newViewInputText: e.target.value});
  };

  render() {
    return (
      <div className="views-dropdown noGridDrag">
        {this.props.views ? (
          <ViewsList
            activateView={this.props.activateView}
            views={this.props.views}
            deleteView={this.props.deleteView}
          />
        ) : null}
        <hr />
        <div className="new-view-row">
          <CreateNewViewTextInput
            newViewInputText={this.state.newViewInputText}
            onViewNameInputChange={this.onViewNameInputChange}
          />
          <CreateNewViewButton createView={this.createView} />
        </div>
      </div>
    );
  }
}

export const ViewsDropdownButton = ({
  createView,
  deleteView,
  activateView,
  views,
}) => {
  const button = (
    <button
      type="button"
      className="btn basic-button-white mpm-border dropdown-button noGridDrag"
    >
      <EyeGlyph className="tools-glyph" />
      Views
      <AngleDownGlyph className="caret-glyph" />
    </button>
  );

  return (
    <Dropdown
      button={button}
      className="dropdown mpm-dropdown"
      id="view-dropdown"
    >
      <ViewsDropdown
        createView={createView}
        deleteView={deleteView}
        activateView={activateView}
        views={views}
      />
    </Dropdown>
  );
};

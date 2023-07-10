/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import React from "react";
import ReactDOM from "react-dom";
import {connect} from "react-redux";

import ArrowsUpDownLeftRightGlyph from "../../../../component/glyph/arrows-up-down-left-right";
import PencilGlyph from "../../../../component/glyph/pencil";
import TriangleExclamationGlyph from "../../../../component/glyph/triangle-exclamation";
import UpRightAndDownLeftFromCenterGlyph from "../../../../component/glyph/up-right-and-down-left-from-center";
import XmarkGlyph from "../../../../component/glyph/xmark";
import {WidgetDefinitions} from "./widgets";
import {deleteWidget} from "../state/dashboards_slice";

const wrapperStyle = {
  border: "2px solid #CECECE",
  borderRadius: 5,
  padding: 10,
  paddingTop: 20,
  height: "100%",
  width: "100%",
};

const topRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  width: "100%",
  marginTop: -30,
  marginBottom: 5,
};

const titleStyle = {
  backgroundColor: "white",
  paddingLeft: 10,
  paddingRight: 10,
  borderRadius: 10,
  marginTop: -3,
  whiteSpace: "nowrap",
};

const controlsStyle = {
  backgroundColor: "white",
  paddingLeft: 10,
  borderRadius: 10,
  whiteSpace: "nowrap",
};

const ControlsIcon = ({glyph, onClick, className}) => {
  const Glyph = glyph || "span";
  return (
    <Glyph
      onClick={onClick}
      className={`${className} hover-grey-darken margin-r-10`}
    />
  );
};

const WidgetWarning = ({warning}) => {
  return (
    <div className="widget-warning">
      <div>
        <TriangleExclamationGlyph className="margin-r-10 warning-yellow" />
      </div>

      <div className="overflow-ellipsis">{warning}</div>
    </div>
  );
};

export class WidgetContainer extends React.Component {
  // Redirect resizes from react-grid-layout
  // Maybe should try and target directly from runs-dashboard
  componentDidMount() {
    const node = ReactDOM.findDOMNode(this);
    node.addEventListener("resize", () => {
      const widget = node.children[1];
      const event = new CustomEvent("resize");
      widget.dispatchEvent(event);
    });
  }

  openBigWidgetModal = () =>
    this.props.openBigWidgetModal(this.props.widgetInstance, this.props.id);

  deleteWidget = () => this.props.deleteWidget(this.props.id);

  render() {
    const {widgetInstance} = this.props;
    const widgetDefinition = WidgetDefinitions[widgetInstance.type];
    const title = widgetInstance.title || widgetDefinition.displayName;
    const warning = widgetInstance.warning;
    const showEditorPen = widgetDefinition.editorIsReactComponent;
    const showDeleteWidget = widgetDefinition.removable;

    const Controls = (
      <div style={controlsStyle}>
        {showEditorPen ? (
          <ControlsIcon
            glyph={PencilGlyph}
            className="cursor-pointer"
            onClick={this.props.openEditor.bind(
              null,
              widgetInstance,
              this.props.id,
            )}
          />
        ) : null}
        <ControlsIcon
          onClick={this.openBigWidgetModal}
          glyph={UpRightAndDownLeftFromCenterGlyph}
          className="cursor-pointer"
        />
        <ControlsIcon
          glyph={ArrowsUpDownLeftRightGlyph}
          className="dashboard-drag-handle cursor-grab"
        />
        {showDeleteWidget ? (
          <>
            <ControlsIcon
              glyph={null}
              className="just-here-to-space-stuff-out"
            />
            <ControlsIcon
              onClick={this.deleteWidget}
              glyph={XmarkGlyph}
              className="cursor-pointer"
            />
          </>
        ) : null}
      </div>
    );

    return (
      <div style={wrapperStyle}>
        <div style={topRowStyle}>
          <div style={titleStyle}> {title} </div>
          {warning ? <WidgetWarning warning={warning} /> : null}
          {Controls}
        </div>
        {this.props.children}
      </div>
    );
  }
}

const mapDispatchToProps = {deleteWidget};

export const ConnectedWidgetContainer = connect(
  null,
  mapDispatchToProps,
)(WidgetContainer);

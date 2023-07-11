/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import AngleLeftGlyph from "../../../../component/glyph/angle-left";
import Modal from "../../../../component/modal/base";
import XmarkGlyph from "../../../../component/glyph/xmark";
import {CommonWidgetEditor} from "../widgets/common_widget_editor";
import {WidgetDefinitions} from "../widgets/widgets";
import {addNewWidget, replaceWidget} from "../state/dashboards_slice";
import {isDefinedAndNotNull} from "../../../../utils";

// Runs into ESLINT no-shadow issue. Might be able to change hoisting rules.
const WidgetMenuList = ({
  setEditorState,
  fullReduxState,
  addNewWidgetAndClose,
}) => {
  // Widgets can either have function builders that immediately create a new widget
  // or a builder that is a react component.
  const displayBuilderOrCreate = (widgetDefinition) => {
    if (widgetDefinition.editorIsReactComponent) {
      const widgetStartingState =
        widgetDefinition.newWidgetStateBuilder(fullReduxState);
      setEditorState(widgetDefinition, widgetStartingState, null);
    } else {
      addNewWidgetAndClose(widgetDefinition.editor(fullReduxState));
    }
  };

  // For simplicity each dashboard has a single table that cannot be removed.
  const userCreatableWidgets = _.filter(
    WidgetDefinitions,
    (widgetDefinition) => widgetDefinition.removable === true,
  );

  return (
    <div className="widget-menu-list">
      <div className="flex-column">
        {_.map(userCreatableWidgets, (widgetDefinition) => (
          <button
            key={widgetDefinition.displayName}
            onClick={displayBuilderOrCreate.bind(null, widgetDefinition)}
            style={{marginBottom: 10}}
            type="button"
            className="btn basic-button-white mpm-border noGridDrag"
          >
            Create New {widgetDefinition.displayName}
          </button>
        ))}
      </div>
    </div>
  );
};

const WidgetEditorModal = ({
  resetEditorState,
  editorState,
  fullReduxState,
  setEditorState,
  reduxAddNewWidget,
  reduxReplaceWidget,
  modalRef,
}) => {
  const editing = isDefinedAndNotNull(editorState.widgetId);
  const addNewWidgetAndClose = (payload) => {
    reduxAddNewWidget(payload);
    modalRef.current.hide();
  };

  const cancelEditing = () => {
    modalRef.current.hide();
    resetEditorState();
  };

  const upsertWidget = (widgetData) => {
    if (editing) {
      const previousLaylout = editorState.widgetData.layout;
      widgetData.layout = _.clone(previousLaylout);

      reduxReplaceWidget({
        widgetId: editorState.widgetId,
        widgetData: widgetData,
      });
    } else {
      reduxAddNewWidget(widgetData);
    }
    resetEditorState();
    modalRef.current.hide();
  };

  const closeModal = () => {
    modalRef.current.hide();
  };

  const showWidgetMenuList = !editorState.widgetDefinition;

  const title = editorState.widgetDefinition
    ? editorState.widgetDefinition.displayName
    : "Create New Widget";

  return (
    <Modal ref={modalRef} className="editor-modal">
      <div className="editor-modal-controls">
        <div>
          {!showWidgetMenuList && !editing && (
            <AngleLeftGlyph
              className="cursor-pointer glyph-medium-font"
              onClick={resetEditorState}
            />
          )}
        </div>
        <div>
          <h4>{title}</h4>
        </div>
        <div>
          <XmarkGlyph
            className="cursor-pointer close-glyph"
            onClick={closeModal}
          />
        </div>
      </div>

      <hr />

      {showWidgetMenuList ? (
        <WidgetMenuList
          fullReduxState={fullReduxState}
          setEditorState={setEditorState}
          addNewWidgetAndClose={addNewWidgetAndClose}
        />
      ) : null}
      {!showWidgetMenuList && (
        <CommonWidgetEditor
          key={JSON.stringify(editorState.widgetData)}
          editorState={editorState}
          upsertWidget={upsertWidget}
          cancelEditing={cancelEditing}
        />
      )}
    </Modal>
  );
};

// We pass down full redux state so immediate function builders have access to state
const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
  fullReduxState: state,
});
const mapDispatchToProps = {
  reduxAddNewWidget: addNewWidget,
  reduxReplaceWidget: replaceWidget,
};

export const ConnectedWidgetEditorModal = connect(
  mapStateToProps,
  mapDispatchToProps,
)(WidgetEditorModal);

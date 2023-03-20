/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import React from "react";

import Modal from "../../../../component/modal/base";
import {WidgetDefinitions} from "../widgets/widgets";

const modalStyle = {
  width: "100%",
  height: "80vh",
};

export const BigWidgetModal = (props) => {
  let WidgetComponent = null;
  if (props.widget) {
    WidgetComponent = WidgetDefinitions[props.widget.type].component;
  }

  return (
    <Modal
      ref={props.modalRef}
      {...props}
      title={props.widget && props.widget.title}
      className="big-modal"
    >
      <div style={modalStyle}>
        {props.render && props.widget && (
          <WidgetComponent
            widget={props.widget}
            updateWidget={props.updateWidget.bind(null, props.widgetId)}
          />
        )}
      </div>
    </Modal>
  );
};

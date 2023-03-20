/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

export const WidgetTitleEditor = ({title, setTitle}) => {
  return (
    <div className="flex-row align-center full-width">
      <label htmlFor="note-title" className="title-editor-label">
        Title:
      </label>
      <input
        className="mpm-border flex-grow"
        id="note-title"
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
    </div>
  );
};

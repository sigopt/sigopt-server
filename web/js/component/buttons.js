/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import ArrowsRotateGlyph from "./glyph/arrows-rotate";
import LinkGlyph from "./glyph/link";
import PlusGlyph from "./glyph/plus";
import XmarkGlyph from "./glyph/xmark";

export const AddButton = function (props) {
  return (
    <span className="btn btn-xs btn-add" value="Add" {...props}>
      <PlusGlyph />
    </span>
  );
};

export const RemoveButton = function (props) {
  return (
    <span className="btn btn-xs btn-remove" value="Remove" {...props}>
      <XmarkGlyph />
    </span>
  );
};

export const DeleteButton = function (props) {
  return (
    <button
      className="btn btn-sm btn-danger delete-btn"
      type="button"
      value="Delete"
      {...props}
    >
      <XmarkGlyph />
    </button>
  );
};

export const ShareButton = function (props) {
  return (
    <button
      className="btn btn-sm btn-secondary share-btn"
      type="button"
      value="Share"
      {...props}
    >
      <LinkGlyph />
    </button>
  );
};

export const RotateButton = function (props) {
  return (
    <button
      className="btn btn-sm btn-secondary rotate-btn"
      type="button"
      value="Rotate"
      {...props}
    >
      <ArrowsRotateGlyph />
    </button>
  );
};

export const TextButton = function (props) {
  return (
    <button
      className="btn btn-md btn-primary"
      type="button"
      value={props.text}
      {...props}
    >
      {props.text}
    </button>
  );
};

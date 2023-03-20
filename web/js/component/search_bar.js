/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import MagnifyingGlassGlyph from "./glyph/magnifying-glass";

export const SearchBar = ({onChange, value, placeholder}) => (
  <div className="search-bar mpm-border noGridDrag">
    <MagnifyingGlassGlyph glyph="magnifying-glass" className="search-glyph" />
    <input className="search-input" {...{onChange, value, placeholder}} />
  </div>
);

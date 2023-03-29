#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# This script adds support for the provided glyph by adding a css style for .fa-$GLYPH:before with content:GLYPH_CHARACTER
# and creating a React component for the glyph at ./$GLYPH
set -e
set -o pipefail

GLYPH="${1:?Provide the fontawesome glyph identifier as the first argument}"
GLYPH_DIR="web/js/component/glyph/$GLYPH"
COMMENT="auto-generated via $0 $*"

mkdir -p "$GLYPH_DIR"

cat <<EOF >"$GLYPH_DIR/glyph.less"
// $COMMENT

@import "../base.less";
.support-glyph($GLYPH);
EOF

cat <<EOF >"$GLYPH_DIR/index.js"
// $COMMENT

import "./glyph.less";

import React from "react";

import Glyph from "../base";

const glyphName = "$GLYPH";
export default class extends React.Component {
  static displayName = \`Glyph(\${glyphName})\`;
  static glyphName = glyphName;

  render() {
    return <Glyph {...this.props} glyph={glyphName} />;
  }
};
EOF

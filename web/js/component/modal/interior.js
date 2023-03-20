/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import ModalBody from "./body";
import ModalFooter from "./footer";
import ModalFrame from "./frame";
import ModalTitle from "./title";

/**
 * All the rendered content inside a Modal. Useful if you want to include something
 * that looks like a Modal on a page without actually having it overlay the page
 */
export default (props) => (
  <ModalFrame>
    <ModalTitle {...props} />
    <ModalBody {...props}>{props.children}</ModalBody>
    <ModalFooter {...props} />
  </ModalFrame>
);

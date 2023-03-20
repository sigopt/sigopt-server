/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import E400Img from "./400.png";
import E404Img from "./404.png";
import E500Img from "./500.png";

export {E404Img};

export default function getErrorImage(status) {
  const stringStatus = (status || 500).toString();
  return (
    {
      400: E400Img,
      404: E404Img,
      500: E500Img,
    }[stringStatus] || E500Img
  );
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {PUBLIC_ASSETS_URL} from "../../net/constant";
import {headCodeHash} from "../../chrome/head_hash";

export default function setStandardHeaders() {
  return (req, res, next) => {
    res.header("Cache-Control", "private, no-cache, no-store, must-revalidate");
    res.header(
      "Content-Type",
      req.endpointResponse?.contentType ?? "text/html; charset=utf-8",
    );
    res.header("Expires", "Sat, 01 Jan 2000 00:00:00 GMT");
    res.header("X-Content-Type-Options", "nosniff");
    res.header("X-Frame-Options", "DENY");
    res.header("X-XSS-Protection", "1; mode=block");
    res.header("X-Powered-By", "multi-armed bandits"); // Override default to obscure
    const csp = [
      "default-src 'self'",
      "font-src 'self' data:",
      "form-action 'self'",
      "frame-ancestors 'none'",
      "frame-src 'none'",
      "img-src 'self' data: blob:",
      "object-src 'none'",
      "style-src 'self' 'unsafe-inline'",
      "upgrade-insecure-requests",
      `media-src ${PUBLIC_ASSETS_URL}`,
    ];
    if (process.env.NODE_ENV === "production") {
      csp.push(`script-src 'self' 'sha512-${headCodeHash}'`);
    } else {
      const assetHost = new URL(
        req.configBroker.get("web.static_asset_url", "sigopt.ninja"),
      ).host;
      csp.push(`connect-src 'self' wss://${assetHost}`);
      csp.push("script-src 'self' 'unsafe-eval' 'unsafe-inline'");
    }
    res.header("Content-Security-Policy", csp.join("; "));
    next();
  };
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";

import NetError from "../alert/error";
import Service from "../services/base";

export default class JqueryRequestor extends Service {
  request(options, success, error) {
    const headers = options.headers;
    const method = (options.method || "GET").toUpperCase();
    let data = options.data;
    let url = options.url;

    // https://bugs.jquery.com/ticket/11586
    if (method === "DELETE") {
      const queryParams = data ? $.param(data) : "";
      data = null;
      url = `${url}?${queryParams}`;
    }

    $.ajax({
      dataType: "text",
      data: data,
      headers: headers,
      type: method,
      url: url,
      success: (response, textStatus, jqXhr) => success(response, jqXhr.status),
      error: (jqXhr) => {
        if (error) {
          error(
            NetError.constructFromAjaxResponse(jqXhr, {
              path: url,
              params: data,
              type: method,
            }),
          );
          return;
        }
      },
    });
  }
}

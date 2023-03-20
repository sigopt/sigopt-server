/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Uri from "jsuri";

export default class ParsedUrl {
  constructor(url) {
    this.url = new Uri(url);
  }

  get anchor() {
    return this.url.anchor();
  }

  get query() {
    return this.url.query();
  }

  get hash() {
    const hash = this.anchor;
    if (hash) {
      return `#${hash}`;
    }
    return "";
  }

  get host() {
    return this.url.host();
  }

  set host(hname) {
    this.url.setHost(hname);
  }

  get origin() {
    const originUrl = new Uri();
    originUrl.setProtocol(this.scheme);
    originUrl.setHost(this.host);
    originUrl.setPort(this.port);
    return originUrl.toString();
  }

  set origin(orig) {
    const originUrl = new Uri(orig);
    this.scheme = originUrl.protocol();
    this.host = originUrl.host();
    this.port = originUrl.port();
  }

  // NOTE: consider the string 'example.com/path/name/here'
  // URI.js path() => 'example.com/path/name/here'
  // jsUri path() =>  '/path/name/here'
  get path() {
    const parsedPath = this.url.path();
    if (!parsedPath && this.url.host()) {
      return "/";
    }
    return parsedPath;
  }

  set path(path) {
    this.url.setPath(path);
  }

  get params() {
    const queryString = this.url.query();
    const index = queryString.indexOf("?");
    const paramString =
      index < 0 ? queryString : queryString.substring(index + 1);
    return _.chain(paramString.split("&"))
      .map((param) => {
        const [key, value] = _.chain(param.split("="))
          .map((s) => s.replace(/\+/gu, " "))
          .map(decodeURIComponent)
          .value();
        return [key, value];
      })
      .object()
      .value();
  }

  set params(paramObj) {
    this.url.setQuery("");
    _.each(paramObj, (v, k) => this.url.addQueryParam(k, v));
  }

  get port() {
    return this.url.port();
  }

  set port(pnumber) {
    this.url.setPort(pnumber);
  }

  get scheme() {
    return this.url.protocol();
  }

  set scheme(sch) {
    this.url.setProtocol(sch);
  }

  get resource() {
    const resourceUrl = new Uri();
    resourceUrl.setPath(this.path);
    resourceUrl.setQuery(this.query);
    resourceUrl.setAnchor(this.anchor);
    return resourceUrl.toString();
  }

  toString() {
    return this.url.toString();
  }
}

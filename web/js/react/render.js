/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// Needed for React 16 compatibility
import "core-js/es6/map";
import "core-js/es6/set";

import $ from "jquery";
import React from "react";
import ReactDOM from "react-dom";

import Chrome from "../chrome/chrome";
import ContextProvider from "../react/context-provider";
import getServicesFromPage from "../services/page";

class BaseComponent extends React.Component {
  state = {
    pageRenderTime: this.props.pageRenderTime,
  };

  componentDidMount() {
    // We only want to consider the pageRenderTime on the initial page load. Once the page
    // has loaded, then any other components that join the page have no serverside attachment,
    // so they should be relative to the current time
    // eslint-disable-next-line react/no-did-mount-set-state
    this.setState({pageRenderTime: null});
  }

  render() {
    return (
      <ContextProvider
        loginState={this.props.loginState}
        services={this.props.services}
        pageRenderTime={this.state.pageRenderTime}
      >
        {this.props.children}
      </ContextProvider>
    );
  }
}

export default function renderToPage(reactComponent, unusedArg, cb) {
  getServicesFromPage(function (services) {
    const holder = $(".chrome-content").toArray()[0];
    const chromeArgs = JSON.parse($("#chrome-args").text());

    const innerComponent = <Chrome {...chromeArgs} content={reactComponent} />;
    const component = (
      <BaseComponent
        loginState={chromeArgs.loginState}
        services={services}
        pageRenderTime={chromeArgs.pageRenderTime}
      >
        {innerComponent}
      </BaseComponent>
    );
    ReactDOM.hydrate(component, holder, cb);
  });
}

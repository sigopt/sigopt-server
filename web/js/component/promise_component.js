/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Loading from "./loading";

export default (promiseFunction, WrappedComponent, options) => {
  class PromiseComponent extends React.Component {
    state = {loading: true};
    lastUpdate = null;

    componentDidMount() {
      this.refresh();
    }

    componentDidUpdate(prevProps) {
      const shouldRefresh = (options || {}).shouldRefresh || (() => false);
      if (shouldRefresh(this.props, prevProps)) {
        this.refresh();
      }
    }

    componentWillUnmount() {
      this.lastUpdate = null;
    }

    refresh() {
      const lastUpdate = {};
      this.lastUpdate = lastUpdate;
      this.setState({loading: true}, () => {
        Promise.resolve(promiseFunction(this.props)).then((data) => {
          if (this.lastUpdate === lastUpdate) {
            this.setState({data, loading: false});
          }
        });
      });
    }

    render() {
      return (
        <Loading loading={this.state.loading}>
          {this.state.loading ? null : (
            <WrappedComponent {...this.props} data={this.state.data} />
          )}
        </Loading>
      );
    }
  }
  return PromiseComponent;
};

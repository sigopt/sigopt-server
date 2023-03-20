/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

export default class HistoryTableWrapper extends React.Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
    pagingBlock: PropTypes.node.isRequired,
  };

  render() {
    const {children, pagingBlock} = this.props;
    return (
      <div className="history-table">
        {pagingBlock && <div className="paging-holder">{pagingBlock}</div>}
        <div className="table-responsive">
          <table className="table table-hover">{children}</table>
        </div>
        {pagingBlock && <div className="paging-holder">{pagingBlock}</div>}
      </div>
    );
  }
}

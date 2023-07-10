/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import PagingBlock from "./paging-block";
import PagingTable from "./paging-table";
import arrayPager from "../net/list";
import makePageable from "./make-pageable";

const pageFetcher = function (...args) {
  return arrayPager(this.props.allData || [])(...args);
};

/**
 * A simple paginated table for a list of values.
 * Renders a table that the * user can use to paginate through the list.
 * Doesn't support asynchronous data fetching, so yse this only when all the data is available immediately
 */
export default makePageable(
  pageFetcher,
  class PaginatedTable extends React.Component {
    static propTypes = {
      allData: PropTypes.arrayOf(PropTypes.object),
      data: PropTypes.arrayOf(PropTypes.object),
      head: PropTypes.node,
      makeRow: PropTypes.func.isRequired,
      reloadPages: PropTypes.func.isRequired,
    };

    componentDidUpdate(prevProps) {
      if (!_.isEqual(prevProps.allData, this.props.allData)) {
        this.props.reloadPages();
      }
    }

    render() {
      const passProps = _.omit(this.props, "head", "allData", "makeRow");
      return (
        <div className="table-responsive">
          <PagingTable className="table" head={this.props.head} {...passProps}>
            {_.map(this.props.data, (item) => this.props.makeRow(item))}
          </PagingTable>
          <div>
            <PagingBlock {...passProps} />
          </div>
        </div>
      );
    }
  },
);

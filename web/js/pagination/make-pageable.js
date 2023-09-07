/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import {NUM_PAGES_EACH_SIDE, calculateEllipsisFlags} from "./paging-block";
import {coalesce, isDefinedAndNotNull} from "../utils";

/**
 * A Higher-Order component for providing Pagination to a component.
 *
 * The most common usage will look like
 *
 * const PagedTable = makePageable(fetcher, class extends React.Component {
 *   render() {
 *     return [
 *       <PagingBlock {...this.props}>,  // Renders as a paging control
 *       <PagingTable {...this.props}>
 *         {_.map(this.props.data, (item) =>
 *           <tr>
 *             // Custom rendering for each paginated item goes here
 *           </tr>)}
 *       </PagingTable>
 *     ];
 *   }
 * })
 *
 * fetcher will be a function taking (params, success, error) that can be successively
 * paged through to provide the pages for the table. It will be called with `this` bound
 * to the Pageable component, so it will be able to access its props and state.
 *
 * The HOC provides the following props to the WrappedComponent:
 *   data: An array of items to be rendered on this page.
 *   isEmpty: A boolean indicating that there is no data to be displayed.
 *     Allows the WrappedComponent to show an empty state if desired.
 *   navigateToPage: A function the WrappedComponent can call to navigate to a specific page.
 *   numPages: How many pages are available in total to be rendered
 *   pageNumber: The current page number, 0-indexed
 *   refreshPage: A function the WrappedComponent can call to reload the data on the current page
 *   reloadPages: A function the WrappedComponent can call to reload all page data.
 *     Accepts a pageNumber to start from
 *
 * These props are also provided, though they are likely only needed by the subcomponents
 *   emptyState: A custom table body to render when there is no content to display
 *   hasNextPage: A boolean indicating if the next page is available
 *   hasPreviousPage: A boolean indicating if the previous page is available
 *   increment: 1 if we are loading data forwards, -1 if backwards
 *   isPaging: A boolean indicating if pages are still being loaded
 *   reverse: Called to reverse the direction of paging
 */
export default function makePageable(pageFetcher, WrappedComponent) {
  return class PageableComponent extends React.Component {
    static defaultProps = WrappedComponent.defaultProps;
    static displayName = `Pageable(${WrappedComponent.displayName})`;

    constructor(props, context) {
      super(props, context);
      this.state = this._initialPagingState(this.props.startPage);
      this._pageFetcher = pageFetcher;
      this._instanceRef = React.createRef();
    }

    componentDidMount() {
      this._isMounted = true;
      this._reloadPages(this.props.startPage);
    }

    componentWillUnmount() {
      this._isMounted = false;
    }

    getInstance = () => this._instanceRef.current;

    _initialPagingState = (startPage = 0) => ({
      after: null,
      before: null,
      farthestPage: null,
      increment: 1,
      isPaging: true,
      numPages: 0,
      numResults: null,
      page: coalesce(startPage, 0),
      pageData: {},
      // Set a unique random value whenever we "reset" the paging. This way if there are any
      // outstanding requests they can check the paging nonce when they asynchronously return.
      // If the nonce has changed then the callback knows it is out of date and can be discarded.
      pagingNonce: Math.random(),
    });

    _setSortAscending = (sortAscending) =>
      this.setState({sortAscending}, this._reloadPages);
    _getPageWithBefore = () =>
      (this.state.sortAscending && this.state.increment === -1) ||
      (!this.state.sortAscending && this.state.increment === 1);
    _getAscending = () =>
      (this.state.sortAscending && this.state.increment === 1) ||
      (!this.state.sortAscending && this.state.increment === -1);

    _pageUpdated = (urlParams, changeHistory) => {
      if (isDefinedAndNotNull(this.props.pageUpdated)) {
        this.props.pageUpdated(urlParams, changeHistory);
      }
    };

    _reloadPages = (startPage) => {
      const page = coalesce(startPage, 0);
      const lastSeenPage =
        this.state.pageData && this.state.pageData[this.state.page];
      const resetState = _.extend(this._initialPagingState(page), {
        lastSeenPage: lastSeenPage,
      });
      this.setState(resetState, this._kickPaging);
    };

    _refreshPage = () => {
      const lastSeenPage =
        this.state.pageData && this.state.pageData[this.state.page];
      const resetState = _.extend(this._initialPagingState(0), {
        lastSeenPage: lastSeenPage,
        page: this.state.page,
      });
      this.setState(resetState, this._kickPaging);
    };

    refreshPage = this._refreshPage;

    _kickPaging = () => this._makePageKicker(this.state.pagingNonce)();

    _makePageKicker = (nonce) => () => {
      if (this.state.isPaging && nonce === this.state.pagingNonce) {
        const numItemsLoaded = Object.keys(this.state.pageData).length;
        const pageToFill =
          this.state.increment === 1
            ? numItemsLoaded
            : this.state.numPages - 1 - numItemsLoaded;

        // NOTE: Logic for continuing depends on whether increment is 1 or -1
        const continueKicking =
          this.state.increment === 1
            ? pageToFill <= this.state.farthestPage
            : pageToFill >= this.state.farthestPage;
        if (!this.state.farthestPage || continueKicking) {
          this._fillPage(pageToFill);
        }
      }
    };

    _fillPage = (index) => {
      const pageWithBefore = this._getPageWithBefore();
      const paging = pageWithBefore
        ? {before: this.state.before}
        : {after: this.state.after};

      const prevNonce = this.state.pagingNonce;

      // NOTE: If paging in reverse, need to set a limit on the results when we request the
      // last page to maintain the correct number of results on the last page
      const normalPageSize = this.props.pageSize || 20;
      const limitPageSize =
        this.state.increment === -1 &&
        index === this.state.numPages - 1 &&
        this.state.numResults % normalPageSize !== 0;

      const pageSize = limitPageSize
        ? this.state.numResults % normalPageSize
        : normalPageSize;

      this._pageFetcher.call(
        this.getInstance(),
        _.extend(paging, {
          limit: pageSize,
          ascending: this._getAscending(),
        }),
        (response) => this._receivePage(paging, response, index, prevNonce),
      );
    };

    _receivePage = (paging, response, index, prevNonce) => {
      if (
        this._isMounted &&
        this.state.pagingNonce === prevNonce &&
        !this.state.pageData[index]
      ) {
        const kicker = this._makePageKicker(this.state.pagingNonce);
        const pageSize = this.props.pageSize || 20;

        this.setState(function (prevState) {
          prevState.pageData[index] =
            prevState.increment === 1
              ? response.data
              : response.data.reverse() || [];
          prevState.after = response.paging.after;
          prevState.before = response.paging.before;
          prevState.numPages = Math.ceil(response.count / pageSize);

          // Catch the case when the url param page is greater than the number of pages
          if (prevState.numPages >= 0 && prevState.page >= prevState.numPages) {
            prevState.page = 0;
            // Update url params
            this._pageUpdated(
              {
                page: 0,
              },
              false,
            );
          }

          prevState.numResults = response.count;
          const pageWithBefore = this._getPageWithBefore();
          prevState.isPaging = Boolean(
            pageWithBefore ? prevState.before : prevState.after,
          );

          prevState.farthestPage = this._calculateFarthestPage(
            prevState.page,
            prevState.numPages,
            prevState.increment,
          );

          return prevState;
        }, kicker);
      }
    };

    _navigateToPage = (pageNumber, changeHistory = true) => {
      this.setState(
        (prevState) => ({
          page: pageNumber,
          farthestPage: this._calculateFarthestPage(
            pageNumber,
            prevState.numPages,
            prevState.increment,
          ),
        }),
        () => {
          this._kickPaging();
          this._pageUpdated(
            {
              page: pageNumber,
            },
            changeHistory,
          );
        },
      );
    };

    _isEmpty = () =>
      _.reduce(
        _.map(this.state.pageData, (data) => (data || []).length),
        (a, b) => a + b,
        0,
      ) === 0;

    _calculateFarthestPage = (pageIndex, numPages, increment) => {
      // TODO: Why are we calculating the ellipsis in two pages?
      const [showFirstEllipsis, showSecondEllipsis] = calculateEllipsisFlags(
        numPages,
        pageIndex,
      );

      if (showFirstEllipsis && showSecondEllipsis) {
        return pageIndex + increment;
      } else if (showFirstEllipsis) {
        return increment === 1
          ? numPages - 1
          : numPages - 1 - NUM_PAGES_EACH_SIDE - 1;
      } else if (showSecondEllipsis) {
        return increment === 1 ? NUM_PAGES_EACH_SIDE + 1 : 0;
      } else {
        return increment === 1 ? numPages - 1 : 0;
      }
    };

    // If the pagination control shows 1...5 6 7...9, reverse() is called when the user clicks 9.
    // reverse() causes us to start paginating from the opposite direction, and is necessary since we
    // want to allow the user to access the last page before the user has paged to it.
    _reverse = () => {
      this.setState(
        (prevState) => {
          const lastSeenPage =
            prevState.pageData && prevState.pageData[prevState.page];
          const newIncrement = -prevState.increment;
          const newPage = newIncrement === 1 ? 0 : prevState.numPages - 1;
          const farthestPage = this._calculateFarthestPage(
            newPage,
            prevState.numPages,
            newIncrement,
          );

          return _.extend(this._initialPagingState(0), {
            lastSeenPage: lastSeenPage,
            increment: newIncrement,
            page: newPage,
            numPages: prevState.numPages,
            farthestPage: farthestPage,
            numResults: prevState.numResults,
          });
        },
        () => {
          this._kickPaging();
          this._pageUpdated(
            {
              page: this.state.page,
            },
            true,
          );
        },
      );
    };

    render() {
      const hasPreviousPage = Boolean(
        this.state.pageData[this.state.page] &&
          this.state.pageData[this.state.page - 1],
      );
      const hasNextPage = Boolean(
        this.state.pageData[this.state.page] &&
          this.state.pageData[this.state.page + 1],
      );

      return (
        <WrappedComponent
          ref={this._instanceRef}
          data={this.state.pageData[this.state.page]}
          emptyState={this.props.emptyState}
          hasNextPage={hasNextPage}
          hasPreviousPage={hasPreviousPage}
          increment={this.state.increment}
          isEmpty={!this.state.isPaging && this._isEmpty()}
          isPaging={this.state.isPaging}
          navigateToPage={this._navigateToPage}
          numPages={this.state.numPages}
          pageNumber={this.state.page}
          refreshPage={this._refreshPage}
          reloadPages={this._reloadPages}
          reverse={this._reverse}
          setSortAscending={this._setSortAscending}
          sortAscending={this.state.sortAscending}
          {...this.props}
        />
      );
    }
  };
}

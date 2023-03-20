/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Spinner from "../component/spinner";
import {withPreventDefault} from "../utils";

export const NUM_PAGES_EACH_SIDE = 3;
export const calculateEllipsisFlags = function (numPages, currentPage) {
  const ellipsisNeeded = numPages > 2 * NUM_PAGES_EACH_SIDE + 1;
  const showFirstEllipsis = ellipsisNeeded
    ? currentPage - 0 > NUM_PAGES_EACH_SIDE
    : false;
  const showSecondEllipsis = ellipsisNeeded
    ? numPages - 1 - currentPage > NUM_PAGES_EACH_SIDE
    : false;
  return [showFirstEllipsis, showSecondEllipsis];
};

const PagingBlock = function (props) {
  const showPagingBlock = !props.isEmpty && props.numPages > 1;
  if (!showPagingBlock) {
    return null;
  }

  // We dynamically construct the pagination control based on the current page and the
  // total number of pages
  const [showFirstEllipsis, showSecondEllipsis] = calculateEllipsisFlags(
    props.numPages,
    props.pageNumber,
  );

  const spinner = (
    <li>
      <span>
        <Spinner position="relative" size={9} />
      </span>
    </li>
  );
  const stillLoadingPreviousPage =
    props.increment === -1 && !props.hasPreviousPage && props.isPaging;
  const prevButton = stillLoadingPreviousPage ? (
    spinner
  ) : (
    <li className={classNames(props.hasPreviousPage ? null : "disabled")}>
      <a
        aria-label="Previous"
        className="previous"
        onClick={
          props.hasPreviousPage
            ? withPreventDefault(() =>
                props.navigateToPage(props.pageNumber - 1),
              )
            : null
        }
      >
        <span aria-hidden="true">&#8592;</span>
      </a>
    </li>
  );
  const stillLoadingNextPage =
    props.increment === 1 && !props.hasNextPage && props.isPaging;
  const nextButton = stillLoadingNextPage ? (
    spinner
  ) : (
    <li className={classNames(props.hasNextPage ? null : "disabled")}>
      <a
        aria-label="Next"
        className="next"
        onClick={
          props.hasNextPage
            ? withPreventDefault(() =>
                props.navigateToPage(props.pageNumber + 1),
              )
            : null
        }
      >
        <span aria-hidden="true">&#8594;</span>
      </a>
    </li>
  );
  const firstButton = (
    <li className={props.pageNumber === 0 ? "active" : ""}>
      <a
        onClick={
          props.increment === 1 ? () => props.navigateToPage(0) : props.reverse
        }
      >
        1
      </a>
    </li>
  );
  const lastButton = (
    <li className={props.pageNumber === props.numPages - 1 ? "active" : ""}>
      <a
        onClick={
          props.increment === 1
            ? props.reverse
            : () => props.navigateToPage(props.numPages - 1)
        }
      >
        {props.numPages}
      </a>
    </li>
  );
  const firstEllipsisButton = (
    <li className="disabled">
      <a>...</a>
    </li>
  );
  const secondEllipsisButton = (
    <li className="disabled">
      <a>...</a>
    </li>
  );

  let interiorPagesStartIndex = null;
  let numInteriorButtons = null;

  if (showFirstEllipsis && showSecondEllipsis) {
    interiorPagesStartIndex = props.pageNumber - 1;
    numInteriorButtons = 3;
  } else if (showFirstEllipsis) {
    interiorPagesStartIndex = props.numPages - 1 - NUM_PAGES_EACH_SIDE - 1;
    numInteriorButtons = NUM_PAGES_EACH_SIDE + 1;
  } else if (showSecondEllipsis) {
    interiorPagesStartIndex = 1;
    numInteriorButtons = NUM_PAGES_EACH_SIDE + 1;
  } else {
    interiorPagesStartIndex = 0;
    numInteriorButtons = props.numPages;
  }

  const interiorButtons = _.map(
    _.range(
      interiorPagesStartIndex,
      interiorPagesStartIndex + numInteriorButtons,
    ),
    function (num) {
      return (
        <li
          key={`interior-page-${num}`}
          className={props.pageNumber === num ? "active" : ""}
        >
          <a onClick={() => props.navigateToPage(num)}>{num + 1}</a>
        </li>
      );
    },
  );

  const showFirstLastButton = showFirstEllipsis || showSecondEllipsis;

  return (
    <div className="paging-block">
      <ul className="pagination">
        {prevButton}
        {showFirstLastButton && firstButton}
        {showFirstEllipsis && firstEllipsisButton}
        {interiorButtons}
        {showSecondEllipsis && secondEllipsisButton}
        {showFirstLastButton && lastButton}
        {nextButton}
      </ul>
    </div>
  );
};

PagingBlock.propTypes = {
  hasNextPage: PropTypes.bool.isRequired,
  hasPreviousPage: PropTypes.bool.isRequired,
  increment: PropTypes.number.isRequired,
  isEmpty: PropTypes.bool.isRequired,
  isPaging: PropTypes.bool.isRequired,
  navigateToPage: PropTypes.func.isRequired,
  numPages: PropTypes.number.isRequired,
  pageNumber: PropTypes.number.isRequired,
  reverse: PropTypes.func.isRequired,
};

export default PagingBlock;

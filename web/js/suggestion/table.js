/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import HistoryTableHead from "../experiment/history/head";
import HistoryTableRow from "../experiment/history/row";
import HistoryTableWrapper from "../experiment/history/table_wrapper";
import PagingBlock from "../pagination/paging-block";
import PagingTableContents from "../pagination/paging-table-contents";
import arrayPager from "../net/list";
import byNaturalSortName from "../experiment/sort_params";
import makePageable from "../pagination/make-pageable";
import schemas from "../react/schemas";

class SuggestionTableRow extends React.Component {
  onClick = () => this.props.onSelectSuggestion(this.props.suggestion);

  render() {
    const {assignments, created, task} = this.props.suggestion;
    return (
      <HistoryTableRow
        {...this.props}
        assignments={assignments}
        canEdit={true}
        conditionals={this.props.conditionals}
        created={created}
        onClick={this.onClick}
        parameters={this.props.parameters}
        resource={this.props.suggestion}
        showValues={false}
        taskCost={task ? task.cost : null}
      />
    );
  }
}

const pageFetcher = function (...args) {
  return arrayPager(this.props.suggestions || [])(...args);
};

export default makePageable(
  pageFetcher,
  class SuggestionTable extends React.Component {
    static propTypes = {
      canEdit: PropTypes.bool,
      data: PropTypes.arrayOf(
        PropTypes.oneOfType([schemas.QueuedSuggestion, schemas.Suggestion]),
      ),
      experiment: schemas.Experiment.isRequired,
      onChange: PropTypes.func,
      onSelectSuggestion: PropTypes.func,
      pageSize: PropTypes.number,
      refreshPage: PropTypes.func.isRequired,
      suggestions: PropTypes.arrayOf(
        PropTypes.oneOfType([schemas.QueuedSuggestion, schemas.Suggestion]),
      ).isRequired,
    };

    static defaultProps = {
      onChange: _.noop,
      onSelectSuggestion: _.noop,
      pageSize: 10,
    };

    componentDidUpdate(prevProps) {
      if (this.props.suggestions !== prevProps.suggestions) {
        this.props.refreshPage();
      }
    }

    render() {
      const conditionals = _.clone(
        this.props.experiment.conditionals || [],
      ).sort(byNaturalSortName);
      const parameters = _.clone(this.props.experiment.parameters || []).sort(
        byNaturalSortName,
      );

      return (
        <HistoryTableWrapper pagingBlock={<PagingBlock {...this.props} />}>
          <PagingTableContents
            data={this.props.data}
            head={
              <HistoryTableHead
                experiment={this.props.experiment}
                canEdit={true}
                conditionals={conditionals}
                expectingMoreCheckpoints={true}
                showMetrics={false}
                parameters={parameters}
              />
            }
            {...this.props}
          >
            {_.map(this.props.data, (suggestion) => (
              <SuggestionTableRow
                conditionals={conditionals}
                key={suggestion.id}
                onSelectSuggestion={this.props.onSelectSuggestion}
                parameters={parameters}
                suggestion={suggestion}
                {...this.props}
              />
            ))}
          </PagingTableContents>
        </HistoryTableWrapper>
      );
    }
  },
);

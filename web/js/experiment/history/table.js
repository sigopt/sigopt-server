/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../../react/component";
import HistoryTableHead from "./head";
import HistoryTableRow from "./row";
import HistoryTableWrapper from "./table_wrapper";
import ObservationModal from "../observation_modal";
import PagingBlock from "../../pagination/paging-block";
import PagingTableContents from "../../pagination/paging-table-contents";
import byNaturalSortName from "../sort_params";
import makePageable from "../../pagination/make-pageable";
import schemas from "../../react/schemas";

const pageFetcher = function (paging, success, error) {
  this.services.promiseApiClient
    .experiments(this.props.experiment.id)
    .observations()
    .fetch(_.extend(paging, {sort: this.state.sortKey}))
    .then(success, error);
};

const HistoryTable = makePageable(
  pageFetcher,
  class HistoryTable extends Component {
    static propTypes = {
      canEdit: PropTypes.bool.isRequired,
      data: PropTypes.arrayOf(schemas.Observation),
      emptyState: PropTypes.node,
      experiment: schemas.Experiment.isRequired,
      pageSize: PropTypes.number,
      refreshPage: PropTypes.func.isRequired,
      reloadPages: PropTypes.func.isRequired,
      setSortAscending: PropTypes.func.isRequired,
      sortAscending: PropTypes.bool,
    };

    static defaultProps = {
      emptyState: <p>No data has been reported for this experiment.</p>,
      pageSize: 10,
    };

    constructor(...args) {
      super(...args);
      this.state = {
        sortKey: "id",
        submitting: false,
      };
      this._observationModal = React.createRef();
    }

    componentDidUpdate(prevProps, prevState) {
      if (this.state.sortKey !== prevState.sortKey) {
        this.props.reloadPages();
      }
    }

    detachObservation = () => {
      this.props.refreshPage();
    };

    onSort = (sortKey, sortAscending) => {
      this.props.setSortAscending(sortAscending);
      this.setState({sortKey: sortKey});
    };

    onClickRow = (observation) =>
      this._observationModal.current.show(observation);

    render() {
      const conditionals = _.clone(
        this.props.experiment.conditionals || [],
      ).sort(byNaturalSortName);
      const parameters = _.clone(this.props.experiment.parameters || []).sort(
        byNaturalSortName,
      );
      return (
        <>
          <ObservationModal
            canEdit={this.props.canEdit}
            experiment={this.props.experiment}
            onObservationDeleted={this.props.refreshPage}
            onObservationUpdated={this.props.refreshPage}
            ref={this._observationModal}
          />
          <HistoryTableWrapper pagingBlock={<PagingBlock {...this.props} />}>
            <PagingTableContents
              head={
                <HistoryTableHead
                  experiment={this.props.experiment}
                  canEdit={this.props.canEdit}
                  conditionals={conditionals}
                  expectingMoreCheckpoints={false}
                  onSort={this.onSort}
                  parameters={parameters}
                  sortAscending={this.props.sortAscending}
                  sortKey={this.state.sortKey}
                />
              }
              {...this.props}
            >
              {_.map(this.props.data, (observation) => (
                <HistoryTableRow
                  {...this.props}
                  assignments={observation.assignments}
                  conditionals={conditionals}
                  created={observation.created}
                  detachObservation={this.detachObservation}
                  failed={observation.failed}
                  key={observation.id}
                  onClick={this.onClickRow}
                  parameters={parameters}
                  resource={observation}
                  showValues={true}
                  values={observation.values}
                  taskCost={observation.task && observation.task.cost}
                />
              ))}
            </PagingTableContents>
          </HistoryTableWrapper>
        </>
      );
    }
  },
);

export default HistoryTable;

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/experiment/experiment.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ExperimentOverviewTileHeader from "./experiment_overview_tile_header";
import ExperimentPage from "../page_wrapper";
import PageBody from "../../../component/page_body";
import StreamingPager from "../../../net/streaming_pager";
import schemas from "../../../react/schemas";
import ui from "../../../experiment/ui";
import {
  ButtonTile,
  ChicletInfoTile,
  ListInfoTile,
  TextListTile,
} from "../../../component/tiles";

class ExperimentAdminPage extends React.Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    canEdit: PropTypes.bool.isRequired,
    client: schemas.Client.isRequired,
    experiment: schemas.Experiment.isRequired,
    organization: schemas.Organization.isRequired,
    promiseApiClient: PropTypes.object.isRequired,
    user: schemas.User,
  };

  constructor(props) {
    super(props);
    const emptyState = () => ({
      loading: true,
      data: [],
      count: 0,
      error: false,
    });

    const state = {
      bestPractices: {
        loading: true,
        violations: [],
        error: false,
      },
    };
    _.each(
      [
        "observations",
        "suggestions",
        "deletedObservations",
        "deletedSuggestions",
      ],
      (k) => (state[k] = emptyState()),
    );
    this.state = state;
  }

  componentDidMount() {
    const success = (key, response, skipLoad = false) => {
      this.setState((prevState) => {
        let data = prevState[key].data ? prevState[key].data : [];
        data = data.concat(response.data);
        return {
          [key]: {
            data: data,
            loading: !skipLoad,
            count: response.count,
          },
        };
      });
    };

    const finish = (key) => {
      this.setState((prevState) => ({
        [key]: _.extend({}, prevState[key], {loading: false}),
      }));
    };

    const error = (key) => {
      this.setState((prevState) => ({
        [key]: {
          loading: false,
          error: true,
          data: prevState[key].data,
          count: prevState[key].count,
        },
      }));
    };

    const createPager = (resource, fields) =>
      new StreamingPager(
        (params) =>
          this.props.promiseApiClient
            .experiments(this.props.experiment.id)
            [resource]()
            .fetch(params),
        _.partial(success, resource),
        _.partial(finish, resource),
        _.partial(error, resource),
        {fields},
      );

    this.pagers = [
      (this.observationPager = createPager(
        "observations",
        "failed,suggestion",
      )),
      (this.suggestionPager = createPager("suggestions", "id,state")),
    ];
    _.each(this.pagers, (pager) => pager.start());

    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .observations()
      .fetch({deleted: true, limit: 0})
      .then(
        _.partial(success, "deletedObservations", _, true),
        _.partial(error, "deletedObservations"),
      );
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .suggestions()
      .fetch({deleted: true, limit: 0})
      .then(
        _.partial(success, "deletedSuggestions", _, true),
        _.partial(error, "deletedSuggestions"),
      );

    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .bestPractices()
      .fetch()
      .then(
        (response) =>
          this.setState({
            bestPractices: {loading: false, violations: response.violations},
          }),
        () => this.setState({bestPractices: {loading: false, error: true}}),
      );
  }

  componentWillUnmount() {
    _.each(this.pagers, (pager) => pager.stop());
  }

  onUpdateParamImportancesClick = () => {
    const success = () =>
      this.props.alertBroker.show(
        "Successfully enqueued importances calculation.",
        "success",
      );
    const error = (e) => this.props.alertBroker.show(`API Error: ${e.message}`);
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .metricImportances()
      .update()
      .then(success, error);
  };

  onResetHyperparametersClick = () => {
    const success = () =>
      this.props.alertBroker.show(
        "Successfully reset hyperparameters.",
        "success",
      );
    const error = (e) => this.props.alertBroker.show(`API Error: ${e.message}`);
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .hyperparameters()
      .delete()
      .then(success, error);
  };

  render() {
    const client = this.props.client;
    const organization = this.props.organization;
    const user = this.props.user;
    const observations = this.state.observations;
    const suggestions = this.state.suggestions;
    const deletedObservations = this.state.deletedObservations;
    const deletedSuggestions = this.state.deletedSuggestions;
    const canEdit = this.props.canEdit;

    const suggestionsById = _.indexBy(suggestions.data, "id");
    const openSuggestions = _.countBy(
      suggestions.data,
      (s) => s.state === "open",
    ).true;
    const experiment = this.props.experiment;

    const parameters = _.countBy(experiment.parameters, (p) => p.type);
    const manualObservations = _.countBy(observations.data, (o) =>
      _.has(suggestionsById, o.suggestion),
    ).false;
    const failedObservations = _.countBy(
      observations.data,
      (o) => o.failed,
    ).true;

    const conditionalsBreadth = _.chain(experiment.conditionals)
      .map((c) => c.values.length)
      .reduce((a, b) => a + b, 0)
      .value();

    const importanceCalculationsDisabled =
      experiment.parameters.length <= 1 ||
      experiment.conditionals.length > 0 ||
      experiment.development;

    const numViolations = this.state.bestPractices.violations.length;

    const overviewHeader = (
      <ExperimentOverviewTileHeader
        experiment={experiment}
        client={client}
        organization={organization}
        user={user}
      />
    );

    return (
      <ExperimentPage
        {...this.props}
        className="experiment-history-page logged-in-page"
      >
        <div className="admin-experiment-page logged-in-page">
          <PageBody>
            <div className="experiment-info-tiles">
              <div className="row">
                <ChicletInfoTile
                  header={overviewHeader}
                  info={[
                    [experiment.parameters.length, "Parameters"],
                    [observations.count, "Observations"],
                  ]}
                  loading={observations.loading || suggestions.loading}
                  error={observations.error || suggestions.error}
                  tileClass="experiment-overview-tile"
                />
              </div>
              <div className="row">
                <ChicletInfoTile
                  header={`${experiment.parameters.length} Parameters`}
                  href={ui.getExperimentUrl(experiment, "/properties")}
                  info={[
                    [parameters.categorical || 0, "Categorical"],
                    [parameters.double || 0, "Double"],
                    [parameters.int || 0, "Integer"],
                  ]}
                  loading={false}
                  error={false}
                />
                <ChicletInfoTile
                  header={`${observations.count} Observations`}
                  href={ui.getExperimentUrl(experiment, "/history")}
                  info={[
                    [failedObservations || 0, "Failed"],
                    [manualObservations || 0, "Manual"],
                    [deletedObservations.count || 0, "Deleted"],
                  ]}
                  loading={
                    observations.loading ||
                    suggestions.loading ||
                    deletedObservations.loading
                  }
                  error={
                    observations.error ||
                    suggestions.error ||
                    deletedObservations.error
                  }
                  tooltip="Total count does not include deleted Observations"
                />
                <ChicletInfoTile
                  header={`${suggestions.count} Suggestions`}
                  href={
                    ui.isAiExperiment(experiment)
                      ? null
                      : `/experiment/${experiment.id}/suggestions`
                  }
                  info={[
                    [openSuggestions || 0, "Open"],
                    [deletedSuggestions.count || 0, "Deleted"],
                  ]}
                  loading={suggestions.loading || deletedSuggestions.loading}
                  error={suggestions.error || deletedSuggestions.error}
                  tooltip={
                    <>
                      Total count does not include deleted Suggestions.
                      {ui.isAiExperiment(experiment)
                        ? " This is an AI Experiment so you will not be able to access the Experiment Suggestions page."
                        : null}
                    </>
                  }
                />
                <ListInfoTile
                  header="Miscellaneous"
                  info={[
                    [
                      experiment.observation_budget ||
                        experiment.budget ||
                        "N/A",
                      "Observation Budget",
                    ],
                    [
                      ui.optimizedMetrics(experiment).length,
                      "Optimized Metrics",
                    ],
                    [ui.storedMetrics(experiment).length, "Stored Metrics"],
                    [
                      ui.constrainedMetrics(experiment).length,
                      "Constraint Metrics",
                    ],
                    [
                      experiment.linear_constraints.length,
                      "Linear Constraints",
                    ],
                    [conditionalsBreadth, "Conditionals Breadth"],
                  ]}
                  loading={false}
                  error={false}
                />
                {canEdit ? (
                  <div>
                    <ButtonTile
                      header="Trigger Importances Calculations"
                      info={{
                        buttonText: "Update importances",
                        onClick: this.onUpdateParamImportancesClick,
                        disabled: importanceCalculationsDisabled,
                      }}
                      loading={false}
                      error={false}
                      tooltip="Triggers a new job to calculate experiment parameter importances.
                    Not supported on conditional or development experiments.
                    Experiment must also have more than one parameter."
                    />
                    <ButtonTile
                      header="Trigger Hyperparameter Reset"
                      info={{
                        buttonText: "Reset hyperparameters",
                        onClick: this.onResetHyperparametersClick,
                      }}
                      loading={false}
                      error={false}
                      tooltip="Resets the current hyperparameters."
                    />
                  </div>
                ) : null}
                <TextListTile
                  header="Best Practices Violations"
                  info={
                    numViolations > 0
                      ? this.state.bestPractices.violations
                      : ["No Violations Detected"]
                  }
                  loading={this.state.bestPractices.loading}
                  error={this.state.bestPractices.error}
                />
              </div>
            </div>
          </PageBody>
        </div>
      </ExperimentPage>
    );
  }
}

export default ExperimentAdminPage;

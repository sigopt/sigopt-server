/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/suggestions.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ExperimentPage from "../../page_wrapper";
import GenerateSuggestionButton from "../../../../suggestion/generate_suggestion_button";
import Loading from "../../../../component/loading";
import Poller from "../../../../net/poller";
import QueuedSuggestionModal from "../../../../queued_suggestion/modal";
import SuggestionModal from "../../../../suggestion/modal";
import SuggestionTable from "../../../../suggestion/table";
import Tooltip from "../../../../component/tooltip";
import makeSubmittableComponent from "../../../../component/make-submittable";
import schemas from "../../../../react/schemas";
import ui from "../../../../experiment/ui";
import {DOCS_URL} from "../../../../net/constant";
import {ExperimentStates} from "../../../../experiment/constants";
import {exhaustivelyPage} from "../../../../net/paging";

const SubmittableSuggestionPage = makeSubmittableComponent(
  class SuggestionPage extends React.Component {
    static propTypes = {
      alertBroker: schemas.AlertBroker.isRequired,
      canEdit: PropTypes.bool.isRequired,
      experiment: schemas.Experiment.isRequired,
      isGuest: PropTypes.bool.isRequired,
      legacyApiClient: schemas.LegacyApiClient.isRequired,
      submit: PropTypes.func.isRequired,
      submitting: PropTypes.bool,
    };

    constructor(...args) {
      super(...args);
      this.state = {
        experiment: this.props.experiment,
        suggestions: null,
        queuedSuggestions: null,
      };
      this._suggestionTable = React.createRef();
      this._suggestionModal = React.createRef();
      this._queuedSuggestionModal = React.createRef();
    }

    componentDidMount() {
      if (this.state.experiment.state !== ExperimentStates.DELETED) {
        const waitTime = 30000;
        this.experimentPoller = new Poller({
          poll: (success, error) =>
            this.props.legacyApiClient.experimentDetail(
              this.state.experiment.id,
              success,
              error,
            ),
          onChange: (experiment) => this.setState({experiment: experiment}),
          waitTime: waitTime,
        }).startOnce();

        this.suggestionPoller = new Poller({
          poll: (success, error) =>
            exhaustivelyPage(
              _.partial(
                this.props.legacyApiClient.experimentSuggestions,
                this.state.experiment.id,
              ),
              {
                success: success,
                error: error,
                params: {state: "open"},
              },
            ),
          onChange: (suggestions) => this.setState({suggestions: suggestions}),
          waitTime: waitTime,
        }).startOnce();

        this.queuedSuggestionPoller = new Poller({
          poll: (success, error) =>
            exhaustivelyPage(
              _.partial(
                this.props.legacyApiClient.queuedSuggestionsListDetail,
                this.state.experiment.id,
              ),
              {success: success, error: error},
            ),
          onChange: (queuedSuggestions) =>
            this.setState({queuedSuggestions: queuedSuggestions}),
          waitTime: waitTime,
        }).startOnce();
      }
    }

    componentWillUnmount() {
      this.experimentPoller.stop();
      this.suggestionPoller.stop();
      this.queuedSuggestionPoller.stop();
    }

    _addSuggestion = (suggestion) => {
      this.setState((previousState) => ({
        suggestions: [suggestion].concat(
          _.reject(previousState.suggestions, (s) => s.id === suggestion.id),
        ),
      }));
    };

    _removeSuggestion = (suggestion) => {
      this.setState((previousState) => ({
        suggestions: _.reject(
          previousState.suggestions,
          (s) => s.id === suggestion.id,
        ),
      }));
    };

    createSuggestion = (success, error) => {
      this.props.submit(
        _.bind(
          this.props.legacyApiClient.suggestionsCreate,
          this,
          this.state.experiment.id,
          {},
        ),
        success,
        error,
      );
    };

    onCreateSuggestion = (suggestion) => {
      this._addSuggestion(suggestion);
      if (!_.isEmpty(this.state.queuedSuggestions)) {
        this._removeQueuedSuggestion(this.state.queuedSuggestions[0]);
      }
      this.props.alertBroker.show(
        "Successfully created a Suggestion",
        "success",
      );
    };

    _addQueuedSuggestion = (queuedSuggestion) => {
      this.setState((previousState) => ({
        queuedSuggestions: _.reject(
          previousState.queuedSuggestions,
          (s) => s.id === queuedSuggestion.id,
        ).concat(queuedSuggestion),
      }));
    };

    _removeQueuedSuggestion = (queuedSuggestion) => {
      this.setState((previousState) => ({
        queuedSuggestions: _.reject(
          previousState.queuedSuggestions,
          (s) => s.id === queuedSuggestion.id,
        ),
      }));
    };

    onDeleteQueuedSuggestion = (queuedSuggestion) => {
      this._removeQueuedSuggestion(queuedSuggestion);
      this.props.alertBroker.info(
        `Deleted Queued Suggestion ${queuedSuggestion.id}`,
      );
    };

    // TODO(SN-1163): think about marking as "closed" instead of removing
    onCreateObservation = (observation) => {
      this._removeSuggestion({id: observation.suggestion});
      this.props.alertBroker.show(
        `Observation reported for suggestion ${observation.suggestion}.`,
        "success",
      );
    };

    onSkip = (suggestion) => {
      this._removeSuggestion(suggestion);
      this.props.alertBroker.show(
        `Suggestion ${suggestion.id} successfully skipped.`,
        "info",
      );
    };

    render() {
      const showParallelBandwidthAlert =
        !this.state.experiment.parallel_bandwidth &&
        _.size(this.state.suggestions) > 1;
      const parallelBandwidthAlert = (
        <div className="row parallel-bandwidth-warning">
          <div className="alert alert-warning">
            This experiment has multiple open suggestions but no{" "}
            <a href={`${DOCS_URL}/advanced_experimentation/parallelism`}>
              parallel bandwidth
            </a>
            . You can set the parallel bandwidth of this experiment via{" "}
            <a href={ui.getExperimentUrl(this.state.experiment, "/properties")}>
              the properties page
            </a>
            {""}.
          </div>
        </div>
      );

      if (this.state.experiment.state === ExperimentStates.DELETED) {
        return null;
      }
      const modals = (
        <>
          <SuggestionModal
            canEdit={this.props.canEdit}
            experiment={this.props.experiment}
            onSuggestionDeleted={(s) => this._removeSuggestion(s)}
            onObservationCreated={(o) => this.onCreateObservation(o)}
            ref={this._suggestionModal}
          />
          <QueuedSuggestionModal
            canEdit={this.props.canEdit}
            experiment={this.props.experiment}
            onQueuedSuggestionCreated={(qs) => this._addQueuedSuggestion(qs)}
            onQueuedSuggestionDeleted={(qs) => this._removeQueuedSuggestion(qs)}
            ref={this._queuedSuggestionModal}
          />
        </>
      );
      if (this.props.isGuest || !this.props.canEdit) {
        return (
          <div>
            {modals}
            <h2>Suggestions</h2>
            <Loading
              loading={!this.state.suggestions}
              empty={_.isEmpty(this.state.suggestions)}
            >
              <SuggestionTable
                {...this.props}
                experiment={this.state.experiment}
                onSelectSuggestion={(s) =>
                  this._suggestionModal.current.show(s)
                }
                suggestions={this.state.suggestions || []}
              />
            </Loading>
          </div>
        );
      } else {
        return (
          <div>
            {modals}
            {showParallelBandwidthAlert && parallelBandwidthAlert}
            <div className="suggestion-section">
              <div>
                <h2>Suggestions</h2>
                <Loading
                  loading={!this.state.suggestions}
                  empty={_.isEmpty(this.state.suggestions)}
                >
                  <SuggestionTable
                    {...this.props}
                    experiment={this.state.experiment}
                    onSelectSuggestion={(s) =>
                      this._suggestionModal.current.show(s)
                    }
                    onSkip={(s) => this.onSkip(s)}
                    ref={this._suggestionTable}
                    suggestions={this.state.suggestions || []}
                  />
                </Loading>
              </div>
              <GenerateSuggestionButton
                {...this.props}
                className="btn btn-sm btn-primary suggestion-button"
                createSuggestion={(success, error) =>
                  this.createSuggestion(success, error)
                }
                disabled={this.props.submitting}
                error={this.props.alertBroker.errorHandlerThatExpectsStatus(
                  400,
                  403,
                )}
                onCreate={(suggestion) => this.onCreateSuggestion(suggestion)}
              >
                Generate Suggestion
              </GenerateSuggestionButton>
            </div>
            <div className="queued-suggestion-section">
              <div>
                <h2>
                  <Tooltip
                    tooltip={
                      "One Queued Suggestion will automatically become an Open Suggestion each time you create a" +
                      " suggestion via the API or website."
                    }
                  >
                    Queued Suggestions
                  </Tooltip>
                </h2>
                <Loading
                  loading={!this.state.queuedSuggestions}
                  empty={_.isEmpty(this.state.queuedSuggestions)}
                >
                  <SuggestionTable
                    {...this.props}
                    experiment={this.state.experiment}
                    onSelectSuggestion={(qs) =>
                      this._queuedSuggestionModal.current.show(qs)
                    }
                    suggestions={this.state.queuedSuggestions || []}
                  />
                </Loading>
              </div>
              <button
                className="btn btn-sm btn-primary queued-suggestion-button"
                onClick={() => this._queuedSuggestionModal.current.createNew()}
                type="button"
              >
                Queue Suggestion
              </button>
            </div>
          </div>
        );
      }
    }
  },
);

export default function ExperimentSuggestionsPage(props) {
  return (
    <ExperimentPage className="experiment-suggestions-page" {...props}>
      <SubmittableSuggestionPage {...props} />
    </ExperimentPage>
  );
}

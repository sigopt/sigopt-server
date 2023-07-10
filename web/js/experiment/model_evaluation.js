/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./model_evaluation.less";
import "./task_section.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Component from "../react/component";
import Loading from "../component/loading";
import RunsCheckpoints from "./runs_checkpoints";
import Tooltip from "../component/tooltip";
import schemas from "../react/schemas";
import {
  AssignmentsTableBody,
  MetadataTableBody,
  TableCard,
  TableHeader,
} from "./tables";
import {Duration, RelativeTime} from "../render/format_times";
import {MeasurementsView} from "./measurements";
import {isDefinedAndNotNull} from "../utils";

const FieldValueDisplay = ({field, value}) => (
  <div className="display-row">
    <div className="field-name">{field}</div>
    <div className="field-value">{value}</div>
  </div>
);

class MiniReport extends Component {
  static propTypes = {
    className: PropTypes.string,
    idLabel: PropTypes.string.isRequired,
    resource: PropTypes.shape({
      id: PropTypes.string.isRequired,
      created: PropTypes.number.isRequired,
    }).isRequired,
    timeLabel: PropTypes.string.isRequired,
  };

  render() {
    return (
      <div className={classNames(this.props.className, "combined-report")}>
        <FieldValueDisplay
          field={this.props.idLabel}
          value={this.props.resource.id}
        />
        <FieldValueDisplay
          field={this.props.timeLabel}
          value={<RelativeTime time={this.props.resource.created} />}
        />
      </div>
    );
  }
}

const ObservationReport = ({observation}) => (
  <MiniReport
    className="observation-report"
    idLabel="Observation ID"
    resource={observation}
    timeLabel="Reported"
  />
);

const SuggestionReport = ({suggestion, suggestionOnly}) => (
  <MiniReport
    className={classNames("suggestion-report", {
      "suggestion-only": suggestionOnly,
    })}
    idLabel={suggestionOnly ? "ID" : "Suggestion ID"}
    resource={suggestion}
    timeLabel="Created"
  />
);

class CombinedReportSection extends Component {
  static propTypes = {
    observation: schemas.Observation,
    suggestion: schemas.Suggestion,
  };

  render() {
    const observation = this.props.observation;
    const suggestion = this.props.suggestion;
    const className = classNames("report-section", {
      "multi-report": observation && observation.suggestion,
    });

    return (
      <div className={className}>
        {observation.suggestion ? (
          <Loading loading={!suggestion}>
            {suggestion ? (
              <SuggestionReport
                suggestion={suggestion}
                suggestionOnly={false}
              />
            ) : null}
          </Loading>
        ) : null}
        <Loading loading={!observation}>
          {observation ? <ObservationReport observation={observation} /> : null}
        </Loading>
      </div>
    );
  }
}

export const AssignmentsTable = ({
  assignments,
  editing,
  experiment,
  onChange,
  onClick,
  scrollable,
  submitting,
}) => (
  <TableCard onClick={onClick} scrollable={scrollable} copyObject={assignments}>
    <TableHeader className="main-header" nameHeader="Assignments" />
    <TableHeader nameHeader="Parameter" valueHeader="Value" />
    <AssignmentsTableBody
      assignments={assignments}
      editing={editing}
      experiment={experiment}
      onChange={onChange}
      submitting={submitting}
    />
  </TableCard>
);

export class ModelEvaluationComponent extends Component {
  static propTypes = {
    bestAssignment: schemas.BestAssignment,
    editing: PropTypes.bool,
    experiment: schemas.Experiment.isRequired,
    /*
      Note: changing this to schemas.Observation breaks on the summary page?
    */
    observation: PropTypes.object,
    onAssignmentsChange: PropTypes.func,
    onMetricsChange: PropTypes.func,
    submitting: PropTypes.bool,
    suggestion: PropTypes.oneOfType([
      schemas.Suggestion,
      schemas.QueuedSuggestion,
    ]),
  };

  state = {run: null};

  componentDidMount() {
    this.componentDidUpdate({});
  }

  componentDidUpdate(prevProps) {
    if (
      this.props.experiment.project &&
      this.props.suggestion !== prevProps.suggestion
    ) {
      this.fetchRun();
    }
  }

  fetchRun = () => {
    if (!this.props.suggestion) {
      this.setState({run: null});
      return;
    }
    this.setState({run: null}, () => {
      const suggestionId = this.props.suggestion.id;
      this.services.promiseApiClient
        .clients(this.props.experiment.client)
        .projects(this.props.experiment.project)
        .trainingRuns()
        .fetch({
          filters: JSON.stringify([
            {
              operator: "==",
              field: "suggestion",
              value: suggestionId,
            },
          ]),
          limit: 1,
        })
        .then(({data}) => {
          if (
            !this.props.suggestion ||
            this.props.suggestion.id !== suggestionId
          ) {
            return;
          }
          const run = _.first(data);
          this.setState({run});
        });
    });
  };

  render() {
    const {
      bestAssignment,
      editing,
      experiment,
      observation,
      onAssignmentsChange,
      onMetricsChange,
      submitting,
      suggestion,
    } = this.props;
    const resource = observation || suggestion || bestAssignment;
    const {assignments, metadata} = resource || {};
    const {failed, values} = observation || bestAssignment || {};
    const showMeasurement =
      isDefinedAndNotNull(failed) || isDefinedAndNotNull(values);
    const task =
      (observation && observation.task) || (suggestion && suggestion.task);
    const elapsedTooltip =
      "The time elapsed from creating a suggestion to reporting the corresponding observation";

    const run = this.state.run;

    return (
      <div className="model-evaluation-component">
        {run ? (
          <div className="run-info-section">
            <FieldValueDisplay
              field="Run"
              value={<a href={`/run/${run.id}`}>{run.name}</a>}
            />
            <RunsCheckpoints key={run.id} run={run} />
          </div>
        ) : null}
        {showMeasurement &&
        !editing &&
        observation &&
        observation.suggestion ? (
          <FieldValueDisplay
            field={<Tooltip tooltip={elapsedTooltip}>Evaluation Time</Tooltip>}
            value={
              <Loading loading={!suggestion}>
                {suggestion ? (
                  <Duration
                    endTime={observation.created}
                    startTime={suggestion.created}
                  />
                ) : null}
              </Loading>
            }
          />
        ) : null}
        {!editing && experiment.tasks && task ? (
          <div className="task-section">
            <FieldValueDisplay
              field="Task"
              value={`${task.name} - ${task.cost}`}
            />
          </div>
        ) : null}
        {showMeasurement ? (
          <div className="metric-section">
            <MeasurementsView
              editing={editing}
              experiment={experiment}
              failed={failed}
              measurements={values}
              onChange={onMetricsChange}
              submitting={submitting}
            />
          </div>
        ) : null}
        {!observation && suggestion ? (
          <SuggestionReport suggestion={suggestion} suggestionOnly={true} />
        ) : null}
        <div className="assignments-section">
          <div className="display-row">
            <AssignmentsTable
              assignments={assignments}
              editing={onAssignmentsChange ? editing : null}
              experiment={experiment}
              onChange={onAssignmentsChange}
              submitting={submitting}
            />
          </div>
          {metadata ? (
            <div className="display-row">
              <TableCard copyObject={metadata}>
                <TableHeader className="main-header" nameHeader="Metadata" />
                <TableHeader nameHeader="Key" valueHeader="Value" />
                <MetadataTableBody metadata={metadata} />
              </TableCard>
            </div>
          ) : null}
        </div>
        {!editing && observation ? (
          <CombinedReportSection
            experiment={experiment}
            observation={observation}
            submitting={submitting}
            suggestion={suggestion}
          />
        ) : null}
      </div>
    );
  }
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import AlertPanel from "../alert/panel";
import Spinner from "../component/spinner";
import makeEditableComponent from "../component/make-editable";
import schemas from "../react/schemas";
import ui from "./ui";
import {ConditionalsSection} from "./conditionals/section";
import {ConstraintsSection} from "./constraints";
import {ExperimentPropertiesSection} from "./properties";
import {ExperimentTypes, InteractionStates, ParameterTypes} from "./constants";
import {MetadataSection} from "./metadata";
import {MetricsCreateSection, MetricsEditSection} from "./metrics/section";
import {ParameterPriorsSection} from "./parameter_priors";
import {ParameterSection} from "./parameter";
import {Section} from "./section.js";
import {TaskSection} from "./task";
import {
  deepCopyJson,
  editKey,
  ignoreBlanks,
  isDefinedAndNotNull,
  maybeAsNumber,
  recursivelyOmitKeys,
} from "../utils";

const EditButtons = function (props) {
  if (props.canEdit && !props.create) {
    return (
      <div className="edit-buttons">
        {props.editing ? (
          <a className="btn btn-warning" onClick={props.cancelEditing}>
            Cancel
          </a>
        ) : null}
        <a
          className="btn create-button submit-button"
          onClick={props.toggleEditing}
        >
          {props.editing ? "Submit" : "Edit"}
        </a>
      </div>
    );
  } else {
    return <noscript />;
  }
};

EditButtons.propTypes = {
  canEdit: PropTypes.bool.isRequired,
  cancelEditing: PropTypes.func.isRequired,
  create: PropTypes.bool.isRequired,
  editing: PropTypes.bool.isRequired,
  toggleEditing: PropTypes.func.isRequired,
};

export const MetricObjectives = ["minimize", "maximize"];

const ExperimentEditor = makeEditableComponent(
  (props) => ({editing: props.create}),
  class ExperimentEditor extends React.Component {
    static propTypes = {
      alertBroker: schemas.AlertBroker.isRequired,
      canEdit: PropTypes.bool,
      cancelEditing: PropTypes.func.isRequired,
      clientId: PropTypes.string,
      create: PropTypes.bool.isRequired,
      creator: schemas.User,
      editing: PropTypes.bool.isRequired,
      editingRecoveryState: PropTypes.object,
      experiment: schemas.Experiment,
      onSuccess: PropTypes.func,
      promiseApiClient: schemas.PromiseApiClient.isRequired,
      renderAlerts: PropTypes.bool.isRequired,
      startEditing: PropTypes.func.isRequired,
      stopEditingAndSubmit: PropTypes.func.isRequired,
      submitted: PropTypes.bool.isRequired,
      submitting: PropTypes.bool.isRequired,
    };

    constructor(...args) {
      super(...args);
      const experiment = deepCopyJson(
        this.props.experiment || this.defaultExperiment(),
      );
      const metadata = _.chain(experiment.metadata)
        .pairs()
        .sortBy((m) => m[0])
        .map((m) => ({
          key: m[0],
          value: m[1],
          new: false,
          number: _.isNumber(m[1]),
        }))
        .value();

      this.state = {
        experimentInput: experiment,
        metadata: metadata,
      };
    }

    componentDidMount() {
      if (this.props.renderAlerts) {
        this.props.alertBroker.registerHandler((lert) => {
          this.setState({error: lert});
        });
      }
    }

    defaultExperiment = () => {
      const experimentInput = {
        name: null,
        metrics: [this.defaultMetric()],
        project: null,
      };
      experimentInput.parameters = [this.defaultParameter()];
      experimentInput.conditionals = [];
      return experimentInput;
    };

    defaultConditional = () => ({
      name: "",
      values: [{name: "", editKey: editKey()}],
      editKey: editKey(),
    });

    defaultMetric = () => ({
      name: "",
      object: "metric",
      objective: MetricObjectives[1],
    });

    defaultParameter = () => ({
      name: "",
      type: ParameterTypes.DOUBLE,
      bounds: {
        min: "",
        max: "",
      },
      categorical_values: [],
      isNew: true,
      editKey: editKey(),
    });

    setFieldOnObject = (field, value, object) => {
      const parts = field.split(".");
      const fieldName = parts.pop();
      const objectToSet = _.foldl(
        parts,
        function (o, f) {
          o[f] ||= {};
          return o[f];
        },
        object,
      );
      objectToSet[fieldName] = value;
      return object;
    };

    _setExperimentField = (field, value, cb) =>
      this.setState((prevState) => {
        const newExperiment = this.setFieldOnObject(
          field,
          value,
          prevState.experimentInput,
        );
        return {experimentInput: newExperiment};
      }, cb);

    experimentSetter = (field) => (e) => {
      e.persist();
      this._setExperimentField(field, e.target.value);
    };

    canEditParameters = () =>
      !this.props.experiment ||
      this.props.experiment.type !== ExperimentTypes.GRID;

    canEditMetrics = () =>
      this.props.experiment &&
      ui.thresholdsAllowedForExperiment(this.props.experiment);

    budgetKeyName = () =>
      this.props.experiment && ui.isAiExperiment(this.props.experiment)
        ? "budget"
        : "observation_budget";

    parameterKey = (p) => p.editKey || p.name;

    setParameter = (parameterInput, updater) => {
      this.setState((prevState) => {
        const prevParameterInput = _.find(
          prevState.experimentInput.parameters,
          (p) => this.parameterKey(p) === this.parameterKey(parameterInput),
        );
        const newParameter = _.isFunction(updater)
          ? updater(prevParameterInput)
          : _.extend({}, prevParameterInput, updater);
        const newParameterList = _.map(
          prevState.experimentInput.parameters,
          (p) =>
            this.parameterKey(p) === this.parameterKey(parameterInput)
              ? newParameter
              : p,
        );

        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            parameters: newParameterList,
          }),
        };
      });
    };

    removeParameter = (parameterInput) => {
      this.setState((prevState) => {
        const newParameterList = _.reject(
          prevState.experimentInput.parameters,
          (p) => this.parameterKey(p) === this.parameterKey(parameterInput),
        );

        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            parameters: newParameterList,
          }),
        };
      });
    };

    onMetricCreateChange = (newMetric, index) => {
      this.setState((prevState) => {
        const newMetricsList = prevState.experimentInput.metrics.slice();
        newMetricsList[index] = newMetric;
        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            metrics: newMetricsList,
          }),
        };
      });
    };

    onMetricCreateRemove = (index) => {
      this.setState((prevState) => {
        const metrics = prevState.experimentInput.metrics.slice();
        metrics.splice(index, 1);
        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            metrics: metrics,
          }),
        };
      });
    };

    submitButton = () => {
      let label;
      if (this.props.create) {
        label = "Create Experiment";
      } else if (this.props.editing) {
        label = "Submit";
      } else {
        label = "Edit";
      }
      return (
        <a
          href="#"
          className="btn create-button submit-button"
          onClick={this.toggleEditing}
        >
          {label}
        </a>
      );
    };

    addParameter = () => () => {
      this.setState((prevState) => ({
        experimentInput: _.extend({}, prevState.experimentInput, {
          parameters: prevState.experimentInput.parameters.concat([
            this.defaultParameter(),
          ]),
        }),
      }));
    };

    addMetricCreate = () => {
      this.setState((prevState) => ({
        experimentInput: _.extend({}, prevState.experimentInput, {
          metrics: prevState.experimentInput.metrics.concat([
            this.defaultMetric(),
          ]),
        }),
      }));
    };

    cancelEditing = (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.props.cancelEditing((recoveryState) => this.setState(recoveryState));
    };

    toggleEditing = (e) => {
      e.preventDefault();
      e.stopPropagation();

      this.setState({
        error: null,
      });

      if (this.props.editing) {
        this.sanitizeExperiment((experiment) =>
          this.props.stopEditingAndSubmit(
            (...args) =>
              this.updateExperiment(
                this.props.experiment && this.props.experiment.id,
                experiment,
                ...args,
              ),
            this.afterExperimentUpdate,
            this.apiError,
          ),
        );
      } else {
        this.props.startEditing(this.state);
      }
    };

    apiError = (error) => {
      if (error.status === 400 || error.status === 403) {
        if (error.message.indexOf("Missing required json key") > -1) {
          error.message = "Please fill in all required values.";
        }
        this.props.alertBroker.handle(error);
      }
    };

    updateExperiment = (experimentId, experiment, success, error) => {
      if (this.props.create) {
        this.props.promiseApiClient
          .clients(this.props.clientId)
          .experiments()
          .create(experiment)
          .then(success, error);
      } else {
        this.props.promiseApiClient
          .experiments(experimentId)
          .update(experiment)
          .then(success, error);
      }
    };

    sanitizeExperiment = (cb) => {
      const experimentInput = deepCopyJson(this.state.experimentInput);
      _.each(experimentInput.parameters, (p) => {
        if (p.type === ParameterTypes.CATEGORICAL) {
          p.bounds = null;
          p.categorical_values ||= [];
        } else {
          p.categorical_values = null;
        }
        if (p.bounds) {
          p.bounds.min = ignoreBlanks(maybeAsNumber(p.bounds.min));
          p.bounds.max = ignoreBlanks(maybeAsNumber(p.bounds.max));
        }
        if (isDefinedAndNotNull(p.default_value)) {
          if (p.type === ParameterTypes.CATEGORICAL) {
            p.default_value = ignoreBlanks(p.default_value);
          } else {
            p.default_value = ignoreBlanks(maybeAsNumber(p.default_value));
          }
        }
        if (p.grid) {
          p.bounds = null;
        }
      });

      experimentInput.metrics = _.map(experimentInput.metrics, (metric) => {
        if (isDefinedAndNotNull(metric.threshold)) {
          metric.threshold = maybeAsNumber(metric.threshold);
        }
        return metric;
      });

      experimentInput.observation_budget = ignoreBlanks(
        maybeAsNumber(experimentInput.observation_budget),
      );

      experimentInput.budget = ignoreBlanks(
        maybeAsNumber(experimentInput.budget),
      );

      experimentInput.parallel_bandwidth = ignoreBlanks(
        maybeAsNumber(experimentInput.parallel_bandwidth),
      );

      experimentInput.metadata = _.object(
        _.pluck(this.state.metadata, "key"),
        _.pluck(this.state.metadata, "value"),
      );

      if (_.isEmpty(experimentInput.project)) {
        experimentInput.project = null;
      }

      if (this.props.create) {
        const parametersData = _.map(experimentInput.parameters, (p) => {
          const newConditions = {};
          _.map(p.conditions, (valueKeys, conditionalKey) => {
            const conditional = _.find(
              experimentInput.conditionals,
              (c) => c.editKey === conditionalKey,
            );
            const values = _.filter(conditional.values, (v) =>
              _.contains(valueKeys, v.editKey),
            );
            newConditions[conditional.name] = _.pluck(values, "name");
          });
          return _.extend({}, p, {conditions: newConditions});
        });

        const conditionalsData = _.map(experimentInput.conditionals, (c) => {
          const values = _.pluck(c.values, "name");
          return _.extend({}, c, {values: values});
        });

        return cb(
          recursivelyOmitKeys(
            _.extend(
              {},
              experimentInput,
              {conditionals: conditionalsData},
              {parameters: parametersData},
            ),
            ["object", "editKey"],
          ),
        );
      } else {
        const keysForUpdate = [
          "name",
          "metadata",
          "parallel_bandwidth",
          "project",
          this.budgetKeyName(),
        ]
          .concat(this.canEditParameters() ? ["parameters"] : [])
          .concat(this.canEditMetrics() ? ["metrics"] : []);
        const omitKeys = ["object", "editKey", "conditionals", "conditions"];
        const experimentData = recursivelyOmitKeys(
          _.pick(experimentInput, keysForUpdate),
          omitKeys,
        );
        const previousInput = recursivelyOmitKeys(
          this.props.editingRecoveryState &&
            this.props.editingRecoveryState.experimentInput,
          omitKeys,
        );
        const updatedKeys = previousInput
          ? _.reject(_.keys(experimentData), (k) =>
              _.isEqual(experimentData[k], previousInput[k]),
            )
          : _.keys(experimentData);
        return cb(_.extend({}, _.pick(experimentData, ...updatedKeys)));
      }
    };

    afterExperimentUpdate = (experiment) => {
      this.setState((prevState) => ({
        experimentInput: experiment,
        metadata: _.map(prevState.metadata, (m) => ({
          key: m.key,
          value: m.value,
          new: false,
        })),
      }));
      if (this.props.onSuccess) {
        this.props.onSuccess(experiment);
      }
    };

    onChangeMetadata = (idx, key, value, isNew, number) => {
      this.setState((prevState) => {
        const metadata = _.map(prevState.metadata, _.identity);
        metadata[idx] = {
          key,
          value,
          new: isNew,
          number: number || false,
        };
        return {metadata};
      });
    };

    onAddMetadata = () => {
      this.setState((prevState) => ({
        metadata: prevState.metadata.concat({key: "", value: "", new: true}),
      }));
    };

    onRemoveMetadata = (idx) => {
      this.setState((prevState) => ({
        metadata: _.reject(prevState.metadata, (m, i) => i === idx),
      }));
    };

    onAddConditional = () => {
      this.setState((prevState) => {
        const prevConditionals = prevState.experimentInput.conditionals;
        const newConditionals = prevConditionals.concat([
          this.defaultConditional(),
        ]);
        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            conditionals: newConditionals,
          }),
        };
      });
    };

    onChangeConditional = (conditional, updater) => {
      const key = conditional.editKey || conditional.name;
      this.setState((prevState) => {
        const prevConditionals = prevState.experimentInput.conditionals;
        const prevConditional = _.find(
          prevConditionals,
          (c) => (c.editKey || c.name) === key,
        );
        const newConditional = _.isFunction(updater)
          ? updater(prevConditional)
          : _.extend({}, prevConditional, updater);
        const newConditionals = _.map(prevConditionals, (c) =>
          (c.editKey || c.name) === key ? newConditional : c,
        );
        const removedValues = _.difference(
          _.pluck(prevConditional.values, "editKey"),
          _.pluck(newConditional.values, "editKey"),
        );

        const removeConditionValue = (p) =>
          _.extend({}, p, {
            conditions: _.mapObject(p.conditions, (values) =>
              _.reject(values, (v) => _.contains(removedValues, v)),
            ),
          });
        const newParameters = _.map(
          prevState.experimentInput.parameters,
          removeConditionValue,
        );

        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            conditionals: newConditionals,
            parameters: newParameters,
          }),
        };
      });
    };

    onRemoveConditional = (conditional) => {
      // TODO(SN-1158): since we're removing conditions do we want a modal to warn people?
      // Note: we rely on editKey a lot for conditionals, not technically a problem since we never edit them
      this.setState((prevState) => {
        const prevConditionals = prevState.experimentInput.conditionals;
        const prevConditional = _.find(
          prevConditionals,
          (c) => c.editKey === conditional.editKey,
        );
        const newConditionals = _.reject(
          prevConditionals,
          (c) => c.editKey === conditional.editKey,
        );

        const removeCondition = (p) =>
          _.extend({}, p, {
            conditions: _.omit(p.conditions, prevConditional.editKey),
          });
        const newParameters = _.map(
          prevState.experimentInput.parameters,
          removeCondition,
        );

        return {
          experimentInput: _.extend({}, prevState.experimentInput, {
            conditionals: newConditionals,
            parameters: newParameters,
          }),
        };
      });
    };

    onMetricsEditChange = (metrics) =>
      this.setState((state) => ({
        experimentInput: _.extend({}, state.experimentInput, {
          metrics: metrics,
        }),
      }));

    render() {
      let interactionState;
      if (this.props.create) {
        interactionState = InteractionStates.CREATE;
      } else if (this.props.editing) {
        interactionState = InteractionStates.MODIFY;
      } else {
        interactionState = InteractionStates.READ_ONLY;
      }

      const experimentInput = this.state.experimentInput;

      const loading =
        this.props.submitting || (this.props.submitted && this.props.create);

      const maybeMetricsCreate = interactionState ===
        InteractionStates.CREATE && (
        <MetricsCreateSection
          addMetricCreate={this.addMetricCreate}
          interactionState={interactionState}
          metrics={experimentInput.metrics}
          onMetricCreateChange={this.onMetricCreateChange}
          onMetricCreateRemove={this.onMetricCreateRemove}
        />
      );
      const maybeMetricsExisting = ui.existingInteraction(interactionState) && (
        <MetricsEditSection
          canEditMetrics={this.canEditMetrics}
          experimentInput={experimentInput}
          interactionState={interactionState}
          onMetricsEditChange={this.onMetricsEditChange}
        />
      );
      return (
        <div
          className={classNames({
            "experiment-editor": true,
            loading: loading,
            editing: this.props.editing,
          })}
        >
          <Spinner position="absolute" loading={loading} />
          <div className="experiment-editor-content">
            <Section
              infoClassName="experiment-summary-info"
              innerClassName="experiment-properties"
              heading="Experiment Properties"
              sectionMeta={
                <EditButtons
                  canEdit={this.props.canEdit}
                  cancelEditing={this.cancelEditing}
                  create={this.props.create}
                  editing={this.props.editing}
                  toggleEditing={this.toggleEditing}
                />
              }
              sectionBody={
                <>
                  <ExperimentPropertiesSection
                    clientId={this.props.clientId}
                    creator={this.props.creator}
                    experimentInput={experimentInput}
                    experimentSetter={this.experimentSetter}
                    interactionState={interactionState}
                  />
                  {maybeMetricsCreate}
                </>
              }
            />
            {maybeMetricsExisting}
            <ParameterSection
              addParameter={this.addParameter}
              canEditParameters={this.canEditParameters}
              experiment={this.props.experiment}
              experimentInput={experimentInput}
              interactionState={interactionState}
              parameterKey={this.parameterKey}
              removeParameter={this.removeParameter}
              setParameter={this.setParameter}
            />
            <TaskSection
              experiment={this.props.experiment}
              interactionState={interactionState}
            />
            <ParameterPriorsSection
              experiment={this.props.experiment}
              interactionState={interactionState}
              parameters={experimentInput.parameters}
            />
            <ConditionalsSection
              experimentInput={experimentInput}
              interactionState={interactionState}
              onAddConditional={this.onAddConditional}
              onChangeConditional={this.onChangeConditional}
              onRemoveConditional={this.onRemoveConditional}
              setParameter={this.setParameter}
            />
            <ConstraintsSection
              interactionState={interactionState}
              linearConstraints={experimentInput.linear_constraints}
            />
            <MetadataSection
              interactionState={interactionState}
              metadata={this.state.metadata}
              onAdd={this.onAddMetadata}
              onChange={this.onChangeMetadata}
              onRemove={this.onRemoveMetadata}
            />
          </div>
          {this.state.error ? (
            <AlertPanel
              error={this.state.error}
              onDismiss={() => this.setState({error: null})}
            />
          ) : null}
          {this.props.create ? (
            <div className="submit-button-holder">{this.submitButton()}</div>
          ) : null}
        </div>
      );
    }
  },
);

export default ExperimentEditor;

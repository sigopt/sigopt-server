/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";

import {ExperimentTypes, ParameterTypes} from "../experiment/constants";

const AjaxClient = PropTypes.object;
const AlertBroker = PropTypes.object;
const ClientsideConfigBroker = PropTypes.object;
const ErrorNotifier = PropTypes.object;
const LegacyApiClient = PropTypes.object;
const Navigator = PropTypes.object;
const PromiseApiClient = PropTypes.object;
const SessionUpdater = PropTypes.object;

const ServicesKeys = {
  AjaxClient,
  AlertBroker,
  ClientsideConfigBroker,
  ErrorNotifier,
  LegacyApiClient,
  Navigator,
  PromiseApiClient,
  SessionUpdater,
};
const Services = PropTypes.shape(ServicesKeys);

const LoginState = PropTypes.shape({
  apiToken: PropTypes.string,
  apiUrl: PropTypes.string,
  clientId: PropTypes.string,
  csrfToken: PropTypes.string,
  userId: PropTypes.string,
});

const Bounds = PropTypes.shape({
  max: PropTypes.number.isRequired,
  min: PropTypes.number.isRequired,
  object: PropTypes.oneOf(["bounds"]).isRequired,
});

const Conditional = PropTypes.shape({
  name: PropTypes.string.isRequired,
  values: PropTypes.arrayOf(PropTypes.string).isRequired,
});

const CategoricalValue = PropTypes.shape({
  enum_index: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["categorical_value"]).isRequired,
});

const Parameter = PropTypes.shape({
  bounds: Bounds,
  categorical_values: PropTypes.arrayOf(CategoricalValue),
  default_value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  grid: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  ),
  name: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["parameter"]).isRequired,
  type: PropTypes.oneOf(_.values(ParameterTypes)).isRequired,
});

const Experiment = PropTypes.shape({
  client: PropTypes.string.isRequired,
  conditionals: PropTypes.arrayOf(Conditional),
  created: PropTypes.number,
  development: PropTypes.bool.isRequired,
  id: PropTypes.string.isRequired,
  metric: PropTypes.object,
  name: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["experiment"]).isRequired,
  observation_budget: PropTypes.number,
  parallel_bandwidth: PropTypes.number,
  parameters: PropTypes.arrayOf(Parameter).isRequired,
  progress: PropTypes.object,
  state: PropTypes.string.isRequired,
  type: PropTypes.oneOf(_.values(ExperimentTypes)).isRequired,
  updated: PropTypes.number,
});

const Project = PropTypes.shape({
  client: PropTypes.string.isRequired,
  created: PropTypes.number.isRequired,
  deleted: PropTypes.bool.isRequired,
  experiment_count: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  metadata: PropTypes.object,
  training_run_count: PropTypes.number,
  user: PropTypes.string,
  updated: PropTypes.number.isRequired,
});

const Assignments = PropTypes.objectOf(
  PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
);

const MetricEvaluation = PropTypes.shape({
  name: PropTypes.string,
  object: PropTypes.oneOf(["metric_evaluation"]),
  value: PropTypes.number,
  value_stddev: PropTypes.number,
});

const Metadata = PropTypes.objectOf(
  PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
);

const observationShape = {
  assignments: Assignments,
  created: PropTypes.number,
  experiment: PropTypes.string,
  failed: PropTypes.bool,
  id: PropTypes.string,
  metadata: Metadata,
  object: PropTypes.oneOf(["observation"]),
  suggestion: PropTypes.string,
  value: PropTypes.number,
  value_stddev: PropTypes.number,
  values: PropTypes.arrayOf(MetricEvaluation),
};

const observationRequiresFields = (fields, extended) => {
  const copiedShape = _.clone(observationShape);
  _.each(fields, (field) => {
    copiedShape[field] = copiedShape[field].isRequired;
  });
  return PropTypes.shape(_.extend(copiedShape, extended));
};

const Observation = observationRequiresFields([
  "assignments",
  "experiment",
  "id",
  "object",
  "values",
]);

const BestAssignment = PropTypes.shape({
  assignments: Assignments.isRequired,
  id: PropTypes.string,
  value: PropTypes.number,
  value_stddev: PropTypes.number,
  values: PropTypes.arrayOf(MetricEvaluation).isRequired,
});

const QueuedSuggestion = PropTypes.shape({
  assignments: Assignments.isRequired,
  created: PropTypes.number,
  experiment: PropTypes.string.isRequired,
  id: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["queued_suggestion"]).isRequired,
});

const Suggestion = PropTypes.shape({
  assignments: Assignments.isRequired,
  created: PropTypes.number,
  deleted: PropTypes.bool,
  experiment: PropTypes.string.isRequired,
  id: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["suggestion"]).isRequired,
  state: PropTypes.string.isRequired,
});

const Note = PropTypes.shape({
  client: PropTypes.string,
  contents: PropTypes.string.isRequired,
  created: PropTypes.number.isRequired,
  object: PropTypes.oneOf(["project_note"]).isRequired,
  project: PropTypes.string,
  user: PropTypes.string,
});

const TrainingRun = PropTypes.shape({
  checkpoint_count: PropTypes.number.isRequired,
  created: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  finished: PropTypes.bool.isRequired,
  metadata: Metadata.isRequired,
  object: PropTypes.oneOf(["training_run"]).isRequired,
  observation: PropTypes.string,
  suggestion: PropTypes.string,
  updated: PropTypes.number.isRequired,
});

const Checkpoint = PropTypes.shape({
  created: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  metadata: Metadata.isRequired,
  object: PropTypes.oneOf(["checkpoint"]).isRequired,
  training_run: PropTypes.string.isRequired,
  values: PropTypes.arrayOf(MetricEvaluation.isRequired).isRequired,
});

const Client = PropTypes.shape({
  created: PropTypes.number,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["client"]).isRequired,
});

const Organization = PropTypes.shape({
  created: PropTypes.number,
  data_storage_bytes: PropTypes.number,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["organization"]).isRequired,
});

const User = PropTypes.shape({
  created: PropTypes.number,
  email: PropTypes.string,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["user"]).isRequired,
  optimized_runs_in_billing_cycle: PropTypes.number,
});

const PendingPermission = PropTypes.shape({
  client: PropTypes.string.isRequired,
  client_name: PropTypes.string.isRequired,
  email: PropTypes.string.isRequired,
  role: PropTypes.string.isRequired,
});

const Invite = PropTypes.shape({
  created: PropTypes.number,
  email: PropTypes.string.isRequired,
  membership_type: PropTypes.string.isRequired,
  object: PropTypes.oneOf(["invite"]).isRequired,
  organization: PropTypes.string.isRequired,
  organization_name: PropTypes.string,
  pending_permissions: PropTypes.arrayOf(PendingPermission.isRequired),
});

const Permission = PropTypes.shape({
  client: Client.isRequired,
  is_owner: PropTypes.bool.isRequired,
  user: User.isRequired,
  can_admin: PropTypes.bool.isRequired,
  can_write: PropTypes.bool.isRequired,
  can_read: PropTypes.bool.isRequired,
});

const Pagination = PropTypes.shape({
  count: PropTypes.number,
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  paging: PropTypes.shape({
    after: PropTypes.string,
    before: PropTypes.string,
  }),
});

const Membership = PropTypes.shape({
  organization: Organization.isRequired,
  type: PropTypes.oneOf(["owner", "member"]).isRequired,
  user: User.isRequired,
});

const Token = PropTypes.shape({
  all_experiments: PropTypes.bool.isRequired,
  client: PropTypes.string,
  development: PropTypes.bool.isRequired,
  experiment: PropTypes.string,
  permissions: PropTypes.oneOf(["read", "write", null]).isRequired,
  token: PropTypes.string.isRequired,
  user: PropTypes.string,
});

const MetricImportance = PropTypes.shape({
  metric: PropTypes.string,
  importances: PropTypes.object.isRequired,
  object: PropTypes.oneOf(["metric_importances"]).isRequired,
});

const Metric = PropTypes.shape({
  name: PropTypes.string,
  objective: PropTypes.string,
  threshold: PropTypes.number,
});

const Task = PropTypes.shape({
  name: PropTypes.string.isRequired,
  cost: PropTypes.number.isRequired,
});

export default _.extend({}, ServicesKeys, {
  Assignments,
  BestAssignment,
  Bounds,
  CategoricalValue,
  Checkpoint,
  Client,
  Conditional,
  Experiment,
  MetricImportance,
  Metric,
  Invite,
  LoginState,
  Metadata,
  MetricEvaluation,
  Membership,
  Note,
  Observation,
  observationRequiresFields,
  Organization,
  Pagination,
  Parameter,
  Permission,
  PendingPermission,
  Project,
  QueuedSuggestion,
  Services,
  Suggestion,
  Task,
  Token,
  TrainingRun,
  User,
});

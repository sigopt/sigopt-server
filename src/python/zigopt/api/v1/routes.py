# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.blueprint import ApiBlueprint
from zigopt.api.common import handler_registry
from zigopt.handlers.aiexperiments.best_training_runs import AiExperimentsBestTrainingRunsHandler
from zigopt.handlers.aiexperiments.create import ClientsProjectsAiExperimentsCreateHandler
from zigopt.handlers.aiexperiments.delete import AiExperimentsDeleteHandler
from zigopt.handlers.aiexperiments.detail import AiExperimentsDetailHandler
from zigopt.handlers.aiexperiments.training_runs.create import AiExperimentTrainingRunsCreateHandler
from zigopt.handlers.aiexperiments.update import AiExperimentsUpdateHandler
from zigopt.handlers.clients.aiexperiments import (
  AiExperimentsListHandler,
  ClientsAiExperimentsListHandler,
  ClientsProjectsAiExperimentsListHandler,
)
from zigopt.handlers.clients.create import ClientsCreateHandler
from zigopt.handlers.clients.delete import ClientsDeleteHandler
from zigopt.handlers.clients.detail import ClientsDetailHandler
from zigopt.handlers.clients.experiments import (
  ClientsExperimentsHandler,
  ClientsProjectsExperimentsHandler,
  ExperimentsListHandler,
  UsersExperimentsHandler,
)
from zigopt.handlers.clients.invite import ClientsCreateInviteHandler, ClientsUninviteHandler
from zigopt.handlers.clients.pending_permissions import ClientsPendingPermissionsHandler
from zigopt.handlers.clients.permissions import ClientsPermissionsHandler
from zigopt.handlers.clients.tokens import (
  ClientsTokensCreateHandler,
  ClientsTokensDeleteHandler,
  ClientsTokensDetailHandler,
  ClientsTokensListDetailHandler,
  ClientsTokensUpdateHandler,
  ExperimentsTokensCreateHandler,
  TrainingRunsTokensCreateHandler,
)
from zigopt.handlers.clients.update import ClientsUpdateHandler
from zigopt.handlers.experiments.best_assignments import ExperimentsBestAssignmentsHandler
from zigopt.handlers.experiments.best_practices import ExperimentsBestPracticesHandler
from zigopt.handlers.experiments.checkpoints.create import CheckpointsCreateHandler
from zigopt.handlers.experiments.checkpoints.detail import CheckpointsDetailHandler, CheckpointsDetailMultiHandler
from zigopt.handlers.experiments.create import ClientsExperimentsCreateHandler, ExperimentsCreateHandler
from zigopt.handlers.experiments.delete import ExperimentsDeleteHandler
from zigopt.handlers.experiments.detail import ExperimentsDetailHandler
from zigopt.handlers.experiments.hyperparameters.delete import ExperimentsHyperparametersDeleteHandler
from zigopt.handlers.experiments.metric_importances.detail import MetricImportancesDetailHandler
from zigopt.handlers.experiments.metric_importances.update import MetricImportancesUpdateHandler
from zigopt.handlers.experiments.observations.create import ObservationsCreateHandler, ObservationsCreateMultiHandler
from zigopt.handlers.experiments.observations.delete import ObservationsDeleteAllHandler, ObservationsDeleteHandler
from zigopt.handlers.experiments.observations.detail import ObservationsDetailHandler, ObservationsDetailMultiHandler
from zigopt.handlers.experiments.observations.update import ObservationsUpdateHandler
from zigopt.handlers.experiments.queued_suggestions.create import QueuedSuggestionsCreateHandler
from zigopt.handlers.experiments.queued_suggestions.delete import QueuedSuggestionsDeleteHandler
from zigopt.handlers.experiments.queued_suggestions.detail import (
  QueuedSuggestionsDetailHandler,
  QueuedSuggestionsDetailMultiHandler,
)
from zigopt.handlers.experiments.stopping_criteria import ExperimentsStoppingCriteriaHandler
from zigopt.handlers.experiments.suggestions.create import SuggestionsCreateHandler
from zigopt.handlers.experiments.suggestions.delete import SuggestionsDeleteAllHandler, SuggestionsDeleteHandler
from zigopt.handlers.experiments.suggestions.detail import SuggestionsDetailHandler, SuggestionsDetailMultiHandler
from zigopt.handlers.experiments.suggestions.update import SuggestionsUpdateHandler
from zigopt.handlers.experiments.update import ExperimentsUpdateHandler
from zigopt.handlers.files.detail import FileDetailHandler
from zigopt.handlers.organizations.clients import (
  OrganizationsClientsCreateHandler,
  OrganizationsClientsListDetailHandler,
)
from zigopt.handlers.organizations.detail import OrganizationsDetailHandler
from zigopt.handlers.organizations.experiments import OrganizationsExperimentsListDetailHandler
from zigopt.handlers.organizations.invite.create import OrganizationsCreateInviteHandler
from zigopt.handlers.organizations.invite.delete import OrganizationsUninviteHandler
from zigopt.handlers.organizations.invite.list import OrganizationsInvitesListDetailHandler
from zigopt.handlers.organizations.invite.update import OrganizationsUpdateInviteHandler
from zigopt.handlers.organizations.memberships import OrganizationsMembershipsListDetailHandler
from zigopt.handlers.organizations.permissions import OrganizationsPermissionsListDetailHandler
from zigopt.handlers.organizations.update import OrganizationsUpdateHandler
from zigopt.handlers.projects.create import ClientsProjectsCreateHandler
from zigopt.handlers.projects.detail import ClientsProjectsDetailHandler
from zigopt.handlers.projects.list import ClientsProjectsListHandler
from zigopt.handlers.projects.notes.create import ClientsProjectsNotesCreateHandler
from zigopt.handlers.projects.notes.list import ClientsProjectsNotesListHandler
from zigopt.handlers.projects.update import ClientsProjectsUpdateHandler
from zigopt.handlers.tags.create import ClientsTagsCreateHandler
from zigopt.handlers.tags.list import ClientsTagsListHandler
from zigopt.handlers.training_runs.create import (
  ProjectsTrainingRunsBatchCreateHandler,
  ProjectsTrainingRunsCreateHandler,
)
from zigopt.handlers.training_runs.delete import TrainingRunsDeleteHandler
from zigopt.handlers.training_runs.detail import TrainingRunsDetailHandler
from zigopt.handlers.training_runs.files import TrainingRunsCreateFileHandler
from zigopt.handlers.training_runs.list import (
  ClientsTrainingRunsDetailMultiHandler,
  OrganizationsTrainingRunsDetailMultiHandler,
  ProjectsTrainingRunsDetailMultiHandler,
)
from zigopt.handlers.training_runs.tags import TrainingRunsAddTagHandler, TrainingRunsRemoveTagHandler
from zigopt.handlers.training_runs.update import TrainingRunsUpdateHandler
from zigopt.handlers.users.create import UsersCreateHandler
from zigopt.handlers.users.delete import UsersDeleteHandler
from zigopt.handlers.users.detail import UsersDetailHandler
from zigopt.handlers.users.email import ResendVerificationEmailHandler, UsersResendVerificationEmailHandler
from zigopt.handlers.users.memberships import UsersMembershipsListDetailHandler
from zigopt.handlers.users.password import UsersChangePasswordHandler, UsersResetPasswordHandler
from zigopt.handlers.users.pending_permissions import UsersPendingPermissionsHandler
from zigopt.handlers.users.permissions import UsersPermissionsHandler, UsersRequestPermissionsHandler
from zigopt.handlers.users.sessions import CreateSessionHandler, SessionHandler
from zigopt.handlers.users.update import UsersUpdateHandler
from zigopt.handlers.web_data.create import WebDataCreateHandler
from zigopt.handlers.web_data.delete import WebDataDeleteHandler
from zigopt.handlers.web_data.list import WebDataListHandler
from zigopt.handlers.web_data.update import WebDataUpdateHandler
from zigopt.net.errors import BadParamError

from sigoptaux.errors import ValidationError


def initialize_blueprint(app):
  api = ApiBlueprint("api_v1", app)
  register_handler = handler_registry(api)

  @app.errorhandler(ValidationError)
  def handle_validation_errors(e):
    return BadParamError(e.msg).get_error_response()

  api.register_error_handler(ValidationError, handle_validation_errors)

  def get_route(route_name, handler_cls):
    return register_handler(route_name, handler_cls, ["GET"], provide_automatic_options=True)

  def post_route(route_name, handler_cls):
    return register_handler(route_name, handler_cls, ["POST"], provide_automatic_options=True)

  def put_route(route_name, handler_cls):
    return register_handler(route_name, handler_cls, ["PUT"], provide_automatic_options=True)

  def merge_route(route_name, handler_cls):
    return register_handler(route_name, handler_cls, ["MERGE"], provide_automatic_options=True)

  def delete_route(route_name, handler_cls):
    return register_handler(route_name, handler_cls, ["DELETE"], provide_automatic_options=True)

  #
  # Organizations
  #
  get_route("/organizations/<int:organization_id>", OrganizationsDetailHandler)
  put_route("/organizations/<int:organization_id>", OrganizationsUpdateHandler)

  get_route("/organizations/<int:organization_id>/clients", OrganizationsClientsListDetailHandler)

  get_route("/organizations/<int:organization_id>/memberships", OrganizationsMembershipsListDetailHandler)

  post_route("/organizations/<int:organization_id>/clients", OrganizationsClientsCreateHandler)

  get_route("/organizations/<int:organization_id>/invites", OrganizationsInvitesListDetailHandler)
  post_route("/organizations/<int:organization_id>/invites", OrganizationsCreateInviteHandler)
  put_route("/organizations/<int:organization_id>/invites/<int:invite_id>", OrganizationsUpdateInviteHandler)
  delete_route("/organizations/<int:organization_id>/invites", OrganizationsUninviteHandler)

  get_route("/organizations/<int:organization_id>/experiments", OrganizationsExperimentsListDetailHandler)

  get_route("/organizations/<int:organization_id>/permissions", OrganizationsPermissionsListDetailHandler)

  #
  # Clients
  #
  get_route("/clients/<int:client_id>", ClientsDetailHandler)
  post_route("/clients", ClientsCreateHandler)
  put_route("/clients/<int:client_id>", ClientsUpdateHandler)
  delete_route("/clients/<int:client_id>", ClientsDeleteHandler)

  get_route("/clients/<int:client_id>/experiments", ClientsExperimentsHandler)
  post_route("/clients/<int:client_id>/experiments", ClientsExperimentsCreateHandler)

  get_route("/clients/<int:client_id>/aiexperiments", ClientsAiExperimentsListHandler)

  post_route("/clients/<int:client_id>/projects", ClientsProjectsCreateHandler)
  get_route("/clients/<int:client_id>/projects", ClientsProjectsListHandler)
  get_route("/clients/<int:client_id>/projects/<string:project_reference_id>", ClientsProjectsDetailHandler)
  put_route("/clients/<int:client_id>/projects/<string:project_reference_id>", ClientsProjectsUpdateHandler)

  get_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/experiments",
    ClientsProjectsExperimentsHandler,
  )

  get_route(
    "/aiexperiments",
    AiExperimentsListHandler,
  )
  get_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/aiexperiments",
    ClientsProjectsAiExperimentsListHandler,
  )

  get_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/notes",
    ClientsProjectsNotesListHandler,
  )
  post_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/notes",
    ClientsProjectsNotesCreateHandler,
  )

  post_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/aiexperiments",
    ClientsProjectsAiExperimentsCreateHandler,
  )
  post_route("/aiexperiments/<int:experiment_id>/training_runs", AiExperimentTrainingRunsCreateHandler)
  get_route(
    "/aiexperiments/<experiment_id>",
    AiExperimentsDetailHandler,
  )
  put_route(
    "/aiexperiments/<experiment_id>",
    AiExperimentsUpdateHandler,
  )
  delete_route(
    "/aiexperiments/<experiment_id>",
    AiExperimentsDeleteHandler,
  )
  get_route(
    "/aiexperiments/<experiment_id>/best_training_runs",
    AiExperimentsBestTrainingRunsHandler,
  )

  get_route("/clients/<int:client_id>/roles", ClientsPermissionsHandler)
  get_route("/clients/<int:client_id>/permissions", ClientsPermissionsHandler)

  get_route("/clients/<int:client_id>/pending_permissions", ClientsPendingPermissionsHandler)

  post_route("/clients/<int:client_id>/invites", ClientsCreateInviteHandler)
  delete_route("/clients/<int:client_id>/invites", ClientsUninviteHandler)

  get_route("/clients/<int:client_id>/tokens", ClientsTokensListDetailHandler)

  post_route("/clients/<int:client_id>/tags", ClientsTagsCreateHandler)
  get_route("/clients/<int:client_id>/tags", ClientsTagsListHandler)

  #
  # Users
  #
  get_route("/users/<int:user_id>", UsersDetailHandler)
  post_route("/users", UsersCreateHandler)
  put_route("/users/<int:user_id>", UsersUpdateHandler)
  delete_route("/users/<int:user_id>", UsersDeleteHandler)

  get_route("/users/<int:user_id>/experiments", UsersExperimentsHandler)

  get_route("/users/<int:user_id>/pending_permissions", UsersPendingPermissionsHandler)

  get_route("/users/<int:user_id>/roles", UsersPermissionsHandler)
  get_route("/users/<int:user_id>/permissions", UsersPermissionsHandler)
  post_route("/users/<int:user_id>/permissions", UsersRequestPermissionsHandler)
  post_route("/users/<int:user_id>/verifications", UsersResendVerificationEmailHandler)

  get_route("/users/<int:user_id>/memberships", UsersMembershipsListDetailHandler)

  # Verifications
  post_route("/verifications", ResendVerificationEmailHandler)

  #
  # Sessions
  #
  get_route("/sessions", SessionHandler)
  post_route("/sessions", CreateSessionHandler)
  put_route("/sessions", UsersChangePasswordHandler)
  delete_route("/sessions", UsersResetPasswordHandler)

  #
  # Experiment
  #
  get_route("/experiments", ExperimentsListHandler)
  get_route("/experiments/<int:experiment_id>", ExperimentsDetailHandler)
  post_route("/experiments", ExperimentsCreateHandler)
  put_route("/experiments/<int:experiment_id>", ExperimentsUpdateHandler)
  delete_route("/experiments/<int:experiment_id>", ExperimentsDeleteHandler)

  put_route("/experiments/<int:experiment_id>/metric_importances", MetricImportancesUpdateHandler)
  get_route("/experiments/<int:experiment_id>/metric_importances", MetricImportancesDetailHandler)
  get_route("/experiments/<int:experiment_id>/best_practices", ExperimentsBestPracticesHandler)
  get_route("/experiments/<int:experiment_id>/stopping_criteria", ExperimentsStoppingCriteriaHandler)
  delete_route("/experiments/<int:experiment_id>/hyperparameters", ExperimentsHyperparametersDeleteHandler)
  get_route("/experiments/<int:experiment_id>/best_assignments", ExperimentsBestAssignmentsHandler)

  #
  # Suggestions
  #
  get_route("/experiments/<int:experiment_id>/suggestions/<int:suggestion_id>", SuggestionsDetailHandler)
  get_route("/experiments/<int:experiment_id>/suggestions", SuggestionsDetailMultiHandler)
  post_route("/experiments/<int:experiment_id>/suggestions", SuggestionsCreateHandler)
  put_route("/experiments/<int:experiment_id>/suggestions/<int:suggestion_id>", SuggestionsUpdateHandler)
  delete_route("/experiments/<int:experiment_id>/suggestions/<int:suggestion_id>", SuggestionsDeleteHandler)
  delete_route("/experiments/<int:experiment_id>/suggestions", SuggestionsDeleteAllHandler)

  #
  # Queued Suggestions
  # TODO(SN-1068): other routes
  #
  get_route(
    "/experiments/<int:experiment_id>/queued_suggestions/<int:queued_suggestion_id>",
    QueuedSuggestionsDetailHandler,
  )
  get_route(
    "/experiments/<int:experiment_id>/queued_suggestions",
    QueuedSuggestionsDetailMultiHandler,
  )
  post_route(
    "/experiments/<int:experiment_id>/queued_suggestions",
    QueuedSuggestionsCreateHandler,
  )
  # put_route(
  #   "/experiments/<int:experiment_id>/queued_suggestions/<int:queued_suggestion_id>",
  #   QueuedSuggestionsUpdateHandler,
  # )
  delete_route(
    "/experiments/<int:experiment_id>/queued_suggestions/<int:queued_suggestion_id>",
    QueuedSuggestionsDeleteHandler,
  )
  # delete_route(
  #   "/experiments/<int:experiment_id>/queued_suggestions",
  #   QueuedSuggestionsDeleteAllHandler,
  # )

  #
  # Observations
  #
  get_route("/experiments/<int:experiment_id>/observations/<int:observation_id>", ObservationsDetailHandler)
  get_route("/experiments/<int:experiment_id>/observations", ObservationsDetailMultiHandler)
  post_route("/experiments/<int:experiment_id>/observations", ObservationsCreateHandler)
  post_route("/experiments/<int:experiment_id>/observations/batch", ObservationsCreateMultiHandler)
  put_route("/experiments/<int:experiment_id>/observations/<int:observation_id>", ObservationsUpdateHandler)
  delete_route("/experiments/<int:experiment_id>/observations/<int:observation_id>", ObservationsDeleteHandler)
  delete_route("/experiments/<int:experiment_id>/observations", ObservationsDeleteAllHandler)

  #
  # Training runs
  #
  get_route("/training_runs/<int:training_run_id>", TrainingRunsDetailHandler)
  put_route("/training_runs/<int:training_run_id>", TrainingRunsUpdateHandler)
  merge_route("/training_runs/<int:training_run_id>", TrainingRunsUpdateHandler)
  delete_route("/training_runs/<int:training_run_id>", TrainingRunsDeleteHandler)
  post_route("/training_runs/<int:training_run_id>/tags", TrainingRunsAddTagHandler)
  delete_route("/training_runs/<int:training_run_id>/tags/<int:tag_id>", TrainingRunsRemoveTagHandler)
  post_route("/training_runs/<int:training_run_id>/files", TrainingRunsCreateFileHandler)
  get_route("/files/<int:file_id>", FileDetailHandler)

  get_route("/clients/<int:client_id>/training_runs", ClientsTrainingRunsDetailMultiHandler)
  get_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/training_runs",
    ProjectsTrainingRunsDetailMultiHandler,
  )
  post_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/training_runs",
    ProjectsTrainingRunsCreateHandler,
  )
  post_route(
    "/clients/<int:client_id>/projects/<string:project_reference_id>/training_runs/batch",
    ProjectsTrainingRunsBatchCreateHandler,
  )

  get_route("/organizations/<int:organization_id>/training_runs", OrganizationsTrainingRunsDetailMultiHandler)

  #
  # WebData
  #

  post_route("/web_data", WebDataCreateHandler)
  get_route("/web_data", WebDataListHandler)
  put_route("/web_data", WebDataUpdateHandler)
  delete_route("/web_data", WebDataDeleteHandler)

  #
  # Checkpoints
  #
  get_route("/training_runs/<int:training_run_id>/checkpoints", CheckpointsDetailMultiHandler)
  get_route("/training_runs/<int:training_run_id>/checkpoints/<int:checkpoint_id>", CheckpointsDetailHandler)
  post_route("/training_runs/<int:training_run_id>/checkpoints", CheckpointsCreateHandler)

  #
  # Tokens
  #
  get_route("/tokens/<token>", ClientsTokensDetailHandler)
  put_route("/tokens/<token>", ClientsTokensUpdateHandler)
  delete_route("/tokens/<token>", ClientsTokensDeleteHandler)
  post_route("/clients/<int:client_id>/tokens", ClientsTokensCreateHandler)
  post_route("/experiments/<int:experiment_id>/tokens", ExperimentsTokensCreateHandler)
  post_route("/training_runs/<int:training_run_id>/tokens", TrainingRunsTokensCreateHandler)

  return api

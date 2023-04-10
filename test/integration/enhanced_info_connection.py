# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# A sigopt.Connection that has private endpoints and objects
import os

from sigopt.endpoint import ApiEndpoint
from sigopt.interface import ConnectionImpl, object_or_paginated_objects
from sigopt.objects import ApiObject, Client, Experiment, MetricImportances, Pagination, TrainingRun
from sigopt.request_driver import RequestDriver
from sigopt.resource import ApiResource

from integration.enhanced_info_objects import (
  EnhancedInfoAiExperiment,
  EnhancedInfoOrganization,
  EnhancedInfoSession,
  EnhancedInfoToken,
  EnhancedInfoTrainingRun,
  EnhancedInfoUser,
  File,
  Invite,
  Membership,
  PendingPermission,
  Permission,
  ProjectNote,
  Tag,
  WebData,
  object_or_internal_paginated_objects,
)


# pylint: disable=protected-access
class EnhancedInfoConnection:
  def __init__(self, client_token, headers=None, requestor=None):
    these_headers = {
      "Content-Type": "application/json",
    }
    these_headers.update(headers or {})
    self.conn = ConnectionImpl(requestor or RequestDriver(client_token, "", these_headers))
    self.conn.set_verify_ssl_certs(os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS"))

    # Custom endpoints

    self.conn.experiments._endpoints["fetch"] = ApiEndpoint(
      None,
      object_or_paginated_objects(Experiment),
      "GET",
      "fetch",
    )

    self.conn.experiments._endpoints["create"] = ApiEndpoint(None, Experiment, "POST", "create")
    self.conn.experiments._endpoints["update"] = ApiEndpoint(None, Experiment, "PUT", "update")

    self.conn.clients._sub_resources["tags"] = ApiResource(
      self.conn,
      "tags",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Tag, *args, **kwargs), "GET", "fetch"),
        ApiEndpoint(None, Tag, "POST", "create"),
      ],
    )

    # /clients/X/projects/Y/notes
    self.conn.clients._sub_resources["projects"]._sub_resources["notes"] = ApiResource(
      self.conn,
      "notes",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(ProjectNote, *args, **kwargs), "GET", "fetch"),
        ApiEndpoint(None, ProjectNote, "POST", "create"),
      ],
    )

    # /clients/X/projects/Y/aiexperiments
    self.conn.clients._sub_resources["projects"]._sub_resources["aiexperiments"] = ApiResource(
      self.conn,
      "aiexperiments",
      endpoints=[
        ApiEndpoint(None, EnhancedInfoAiExperiment, "POST", "create"),
        ApiEndpoint(
          None, lambda *args, **kwargs: Pagination(EnhancedInfoAiExperiment, *args, **kwargs), "GET", "fetch"
        ),
      ],
    )

    # /aiexperiments
    self.conn.aiexperiments = ApiResource(
      self.conn,
      "aiexperiments",
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(EnhancedInfoAiExperiment), "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoAiExperiment, "PUT", "update"),
        ApiEndpoint(None, None, "DELETE", "delete"),
      ],
    )
    self.conn.aiexperiments._sub_resources["training_runs"] = ApiResource(
      self.conn,
      "training_runs",
      endpoints=[
        ApiEndpoint(None, EnhancedInfoTrainingRun, "POST", "create"),
      ],
    )
    self.conn.aiexperiments._sub_resources["best_training_runs"] = ApiResource(
      self.conn,
      "best_training_runs",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(EnhancedInfoTrainingRun, *args, **kwargs), "GET", "fetch"),
      ],
    )

    training_runs = ApiResource(
      self.conn,
      "training_runs",
      endpoints=[
        ApiEndpoint(None, object_or_internal_paginated_objects(EnhancedInfoTrainingRun), "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoTrainingRun, "POST", "create"),
        ApiEndpoint(None, EnhancedInfoTrainingRun, "PUT", "update"),
        ApiEndpoint("batch", object_or_internal_paginated_objects(EnhancedInfoTrainingRun), "POST", "create_batch"),
      ],
    )
    self.conn.clients._sub_resources["projects"]._sub_resources["training_runs"] = training_runs

    # /sessions
    sessions = ApiResource(
      self.conn,
      "sessions",
      endpoints=[
        ApiEndpoint(None, EnhancedInfoSession, "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoSession, "POST", "create"),
        ApiEndpoint(None, EnhancedInfoSession, "PUT", "update"),
        ApiEndpoint(None, EnhancedInfoSession, "DELETE", "delete"),
      ],
    )
    self.conn.sessions = sessions

    # /training_runs
    training_runs = ApiResource(
      self.conn,
      "training_runs",
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(EnhancedInfoTrainingRun), "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoTrainingRun, "PUT", "update"),
        ApiEndpoint(None, EnhancedInfoTrainingRun, "MERGE", "merge"),
        ApiEndpoint(None, EnhancedInfoTrainingRun, "DELETE", "delete"),
      ],
    )
    self.conn.training_runs = training_runs
    self.conn.training_runs._sub_resources["checkpoints"] = self.conn.experiments._sub_resources[
      "training_runs"
    ]._sub_resources["checkpoints"]
    self.conn.training_runs._sub_resources["tags"] = ApiResource(
      self.conn,
      "tags",
      endpoints=[
        ApiEndpoint(None, Tag, "POST", "create"),
        ApiEndpoint(None, Tag, "DELETE", "delete"),
      ],
    )
    self.conn.training_runs._sub_resources["files"] = ApiResource(
      self.conn,
      "files",
      endpoints=[
        ApiEndpoint(None, File, "POST", "create"),
      ],
    )
    self.conn.files = ApiResource(
      self.conn,
      "files",
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(File), "GET", "fetch"),
      ],
    )

    # /experiments/X/metric_importances
    self.conn.experiments._sub_resources["metric_importances"] = ApiResource(
      self.conn,
      "metric_importances",
      endpoints=[
        ApiEndpoint(None, None, "PUT", "update"),
        ApiEndpoint(None, object_or_paginated_objects(MetricImportances), "GET", "fetch"),
      ],
    )

    # /experiments/X/hyperparameters
    self.conn.experiments._sub_resources["hyperparameters"] = ApiResource(
      self.conn,
      "hyperparameters",
      endpoints=[
        ApiEndpoint(None, None, "DELETE", "delete"),
      ],
    )

    # /experiments/X/best_practices
    self.conn.experiments._sub_resources["best_practices"] = ApiResource(
      self.conn,
      "best_practices",
      endpoints=[
        ApiEndpoint(None, ApiObject, "GET", "fetch"),
      ],
    )

    self.conn.experiments._sub_resources["best_training_runs"] = ApiResource(
      self.conn,
      "best_training_runs",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(TrainingRun, *args, **kwargs), "GET", "fetch"),
      ],
    )

    self.conn.clients._endpoints["fetch"] = ApiEndpoint(
      None,
      object_or_paginated_objects(Client),
      "GET",
      "fetch",
    )
    self.conn.clients._endpoints["create"] = ApiEndpoint(None, Client, "POST", "create")
    self.conn.clients._endpoints["update"] = ApiEndpoint(None, Client, "PUT", "update")
    self.conn.clients._endpoints["delete"] = ApiEndpoint(None, Client, "DELETE", "delete")

    # Web Data Endpoint
    web_data = ApiResource(
      self.conn,
      "web_data",
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(WebData), "GET", "fetch"),
        ApiEndpoint(None, WebData, "POST", "create"),
        ApiEndpoint(None, WebData, "PUT", "update"),
        ApiEndpoint(None, None, "DELETE", "delete"),
      ],
    )
    self.conn.web_data = web_data

    # /clients/X/permissions
    self.conn.clients._sub_resources["permissions"] = ApiResource(
      self.conn,
      "permissions",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Permission, *args, **kwargs), "GET", "fetch"),
      ],
    )

    self.conn.clients._sub_resources["invites"] = ApiResource(
      self.conn,
      "invites",
      endpoints=[
        # NOTE - Create endpoint returns PendingPermission because an Invite would be unusable by the client
        ApiEndpoint(None, PendingPermission, "POST", "create"),
        ApiEndpoint(None, None, "DELETE", "delete"),
      ],
    )

    self.conn.clients._sub_resources["merge"] = ApiResource(
      self.conn,
      "merge",
      endpoints=[
        ApiEndpoint(None, None, "PUT", "update"),
      ],
    )

    self.conn.clients._sub_resources["pending_permissions"] = ApiResource(
      self.conn,
      "pending_permissions",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(PendingPermission, *args, **kwargs), "GET", "fetch"),
      ],
    )

    self.conn.clients._sub_resources["experiments"]._endpoints["create"] = ApiEndpoint(
      None,
      Experiment,
      "POST",
      "create",
    )

    self.conn.clients._sub_resources["experiments"]._endpoints["update"] = ApiEndpoint(
      None,
      Experiment,
      "PUT",
      "update",
    )

    self.conn.clients._sub_resources["experiments"]._endpoints["fetch"] = ApiEndpoint(
      None,
      object_or_paginated_objects(Experiment),
      "GET",
      "fetch",
    )

    user_experiments = ApiResource(
      self.conn,
      "experiments",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Experiment, *args, **kwargs), "GET", "fetch"),
      ],
    )

    user_pending_permissions = ApiResource(
      self.conn,
      "pending_permissions",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(PendingPermission, *args, **kwargs), "GET", "fetch"),
      ],
    )

    user_permissions = ApiResource(
      self.conn,
      "permissions",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Permission, *args, **kwargs), "GET", "fetch"),
        ApiEndpoint(None, Permission, "POST", "create"),
      ],
    )

    user_memberships = ApiResource(
      self.conn,
      "memberships",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Membership, *args, **kwargs), "GET", "fetch"),
      ],
    )

    user_tokens = ApiResource(
      self.conn,
      "tokens",
      endpoints=[
        ApiEndpoint(None, EnhancedInfoToken, "GET", "fetch"),
      ],
    )

    verifications = ApiResource(
      self.conn,
      "verifications",
      endpoints=[
        ApiEndpoint(None, None, "POST", "create"),
      ],
    )
    self.conn.verifications = verifications

    # Users
    users = ApiResource(
      self.conn,
      "users",
      resources=[
        user_experiments,
        user_pending_permissions,
        user_permissions,
        user_memberships,
        user_tokens,
        sessions,
        verifications,
      ],
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(EnhancedInfoUser), "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoUser, "POST", "create"),
        ApiEndpoint(None, EnhancedInfoUser, "PUT", "update"),
        ApiEndpoint(None, EnhancedInfoUser, "DELETE", "delete"),
      ],
    )
    self.conn.users = users
    self.conn.clients._sub_resources["users"] = users

    # /tokens
    tokens = ApiResource(
      self.conn,
      "tokens",
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(EnhancedInfoToken), "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoToken, "POST", "create"),
        ApiEndpoint(None, EnhancedInfoToken, "DELETE", "delete"),
        ApiEndpoint(None, EnhancedInfoToken, "PUT", "update"),
      ],
    )
    self.conn.tokens = tokens
    self.conn.clients._sub_resources["tokens"] = tokens
    self.conn.experiments._sub_resources["tokens"] = tokens
    training_runs._sub_resources["tokens"] = tokens

    # /organizations
    organization_memberships = ApiResource(
      self.conn,
      "memberships",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Membership, *args, **kwargs), "GET", "fetch"),
      ],
    )

    organization_clients = ApiResource(
      self.conn,
      "clients",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Client, *args, **kwargs), "GET", "fetch"),
        ApiEndpoint(None, Client, "POST", "create"),
      ],
    )

    organization_invites = ApiResource(
      self.conn,
      "invites",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Invite, *args, **kwargs), "GET", "fetch"),
        ApiEndpoint(None, Invite, "POST", "create"),
        ApiEndpoint(None, Invite, "PUT", "update"),
        ApiEndpoint(None, None, "DELETE", "delete"),
      ],
    )

    organization_experiments = ApiResource(
      self.conn,
      "experiments",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Experiment, *args, **kwargs), "GET", "fetch"),
      ],
    )

    organization_permissions = ApiResource(
      self.conn,
      "permissions",
      endpoints=[
        ApiEndpoint(None, lambda *args, **kwargs: Pagination(Permission, *args, **kwargs), "GET", "fetch"),
      ],
    )

    organizations = ApiResource(
      self.conn,
      "organizations",
      resources=[
        organization_clients,
        organization_memberships,
        organization_invites,
        organization_experiments,
        organization_permissions,
      ],
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(EnhancedInfoOrganization), "GET", "fetch"),
        ApiEndpoint(None, EnhancedInfoOrganization, "POST", "create"),
        ApiEndpoint(None, EnhancedInfoOrganization, "PUT", "update"),
        ApiEndpoint(None, EnhancedInfoOrganization, "DELETE", "delete"),
      ],
    )

    self.conn.organizations = organizations

    self.conn.all_experiments = ApiResource(
      self.conn,
      "all_experiments",
      endpoints=[
        ApiEndpoint(None, object_or_paginated_objects(Experiment), "GET", "fetch"),
      ],
    )

  def __getattr__(self, name):
    return getattr(self.conn, name)

  def set_api_url(self, api_url):
    self.conn.set_api_url(api_url)

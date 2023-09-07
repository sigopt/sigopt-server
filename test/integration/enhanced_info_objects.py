# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigopt.objects import (
  ApiObject,
  Assignments,
  Client,
  Conditional,
  Field,
  LinearConstraint,
  ListOf,
  Metadata,
  Metric,
  Organization,
  Pagination,
  Parameter,
  Session,
  Token,
  TrainingRun,
  User,
  _DictWrapper,
)


def object_or_internal_paginated_objects(api_object):
  def decorator(body, *args, **kwargs):
    if body.get("object") == "pagination":
      return EnhancedInfoPagination(api_object, body, *args, **kwargs)
    return api_object(body, *args, **kwargs)

  return decorator


class DefinedFields(ApiObject):
  key = Field(str)
  count = Field(int)


class EnhancedInfoPagination(Pagination):
  defined_fields = Field(ListOf(DefinedFields))


class EnhancedInfoToken(Token):
  lease_length = Field(int)
  training_run = Field(str)


class EnhancedInfoTrainingRun(TrainingRun):
  # TODO: Give datasets, logs and values better types, would require an ObjectOf
  # TODO: some of these redefine types but it's unclear why
  datasets = Field(Assignments)
  favorite = Field(bool)
  logs = Field(Assignments)
  tags = Field(list)
  values = Field(Assignments)


# TODO: already covered in `Progress` public object, but in process of forking
class EnhancedInfoRunsProgress(ApiObject):
  active_run_count = Field(int)
  finished_run_count = Field(int)
  total_run_count = Field(int)
  remaining_budget = Field(float)


# TODO: after sigopt-python adds `AiExperiment` object, can inherit more cleanly
class EnhancedInfoAiExperiment(ApiObject):
  budget = Field(float)
  client = Field(str)
  conditionals = Field(ListOf(Conditional))
  created = Field(int)
  id = Field(str)
  linear_constraints = Field(ListOf(LinearConstraint))
  metadata = Field(Metadata)
  metrics = Field(ListOf(Metric))
  name = Field(str)
  num_solutions = Field(int)
  observation_budget = Field(int)
  parallel_bandwidth = Field(int)
  parameters = Field(ListOf(Parameter))
  progress = Field(EnhancedInfoRunsProgress)
  project = Field(str)
  state = Field(str)
  updated = Field(int)
  user = Field(str)


class PendingPermission(ApiObject):
  client = Field(str)
  client_name = Field(str)
  email = Field(str)
  invite_code = Field(str)
  role = Field(str)


class Invite(ApiObject):
  id = Field(str)
  email = Field(str)
  invite_code = Field(str)
  membership_type = Field(str)
  organization = Field(str)
  organization_name = Field(str)
  pending_permissions = Field(ListOf(PendingPermission))


class EnhancedInfoOrganization(Organization):
  allow_signup_from_email_domains = Field(bool)
  client_for_email_signup = Field(str)
  email_domains = Field(ListOf(str))


class EnhancedInfoUser(User):
  educational_user = Field(bool)
  has_verified_email = Field(bool)


class Membership(ApiObject):
  organization = Field(Organization)
  type = Field(str)
  user = Field(EnhancedInfoUser)


class Permission(ApiObject):
  client = Field(Client)
  role = Field(str)
  user = Field(EnhancedInfoUser)
  can_admin = Field(bool)
  can_write = Field(bool)
  can_read = Field(bool)
  is_owner = Field(bool)


class EnhancedInfoSession(Session):
  api_token = Field(EnhancedInfoToken)  # override
  code = Field(str)
  needs_password_reset = Field(bool)
  user = Field(EnhancedInfoUser)  # override


class DynamicData(_DictWrapper):
  pass


class WebData(ApiObject):
  id = Field(str)
  created = Field(int)
  created_by = Field(str)
  display_name = Field(str)
  parent_resource_id = Field(DynamicData)
  parent_resource_type = Field(str)
  payload = Field(DynamicData)
  updated = Field(int)
  web_data_type = Field(str)


class Note(ApiObject):
  contents = Field(str)
  created = Field(int)
  user = Field(str)


class ProjectNote(Note):
  client = Field(str)
  project = Field(str)


class Tag(ApiObject):
  id = Field(str)
  client = Field(str)
  name = Field(str)
  color = Field(str)


class UploadInfo(ApiObject):
  headers = Field(dict)
  method = Field(str)
  url = Field(str)


class DownloadInfo(ApiObject):
  url = Field(str)


class File(ApiObject):
  client = Field(str)
  content_length = Field(int)
  content_md5 = Field(str)
  content_type = Field(str)
  download = Field(DownloadInfo)
  filename = Field(str)
  id = Field(str)
  name = Field(str)
  upload = Field(UploadInfo)

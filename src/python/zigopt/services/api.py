# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=attribute-defined-outside-init

from zigopt.common import *
from zigopt.best_practices.service import BestPracticesService
from zigopt.checkpoint.service import CheckpointService
from zigopt.client.service import ClientService
from zigopt.db.service import DatabaseConnectionService, DatabaseService
from zigopt.email.list import EmailTemplates
from zigopt.email.queue import EmailQueueService
from zigopt.email.router import EmailRouterService
from zigopt.email.sender import EmailSenderService
from zigopt.email.smtp import SmtpEmailService
from zigopt.exception.logger import ExceptionLogger
from zigopt.experiment.best import ExperimentBestObservationService
from zigopt.experiment.progress import ExperimentProgressService
from zigopt.experiment.segmenter import ExperimentParameterSegmenter
from zigopt.experiment.service import ExperimentService
from zigopt.file.s3_user_upload_service import S3UserUploadService
from zigopt.file.service import FileService
from zigopt.iam_logging.service import IamLoggingService
from zigopt.importance.service import ImportancesService
from zigopt.invite.service import InviteService
from zigopt.log.service import LoggingService
from zigopt.membership.service import MembershipService
from zigopt.message_tracking.service import MessageTrackingService
from zigopt.note.service import NoteService
from zigopt.observation.service import ObservationService
from zigopt.optimization_aux.service import PostgresAuxService
from zigopt.optimize.optimizer import OptimizerService
from zigopt.optimize.queue import OptimizeQueueService
from zigopt.organization.service import OrganizationService
from zigopt.pagination.query import QueryPager
from zigopt.permission.pending.service import PendingPermissionService
from zigopt.permission.service import PermissionService
from zigopt.project.service import ProjectService
from zigopt.queue.base import BaseQueueService
from zigopt.queue.grouper import QueueMessageGrouper
from zigopt.queue.local import LocalQueueService
from zigopt.queue.monitor import QueueMonitor
from zigopt.queue.providers import make_providers
from zigopt.queue.router import MessageRouter
from zigopt.queue.service import QueueService
from zigopt.queued_suggestion.service import QueuedSuggestionService
from zigopt.ratelimit.service import RateLimiter
from zigopt.redis.service import RedisKeyService, RedisService
from zigopt.services.bag import RequestLocalServiceBag, ServiceBag
from zigopt.services.disabled import DisabledService
from zigopt.sigoptcompute.adapter import SCAdapter
from zigopt.suggestion.broker.queued import SuggestionBroker
from zigopt.suggestion.processed.service import ProcessedSuggestionService
from zigopt.suggestion.ranker import SuggestionRanker
from zigopt.suggestion.service import SuggestionService
from zigopt.suggestion.unprocessed.service import UnprocessedSuggestionService
from zigopt.tag.service import TagService
from zigopt.token.service import TokenService
from zigopt.training_run.service import TrainingRunService
from zigopt.user.email_verification_service import EmailVerificationService
from zigopt.user.service import UserService
from zigopt.web_data.service import WebDataService


class ApiServiceBag(ServiceBag):
  queue_service: BaseQueueService
  s3_user_upload_service: S3UserUploadService | DisabledService

  def __init__(self, config_broker, is_qworker):
    self.is_qworker = is_qworker
    super().__init__(config_broker)

  def _create_services(self, config_broker):
    super()._create_services(config_broker)
    self.database_connection_service = DatabaseConnectionService(self)
    self.email_queue_service = EmailQueueService(self)
    self.email_router = EmailRouterService(self, is_qworker=self.is_qworker)
    self.exception_logger = ExceptionLogger(self)
    self.immediate_email_sender = EmailSenderService(self)
    self.logging_service = LoggingService(self)
    self.message_router = MessageRouter(self)
    self.message_tracking_service = MessageTrackingService(self)
    self.queue_message_grouper = QueueMessageGrouper(self)
    self.rate_limiter = RateLimiter(self)
    self.redis_service = RedisService(self)
    self.redis_key_service = RedisKeyService(self)
    self.smtp_email_service = SmtpEmailService(self)

    queue_type = self.config_broker.get("queue.type", default="async")
    if queue_type == "sync":
      self.queue_service = LocalQueueService(self, request_local_cls=ApiRequestLocalServiceBag)
    else:
      self.queue_service = QueueService(self, make_providers(self))

    if self.is_qworker:
      self.s3_user_upload_service = DisabledService(self)
    else:
      self.s3_user_upload_service = S3UserUploadService(self)

  def _warmup_services(self):
    super()._warmup_services()
    self._db_connection = self.database_connection_service.warmup_db()
    self.queue_service.warmup()
    self.redis_service.warmup()

  @classmethod
  def from_config_broker(cls, config_broker, is_qworker=False):
    return cls(config_broker, is_qworker)


class ApiRequestLocalServiceBag(RequestLocalServiceBag):
  def __init__(self, underlying, request=None):
    super().__init__(underlying, request=None)
    self.best_practices_service = BestPracticesService(self)
    self.checkpoint_service = CheckpointService(self)
    self.client_service = ClientService(self)
    self.database_service = DatabaseService(self, self._db_connection)
    self.email_templates = EmailTemplates(self)
    self.email_verification_service = EmailVerificationService(self)
    self.experiment_best_observation_service = ExperimentBestObservationService(self)
    self.experiment_parameter_segmenter = ExperimentParameterSegmenter(self)
    self.experiment_progress_service = ExperimentProgressService(self)
    self.experiment_service = ExperimentService(self)
    self.iam_logging_service = IamLoggingService(self)
    self.importances_service = ImportancesService(self)
    self.invite_service = InviteService(self)
    self.membership_service = MembershipService(self)
    self.sc_adapter = SCAdapter(self)
    self.note_service = NoteService(self)
    self.observation_service = ObservationService(self)
    self.optimize_queue_service = OptimizeQueueService(self)
    self.optimizer = OptimizerService(self)
    self.organization_service = OrganizationService(self)
    self.pending_permission_service = PendingPermissionService(self)
    self.permission_service = PermissionService(self)
    self.aux_service = PostgresAuxService(self)
    self.processed_suggestion_service = ProcessedSuggestionService(self)
    self.project_service = ProjectService(self)
    self.query_pager = QueryPager(self)
    self.queue_monitor = QueueMonitor(self)
    self.queued_suggestion_service = QueuedSuggestionService(self)
    self.suggestion_broker = SuggestionBroker(self)
    self.suggestion_ranker = SuggestionRanker(self)
    self.suggestion_service = SuggestionService(self)
    self.tag_service = TagService(self)
    self.file_service = FileService(self)
    self.token_service = TokenService(self)
    self.training_run_service = TrainingRunService(self)
    self.unprocessed_suggestion_service = UnprocessedSuggestionService(self)
    self.user_service = UserService(self)
    self.web_data_service = WebDataService(self)

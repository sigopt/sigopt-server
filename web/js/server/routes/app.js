/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import AiExperimentAnalysisEndpoint from "../../pages/experiment/ai/analysis/endpoint";
import AiExperimentApiEndpoint from "../../pages/experiment/ai/api/endpoint";
import AiExperimentHistoryEndpoint from "../../pages/experiment/ai/history/endpoint";
import AiExperimentInformOptimizerEndpoint from "../../pages/experiment/ai/inform/endpoint";
import AiExperimentListEndpoint from "../../pages/aiexperiment/list/endpoint";
import AiExperimentPropertiesEndpoint from "../../pages/experiment/ai/properties/endpoint";
import AiExperimentViewEndpoint from "../../pages/experiment/ai/view/endpoint";
import ChangePasswordEndpoint from "../../pages/change_password/endpoint";
import ClientCreateEndpoint from "../../pages/client/create/endpoint";
import ClientDeleteEndpoint from "../../pages/client/delete/endpoint";
import DebugEndpoint from "../../pages/debug/endpoint";
import DecryptCookieEndpoint from "../endpoint/cookie";
import EmailVerifyEndpoint from "../../pages/email_verify/endpoint";
import ExperimentAdminEndpoint from "../../pages/experiment/admin/endpoint";
import ExperimentAnalysisEndpoint from "../../pages/experiment/core/analysis/endpoint";
import ExperimentApiEndpoint from "../../pages/experiment/core/api/endpoint";
import ExperimentCopyEndpoint from "../../pages/experiment/core/copy/endpoint";
import ExperimentCreateEndpoint from "../../pages/experiment/common/create/endpoint";
import ExperimentHistoryDownloadEndpoint from "../../pages/experiment/core/bulkdownload/endpoint";
import ExperimentHistoryEndpoint from "../../pages/experiment/core/history/endpoint";
import ExperimentListEndpoint from "../../pages/experiment/list/endpoint";
import ExperimentPropertiesEndpoint from "../../pages/experiment/core/properties/endpoint";
import ExperimentReportEndpoint from "../../pages/experiment/core/report/endpoint";
import ExperimentReportFileEndpoint from "../../pages/experiment/core/bulkupload/endpoint";
import ExperimentResetEndpoint from "../../pages/experiment/core/reset/endpoint";
import ExperimentSuggestionsEndpoint from "../../pages/experiment/core/suggestions/endpoint";
import ExperimentViewEndpoint from "../../pages/experiment/core/view/endpoint";
import ForgotPasswordEndpoint from "../../pages/forgot_password/endpoint";
import GuestEndpoint from "../../pages/guest/endpoint";
import HomeEndpoint from "../../pages/home/endpoint";
import LoginEndpoint from "../../pages/landing/login/endpoint";
import LogoutEndpoint from "../../pages/landing/logout";
import ObservationToRunRedirect from "../redirects/observation_to_run";
import OrganizationExperimentsEndpoint from "../../pages/organization/experiments/endpoint";
import OrganizationRunsEndpoint from "../../pages/organization/runs/endpoint";
import OrganizationTeamsEndpoint from "../../pages/organization/teams/endpoint";
import OrganizationUserDetailsEndpoint from "../../pages/organization/users/user/endpoint";
import OrganizationUsersEndpoint from "../../pages/organization/users/endpoint";
import PopSessionEndpoint from "../../pages/session/pop";
import ProjectAiExperimentsEndpoint from "../../pages/project/experiments/endpoint";
import ProjectAnalysisEndpoint from "../../pages/project/analysis/endpoint";
import ProjectNotesEndpoint from "../../pages/project/notes/endpoint";
import ProjectOverviewEndpoint from "../../pages/project/overview/endpoint";
import ProjectRunsEndpoint from "../../pages/project/runs/endpoint";
import ProjectsEndpoint from "../../pages/projects/endpoint";
import PushSessionEndpoint from "../../pages/session/push";
import SetupEndpoint from "../../pages/setup/endpoint";
import SicknessEndpoint from "../../pages/error/sickness";
import SignUpEndpoint from "../../pages/signup/endpoint";
import TokenDashboardEndpoint from "../../pages/token_dashboard/endpoint";
import TokenInfoEndpoint from "../../pages/token_info/endpoint";
import TrainingRunViewEndpoint from "../../pages/training_run/view/endpoint";
import UserDeleteEndpoint from "../../pages/user/delete/endpoint";
import UserProfileEndpoint from "../../pages/user_profile/endpoint";
import {redirectTo, replaceWith} from "./lib";

const aiExperimentRoutes = {
  "/aiexperiment/:aiExperimentId": new AiExperimentViewEndpoint(),
  "/aiexperiment/:aiExperimentId/analysis": new AiExperimentAnalysisEndpoint(),
  "/aiexperiment/:aiExperimentId/history": new AiExperimentHistoryEndpoint(),
  "/aiexperiment/:aiExperimentId/inform":
    new AiExperimentInformOptimizerEndpoint(),
  "/aiexperiment/:aiExperimentId/properties":
    new AiExperimentPropertiesEndpoint(),
  "/aiexperiment/:aiExperimentId/observation/:observationId/run":
    new ObservationToRunRedirect(),
  "/aiexperiment/:experimentId/api": new AiExperimentApiEndpoint(),
  "/aiexperiment/:experimentId/admin": new ExperimentAdminEndpoint(),
};

const coreExperimentRoutes = {
  "/experiment/:experimentId": new ExperimentViewEndpoint(),
  "/experiment/:experimentId/analysis": new ExperimentAnalysisEndpoint(),
  "/experiment/:experimentId/api": new ExperimentApiEndpoint(),
  "/experiment/:experimentId/copy": new ExperimentCopyEndpoint(),
  "/experiment/:experimentId/history": new ExperimentHistoryEndpoint(),
  "/experiment/:experimentId/historydownload":
    new ExperimentHistoryDownloadEndpoint(),
  "/experiment/:experimentId/properties": new ExperimentPropertiesEndpoint(),
  "/experiment/:experimentId/report": new ExperimentReportEndpoint(),
  "/experiment/:experimentId/report/file": new ExperimentReportFileEndpoint(),
  "/experiment/:experimentId/reset": new ExperimentResetEndpoint(),
  "/experiment/:experimentId/suggestions": new ExperimentSuggestionsEndpoint(),
  "/experiment/:experimentId/observation/:observationId/run":
    new ObservationToRunRedirect(),
  "/experiment/:experimentId/admin": new ExperimentAdminEndpoint(),
};

/**
 * Used for logged-in pages that engage with the API.
 */
export default function appRoutes(configBroker) {
  const ConfigLoginEndpoint = LoginEndpoint;

  const experimentDetailRoutes = _.extend(
    {},
    aiExperimentRoutes,
    coreExperimentRoutes,
  );

  const routes = _.extend({}, experimentDetailRoutes, {
    "/": redirectTo("/login"),
    "/aiexperiments": new AiExperimentListEndpoint(),
    "/change_password": new ChangePasswordEndpoint(),
    "/client/:clientId/delete": new ClientDeleteEndpoint(),
    "/client/:clientId/project/:projectId": redirectTo(
      (req) =>
        `/client/${req.matchedProject.client}/project/${req.matchedProject.id}/overview`,
    ),
    "/client/:clientId/project/:projectId/analysis":
      new ProjectAnalysisEndpoint(),
    "/client/:clientId/project/:projectId/experiments": redirectTo(
      (req) =>
        `/client/${req.matchedProject.client}/project/${req.matchedProject.id}/aiexperiments`,
    ),
    "/client/:clientId/project/:projectId/aiexperiments":
      new ProjectAiExperimentsEndpoint(),
    "/client/:clientId/project/:projectId/notes": new ProjectNotesEndpoint(),
    "/client/:clientId/project/:projectId/overview":
      new ProjectOverviewEndpoint(),
    "/client/:clientId/project/:projectId/runs": new ProjectRunsEndpoint(),
    "/client/:clientId/tokens": new TokenDashboardEndpoint(),
    "/clients/create": new ClientCreateEndpoint(),
    "/debug": new DebugEndpoint(),
    "/experiments": new ExperimentListEndpoint(),
    "/experiments/create": new ExperimentCreateEndpoint(),
    "/forgot_password": new ForgotPasswordEndpoint(),
    "/guest": new GuestEndpoint(),
    "/home": new HomeEndpoint(),
    "/industries": replaceWith("/industries/banking"),
    "/log_in": replaceWith("/login"),
    "/log_out": replaceWith("/logout"),
    "/login": new ConfigLoginEndpoint(),
    "/login_password": new LoginEndpoint(),
    "/logout": new LogoutEndpoint(),
    "/nsickness": new SicknessEndpoint(),
    "/organization": replaceWith("/organization/users"),
    "/organization/:organizationId": new OrganizationUsersEndpoint(),
    "/organization/:organizationId/experiments":
      new OrganizationExperimentsEndpoint(),
    "/organization/:organizationId/runs": new OrganizationRunsEndpoint(),
    "/organization/:organizationId/teams": new OrganizationTeamsEndpoint(),
    "/organization/:organizationId/users": new OrganizationUsersEndpoint(),
    "/organization/:organizationId/users/:userId":
      new OrganizationUserDetailsEndpoint(),
    "/pop_session": new PopSessionEndpoint(),
    "/project/:projectId": redirectTo(
      (req) => `/client/${req.matchedProject.client}${req.path}/overview`,
    ),
    "/project/:projectId/:page": redirectTo(
      (req) => `/client/${req.matchedProject.client}${req.path}`,
    ),
    "/projects": new ProjectsEndpoint(),
    "/push_session": new PushSessionEndpoint(),
    "/setup": new SetupEndpoint(),
    "/signup": new SignUpEndpoint(),
    "/run/:trainingRunId": new TrainingRunViewEndpoint(),
    "/tokens/info": new TokenInfoEndpoint(),
    "/tokens/manage": new TokenDashboardEndpoint(),
    "/user/i_want_to_delete_my_account": new UserDeleteEndpoint(),
    "/user/info": new UserProfileEndpoint(),
    "/verify": new EmailVerifyEndpoint(),
  });

  if (
    process.env.ALLOW_DECRYPT_COOKIE_ENDPOINT &&
    configBroker.get("web.enable_decrypt_cookie_endpoint")
  ) {
    routes["/cookie"] = new DecryptCookieEndpoint();
  }

  return routes;
}

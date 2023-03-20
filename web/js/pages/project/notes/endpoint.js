/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ProjectEndpoint from "../server/endpoint";

export default class ProjectNotesEndpoint extends ProjectEndpoint {
  pageName() {
    return "Notes";
  }

  static page = require("./page");

  _fetchLatestNote(clientId, projectId) {
    return this.services.promiseApiClient
      .clients(clientId)
      .projects(projectId)
      .notes()
      .fetch()
      .then((notesPage) => notesPage.data[0]);
  }

  parseParams(req) {
    const {client: clientId, id: projectId} = req.matchedProject;

    return this._fetchLatestNote(clientId, projectId).then((note) => ({note}));
  }
}

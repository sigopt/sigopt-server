/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/project_notes_page.less";

import React from "react";

// eslint-disable-next-line import/no-named-as-default
import NotesEditor from "../../../component/notes_editor";
import ProjectPage from "../page_wrapper";

export default class ProjectNotes extends React.Component {
  handleSubmit = (note) => {
    const {client: clientId, id: projectId} = this.props.project;
    return this.props.promiseApiClient
      .clients(clientId)
      .projects(projectId)
      .notes()
      .create(note);
  };

  render() {
    const {note, ...props} = this.props;
    return (
      <ProjectPage {...props}>
        <div className="project-notes-page">
          <NotesEditor
            currentUser={props.currentUser}
            note={note}
            onSubmit={this.handleSubmit}
          />
        </div>
      </ProjectPage>
    );
  }
}

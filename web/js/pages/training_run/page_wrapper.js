/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import classNames from "classnames";

import Component from "../../react/component";
import PageBody from "../../component/page_body";
import PageTitle from "../../component/page_title";
import TagEditor from "../../tag/editor";
import {Duration} from "../../render/format_times";
import {statusGlyphs} from "./constants";

const RunStatus = ({run}) => {
  const Glyph = statusGlyphs[run.state];
  return (
    <span className={classNames("run-status", run.state)}>
      <Glyph /> {run.state}
    </span>
  );
};

export default class TrainingRunPage extends Component {
  constructor(props) {
    super(props);
    this.state = {
      run: this.props.trainingRun,
      tags: this.props.tags,
    };
  }

  extendTagsState = (tag, cb) => {
    this.setState(
      ({tags}) => ({tags: _.extend({}, tags, {[tag.id]: tag})}),
      cb,
    );
  };

  onCreateTag = (tagData) =>
    this.services.promiseApiClient
      .clients(this.state.run.client)
      .tags()
      .create({color: tagData.color, name: tagData.name})
      .then(
        (newTag) =>
          new Promise((cb) => this.extendTagsState(newTag, () => cb(newTag))),
      );

  onApplyTag = (tag) =>
    this.services.promiseApiClient
      .trainingRuns(this.state.run.id)
      .tags()
      .create({id: tag.id})
      .then(this.applyTagToRun);

  onRemoveTag = (tag) =>
    this.services.promiseApiClient
      .trainingRuns(this.state.run.id)
      .tags(tag.id)
      .delete()
      .then(this.removeTagFromRun);

  applyTagToRun = (newTag) => {
    this.setState(({run}) => ({
      run: _.extend({}, run, {tags: run.tags.concat([newTag.id])}),
    }));
  };

  removeTagFromRun = (tag) => {
    this.setState(({run}) => ({
      run: _.extend({}, run, {tags: _.without(run.tags, tag.id)}),
    }));
  };

  reloadTags = () => {
    this.services.promiseApiClient
      .clients(this.state.run.client)
      .tags()
      .exhaustivelyPage()
      .then((tags) => this.setState({tags: _.indexBy(tags, "id")}));
    this.services.promiseApiClient
      .trainingRuns(this.state.run.id)
      .fetch()
      .then(({tags}) => this.setState(({run}) => ({run: {...run, tags}})));
  };

  render() {
    const run = this.state.run || this.props.trainingRun;
    const breadcrumbs = [];
    if (this.props.showBreadcrumbs) {
      breadcrumbs.push({href: "/projects", label: "Projects"});
      if (this.props.project && this.props.project.id) {
        breadcrumbs.push({
          href: `/client/${this.props.project.client}/project/${this.props.project.id}`,
          label: this.props.project.name,
        });
        breadcrumbs.push({
          href: `/client/${this.props.project.client}/project/${this.props.project.id}/runs`,
          label: "Runs",
        });
      }
    }
    return (
      <div className="run-page">
        <PageTitle
          gradientStyle="run"
          info={
            <>
              <dt>Status</dt>
              <dd>
                <RunStatus run={run} />
              </dd>
              <dt>Runtime</dt>
              <dd>
                <Duration
                  startTime={run.created}
                  endTime={run.completed || new Date().getTime() / 1000}
                />
              </dd>
              {this.props.tags ? (
                <>
                  <dt>Tags</dt>
                  <dd>
                    <TagEditor
                      tags={this.state.tags}
                      selectedTagIds={run.tags}
                      onApplyTag={this.onApplyTag}
                      onRemoveTag={this.onRemoveTag}
                      onCreateTag={this.onCreateTag}
                      reloadTags={this.reloadTags}
                    />
                  </dd>
                </>
              ) : null}
            </>
          }
          breadcrumbs={breadcrumbs}
          title={this.props.trainingRun.name}
        />
        <PageBody>{this.props.children}</PageBody>
      </div>
    );
  }
}

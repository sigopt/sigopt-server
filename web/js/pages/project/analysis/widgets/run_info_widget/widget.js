/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import Component from "../../../../../react/component";
import Section from "../../../../../component/section";
import TagEditor from "../../../../../tag/editor";
import {Content as MetadataContent} from "../../../../training_run/view/metadata";
import {Content as MetricContent} from "../../../../training_run/view/metric";
import {Content as ParameterContent} from "../../../../training_run/view/parameter";
import {createTag, fetchTags, modifyRun} from "../../../state/dimensions_slice";

class CollapsableSection extends React.Component {
  state = {collapsed: true};

  setCollapsed = (collapsed) => this.setState({collapsed});

  render() {
    return (
      <Section
        fullWidth={true}
        title={this.props.title}
        collapsable={true}
        collapsed={this.state.collapsed}
        setCollapsed={this.setCollapsed}
      >
        {this.props.children}
      </Section>
    );
  }
}

class RunInfoTagEditor extends Component {
  onApplyTag = (tag) => {
    const runId = this.props.run.id;
    return this.services.promiseApiClient
      .trainingRuns(runId)
      .tags()
      .create({id: tag.id})
      .then(() => {
        this.props.modifyRun(runId, (run) =>
          _.extend({}, run, {tags: _.uniq(run.tags.concat([tag.id]))}),
        );
      });
  };

  onRemoveTag = (tag) => {
    const runId = this.props.run.id;
    return this.services.promiseApiClient
      .trainingRuns(runId)
      .tags(tag.id)
      .delete()
      .then(() => {
        this.props.modifyRun(runId, (run) =>
          _.extend({}, run, {tags: _.without(run.tags, tag.id)}),
        );
      });
  };

  onCreateTag = (tag) =>
    new Promise((success, error) => {
      this.props.createTag(tag, success, error);
    });

  render() {
    return (
      <TagEditor
        key={this.props.run.id}
        addTagsHintExpand={true}
        tags={this.props.tags}
        selectedTagIds={this.props.run.tags}
        onApplyTag={this.onApplyTag}
        onRemoveTag={this.onRemoveTag}
        onCreateTag={this.props.createTag}
        reloadTags={this.props.fetchTags}
      />
    );
  }
}

class RunInfoWidget extends React.Component {
  createTag = (tagData) =>
    new Promise((success, error) => {
      this.props.createTag(tagData, success, error);
    });

  render() {
    const run = this.props.runs[this.props.hoverId];
    return run ? (
      <div className="run-info widget">
        <div className="run-name">
          <a href={`/run/${run.id}`} target="_blank" rel="noopener noreferrer">
            <h1>{run.name}</h1>
          </a>
        </div>
        <RunInfoTagEditor
          run={run}
          tags={this.props.tags}
          createTag={this.createTag}
          modifyRun={this.props.modifyRun}
          fetchTags={this.props.fetchTags}
        />
        {!_.isEmpty(run.values) && (
          <CollapsableSection title="Metrics">
            <MetricContent trainingRun={run} />
          </CollapsableSection>
        )}
        {!_.isEmpty(run.assignments) && (
          <CollapsableSection title="Parameters">
            <ParameterContent trainingRun={run} />
          </CollapsableSection>
        )}
        {!_.isEmpty(run.metadata) && (
          <CollapsableSection title="Metadata">
            <MetadataContent trainingRun={run} />
          </CollapsableSection>
        )}
      </div>
    ) : (
      <p>Hover over a run to see details</p>
    );
  }
}

const mapDispatchToProps = {
  createTag,
  fetchTags,
  modifyRun,
};

const mapStateToProps = (state) => ({
  hoverId: state.dimensions.hoverInfo.runId,
  runs: state.dimensions.runsById,
  tags: state.dimensions.tagsById,
});

export const ConnectedRunInfoWidget = connect(
  mapStateToProps,
  mapDispatchToProps,
)(RunInfoWidget);

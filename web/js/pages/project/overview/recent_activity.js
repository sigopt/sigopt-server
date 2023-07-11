/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import ArrowTurnUpGlyph from "../../../component/glyph/arrow-turn-up";
import AsynchronousUserName from "../../../user/name_span";
import CertificateGlyph from "../../../component/glyph/certificate";
import CircleExclamationGlyph from "../../../component/glyph/circle-exclamation";
import ClockGlyph from "../../../component/glyph/clock";
import FlagCheckeredGlyph from "../../../component/glyph/flag-checkered";
import {AbsoluteTime, Duration} from "../../../render/format_times";
import {isDefinedAndNotNull} from "../../../utils";

const getLinkForAction = (action) => {
  const createPaths = {
    experiment: (o) => `/experiment/${o.id}`,
    project: (o) => `/project/${o.id}`,
    run: (o) => `/run/${o.id}`,
  };
  return createPaths[action.for](action.object);
};

const actionForDisplay = {
  experiment: "Experiment",
  project: "Project",
  run: "Run",
};

const actionTypeDisplay = {
  complete: "completed",
  create: "created",
  fail: "failed",
  update: "updated",
};

const actionTypeGlyph = {
  complete: <FlagCheckeredGlyph />,
  create: <CertificateGlyph />,
  fail: <CircleExclamationGlyph />,
  update: <ArrowTurnUpGlyph />,
};

const ActionView = ({action, userDataSources}) => (
  <div className="action-view">
    <div className="action-type-indicator">{actionTypeGlyph[action.type]}</div>
    <div className="action-text">
      <div className="action-description">
        {actionForDisplay[action.for]} {actionTypeDisplay[action.type]}
      </div>
      <div className="action-info">
        {isDefinedAndNotNull(action.duration) && (
          <>
            <ClockGlyph />{" "}
            <Duration
              startTime={action.duration.start}
              endTime={action.duration.end}
            />{" "}
            &bull;{" "}
          </>
        )}
        <AbsoluteTime time={action.time} /> &bull;{" "}
        <a href={getLinkForAction(action)}>{action.object.name}</a>
        {action.by ? (
          <>
            {" "}
            &bull;{" "}
            <AsynchronousUserName dataSource={userDataSources.get(action.by)} />
          </>
        ) : null}
      </div>
    </div>
  </div>
);

export default class RecentActivity extends React.Component {
  render() {
    return (
      <div className="recent-activity">
        {_.map(this.props.actions, (action) => (
          <ActionView
            action={action}
            key={action.key}
            userDataSources={this.props.userDataSources}
          />
        ))}
      </div>
    );
  }
}

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./task.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas";
import ui from "./ui";
import {Section} from "./section";
import {TaskInput} from "./input.js";

export class TaskView extends React.Component {
  static propTypes = {
    creating: PropTypes.bool,
    onChange: PropTypes.func,
    submitting: PropTypes.bool,
    task: schemas.Task.isRequired,
    taskList: PropTypes.arrayOf(schemas.Task).isRequired,
  };

  onTaskChange = (event) => {
    const newTask = _.find(
      this.props.taskList,
      (t) => t.name === event.target.value,
    );
    this.props.onChange(newTask);
  };

  render() {
    return (
      <div className="task-view">
        <div className="field-name">Task</div>
        {this.props.creating ? (
          <div className="input-value">
            <TaskInput
              className="form-control value data-input"
              currentTask={this.props.task}
              tasks={this.props.taskList}
              disabled={this.props.submitting}
              onChange={this.onTaskChange}
            />
          </div>
        ) : (
          <div className="field-value">
            <div className="value">{ui.renderTask(this.props.task)}</div>
          </div>
        )}
      </div>
    );
  }
}

const ExperimentTasksTable = function (props) {
  return (
    <table className="table experiment-edit-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Cost</th>
        </tr>
      </thead>
      <tbody>
        {_.chain(props.experiment.tasks)
          .sortBy("cost")
          .map((t) => (
            <tr key={t.name}>
              <td>{t.name}</td>
              <td>{ui.renderTaskCost(t.cost)}</td>
            </tr>
          ))
          .value()}
      </tbody>
    </table>
  );
};
ExperimentTasksTable.propTypes = {
  experiment: schemas.Experiment.isRequired,
};

const TaskReadOnlySection = function (props) {
  return (
    <Section
      infoClassName="experiment-task-info"
      heading="Tasks"
      sectionBody={<ExperimentTasksTable experiment={props.experiment} />}
    />
  );
};

export const TaskSection = function (props) {
  const anyTasks = props.experiment && props.experiment.tasks;
  const showTasks = Boolean(
    anyTasks && ui.existingInteraction(props.interactionState),
  );
  return showTasks && <TaskReadOnlySection experiment={props.experiment} />;
};

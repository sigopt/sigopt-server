/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {CheckpointsWidgetDefinition} from "./checkpoints_widget/";
import {MultiScatterWidgetDefinition} from "./multi_scatter_widget/";
import {PCChartWidgetDefinition} from "./pc_chart_widget/";
import {ParamaterRangeWidgetDefinition} from "./parameter_range_widget";
import {RunInfoWidgetDefinition} from "./run_info_widget";
import {RunTableWidgetDefinition} from "./runs_table_widget/";

/**
 * @typedef WidgetIndex
 * @type {object}
 * @property {function} newWidgetStateBuilder - populates editor when making new widget
 * @property {function} component             - the actual widget
 * @property {string} type                    - string constant, make sure it is unique
 * @property {object} editor                  - editor for the widget
 * @property {object} editorIsReactComponent  - is the editor a react commponent
 * @property {string} displayName             - name of widget for display purposes
 * @property {boolean} removable              - Can it be removed ? (used to make runs table unremovable)
 */

/**  @type{Object.<string, WidgetIndex>} */
export const WidgetDefinitions = {
  [MultiScatterWidgetDefinition.type]: MultiScatterWidgetDefinition,
  [PCChartWidgetDefinition.type]: PCChartWidgetDefinition,
  [RunTableWidgetDefinition.type]: RunTableWidgetDefinition,
  [CheckpointsWidgetDefinition.type]: CheckpointsWidgetDefinition,
  [ParamaterRangeWidgetDefinition.type]: ParamaterRangeWidgetDefinition,
  [RunInfoWidgetDefinition.type]: RunInfoWidgetDefinition,
};

export const WidgetNames = _.object(
  _.map(_.keys(WidgetDefinitions), (k) => [k, k]),
);

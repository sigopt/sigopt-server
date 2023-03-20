/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import classNames from "classnames";
import {connect} from "react-redux";
import {produce} from "immer";

import Component from "../react/component";
import SetFilter from "./custom_filters/set_filter";
import StarGlyph from "../component/glyph/star";
import Tag from "../tag/component";
import TagFilter from "./custom_filters/tag_filter";
import {CHART_COLORS, PARAMETER_SOURCES} from "../chart/constants";
import {Duration, RelativeTime} from "../render/format_times";
import {isDefinedAndNotNull} from "../utils";

const timestamp = ({value}) =>
  value ? <RelativeTime time={Math.floor(value.getTime() / 1000)} /> : "";

const boolean = ({value}) => {
  if (isDefinedAndNotNull(value)) {
    return <span> {value.toString()} </span>;
  } else {
    return "";
  }
};

const LinkableCell = ({href, children}) => (
  <span>
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{textDecoration: "underline", textUnderlinePosition: "under"}}
    >
      {children}
    </a>
  </span>
);

const RunLink = ({value, data}) =>
  data ? <LinkableCell href={`/run/${data.id}`}> {value} </LinkableCell> : "";

const ExperimentLink = ({value}) =>
  value ? (
    <LinkableCell href={`/aiexperiment/${value}`}> {value} </LinkableCell>
  ) : (
    ""
  );

class CreatedByLink extends React.Component {
  constructor(props) {
    super(props);
    this.getAndSetUser();
    this.state = {
      user: null,
    };
  }

  getAndSetUser = () => {
    if (this.props.data && isDefinedAndNotNull(this.props.data.user)) {
      this.props.context.usersDataPool
        .get(this.props.data.user)
        .then((user) => this.setState({user}));
    }
  };

  render() {
    if (!this.props.data) {
      return "";
    }
    const {data, value, context} = this.props;
    const linkableCellContent = this.state.user ? this.state.user.name : value;

    return (
      <LinkableCell
        href={`/organization/${context.organizationId}/users/${data.user}`}
      >
        {linkableCellContent}
      </LinkableCell>
    );
  }
}

class FavoriteCell extends Component {
  constructor(props) {
    super(props);
    this.state = {active: this.props.data && this.props.data.favorite};
  }

  toggleEventHandler = (event) => {
    event.stopPropagation();
    const updateNonce = Math.random();
    this.currentNonce = updateNonce;
    const initialActive = this.state.active;
    const newActive = !initialActive;
    this.setState({active: newActive}, () => {
      this.services.promiseApiClient
        .trainingRuns(this.props.data.id)
        .update({favorite: newActive})
        .then(
          () => {
            if (updateNonce === this.currentNonce) {
              this.props.node.data = produce(this.props.node.data, (s) => {
                s.favorite = true;
              });
            }
          },
          (err) => {
            if (updateNonce === this.currentNonce) {
              this.setState({active: initialActive});
            }
            return Promise.reject(err);
          },
        );
    });
  };

  render() {
    return (
      <div className="star-wrapper">
        <StarGlyph
          className={classNames("star", {
            active: this.state.active,
            inactive: !this.state.active,
          })}
          onClick={this.toggleEventHandler}
        />
      </div>
    );
  }
}

class DatasetsCell extends Component {
  render() {
    if (!this.props.data) {
      return null;
    }
    return <div>{(_.keys(this.props.data.datasets) || []).join(", ")}</div>;
  }
}

class DurationCell extends React.Component {
  state = {now: Date.now() / 1000};
  render() {
    const {data} = this.props;
    const startTime = data.created;
    const endTime = data.completed || this.state.now;
    return <Duration startTime={startTime} endTime={endTime} />;
  }
}

const mapTagsStateToProps = (state) => ({
  tags: state.dimensions.tagsById,
});

const TagsCell = connect(mapTagsStateToProps)(
  class _TagsCell extends React.Component {
    render() {
      if (!this.props.data || !this.props.tags) {
        return null;
      }
      return (
        <div>
          {_.map(this.props.data.tags, (tagId) => (
            <Tag key={tagId} data={this.props.tags[tagId]} />
          ))}
        </div>
      );
    }
  },
);

export const TagFilterCell = connect(mapTagsStateToProps)(
  class _TagFilterCell extends React.Component {
    render() {
      if (!this.props.value || !this.props.tags) {
        return null;
      }
      return <Tag data={this.props.tags[this.props.value]} />;
    }
  },
);

const PARAMETER_SOURCE_COLOURS = {
  [PARAMETER_SOURCES.SIGOPT]: CHART_COLORS.LIGHT_BLUE,
  [PARAMETER_SOURCES.USER]: CHART_COLORS.ORANGE,
};
const PARAMETER_SOURCE_FALLBACK_COLOR = CHART_COLORS.MEDIUM_GREY;
const TRIANGLE_GRADIENT = (color) =>
  `linear-gradient(45deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 50%, ${color} 50%, ${color} 100%)`;

const getParameterSourceTriangle = (sourceName) => {
  const sourceColor =
    PARAMETER_SOURCE_COLOURS[sourceName] || PARAMETER_SOURCE_FALLBACK_COLOR;
  return TRIANGLE_GRADIENT(sourceColor);
};

const ParameterCell = ({data, value, colDef}) => {
  const parameterName = colDef.colId.slice("assignments.".length);
  const parameterSource =
    data &&
    data.assignments_meta &&
    data.assignments_meta[parameterName] &&
    data.assignments_meta[parameterName].source;

  const style = {};
  if (parameterSource) {
    style.background = getParameterSourceTriangle(parameterSource);
  }

  return (
    <div>
      {value}
      <div className="parameter-source-triangle" style={style} />
    </div>
  );
};

const ParameterCellTooltip = ({api, rowIndex, colDef}) => {
  const data = api.getDisplayedRowAtIndex(rowIndex).data;
  const parameterName = colDef.colId.slice("assignments.".length);
  const parameterSource =
    data &&
    data.assignments_meta &&
    data.assignments_meta[parameterName] &&
    data.assignments_meta[parameterName].source;

  if (!parameterSource) {
    return "";
  }

  return (
    <div className="parameter-tooltip">
      <div>Parameter Source: {parameterSource}</div>
    </div>
  );
};

// NOTE: You can have the type field match(ie timestamp/bool) or manually set the renderer in columnOverrides.
// If you need aditional information in a renderer pass it via the context object on the table.
export const CellRenderers = {
  boolean,
  timestamp,

  CreatedByLink,
  DatasetsCell,
  DurationCell,
  ExperimentLink,
  RunLink,
  SetFilter,
  TagFilterCell,
  TagsCell,
  TagFilter,
  FavoriteCell,
  ParameterCell,
  ParameterCellTooltip,
};

export const CellRendererNames = _.object(
  _.map(_.keys(CellRenderers), (k) => [k, k]),
);

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Autocomplete from "react-autocomplete";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import MagnifyingGlassGlyph from "../component/glyph/magnifying-glass";
import Spinner from "../component/spinner";
import schemas from "../react/schemas";
import {coalesce} from "../utils";

const stateEnum = {
  EMPTY: "empty",
  LOADING: "loading",
  FILL: "fill",
};

const dropdownEnum = {
  SEARCH_ALL: "search_all",
  SEARCH_RESULT: "search_result",
};

const LIMIT_RESULTS = 7;

class AsynchronousUserNameHighlight extends React.Component {
  static propTypes = {
    dataSource: PropTypes.object.isRequired,
    highlight: PropTypes.func.isRequired,
  };

  constructor() {
    super();
    this._isMounted = false;
  }

  state = {
    hasUser: false,
    user: null,
  };

  componentDidMount() {
    this._isMounted = true;
    this.componentDidUpdate({}, this.state);
  }

  componentDidUpdate() {
    if (!this.state.hasUser && this.props.dataSource) {
      this.props.dataSource.getData((user) => {
        if (this._isMounted) {
          this.setState({user: user, hasUser: true});
        }
      });
    }
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  render() {
    const text = (this.state.user && this.state.user.name) || "Unknown";
    return this.state.hasUser ? (
      <span>by {this.props.highlight(text)}</span>
    ) : (
      <Spinner className="created-by-spinner" size={7} position="relative" />
    );
  }
}

class SearchBoxMenuItem extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    isHighlighted: PropTypes.bool.isRequired,
    keyword: PropTypes.string.isRequired,
    onClick: PropTypes.func,
    onMouseEnter: PropTypes.func,
    userDataSources: PropTypes.object.isRequired,
  };

  highlight = (text) => {
    const keyword = this.props.keyword.toLowerCase().trim();
    const firstMatchIndex = text.toLowerCase().indexOf(keyword);
    const escapedReactComponents = [];
    if (firstMatchIndex >= 0) {
      escapedReactComponents.push(text.substring(0, firstMatchIndex));
      const emphasizedString = (
        <em key="1">
          {text.substring(firstMatchIndex, firstMatchIndex + keyword.length)}
        </em>
      );
      escapedReactComponents.push(emphasizedString);
      escapedReactComponents.push(
        text.substring(firstMatchIndex + keyword.length, text.length),
      );
      return escapedReactComponents;
    } else {
      return text;
    }
  };

  render() {
    // NOTE: Need to pass mouse handlers to ensure react-autocomplete's mouseover highlight functionality works
    return (
      <div
        className={classNames(
          "search-box-menu-item",
          this.props.isHighlighted && "highlight",
        )}
        onMouseEnter={this.props.onMouseEnter}
        onClick={this.props.onClick}
      >
        <span className="experiment-name">
          {this.highlight(this.props.experiment.name)}
        </span>
        <span className="experiment-author">
          {this.props.experiment.user ? (
            <AsynchronousUserNameHighlight
              dataSource={this.props.userDataSources.get(
                this.props.experiment.user,
              )}
              highlight={this.highlight}
              userId={this.props.experiment.user}
            />
          ) : null}
        </span>
      </div>
    );
  }
}

class SearchBox extends React.Component {
  static propTypes = {
    experimentListFetcher: PropTypes.func.isRequired,
    isProjectPage: PropTypes.bool.isRequired,
    name: PropTypes.string,
    navigator: schemas.Navigator.isRequired,
    onSearchAll: PropTypes.func.isRequired,
    pageQuery: PropTypes.string.isRequired,
    userDataSources: PropTypes.object.isRequired,
  };

  state = {
    menuState: stateEnum.EMPTY,
    keyword: this.props.pageQuery,
    keywordOfResults: "",
    suggestions: [],
  };

  componentDidMount() {
    this._isMounted = true;
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  wrapperProps = () => ({
    className: "search-wrapper",
    style: {},
    onFocus: (e) => e.target.select(),
  });

  inputProps = () => ({
    className: "search-input",
    placeholder: "Search...",
  });

  handleChange = (e, keyword) => {
    const searchTerm = coalesce(keyword, this.state.keyword, "");
    if (searchTerm.trim() === "") {
      this.setState({
        keyword: searchTerm,
        menuState: stateEnum.EMPTY,
        suggestions: [],
        keywordOfResults: "",
      });
    } else {
      if (this.state.suggestions.length > 0) {
        this.setState({keyword: searchTerm, menuState: stateEnum.FILL});
      } else {
        this.setState({keyword: searchTerm, menuState: stateEnum.LOADING});
      }

      this.props.experimentListFetcher(
        {
          search: searchTerm,
          limit: LIMIT_RESULTS,
          state: "all",
          sort: "recent",
        },
        (c) => {
          // NOTE: Ensures correct suggestions aren't overwritten by delayed callback
          if (
            this._isMounted &&
            this.state.keywordOfResults !== this.state.keyword
          ) {
            const menuItems = _.map(c.data, (item) => ({
              kind: dropdownEnum.SEARCH_RESULT,
              data: item,
            }));
            if (menuItems.length > 0) {
              menuItems.unshift({
                kind: dropdownEnum.SEARCH_ALL,
                highlighted: false,
              });
            }
            this.setState({
              menuState: stateEnum.FILL,
              keywordOfResults: searchTerm,
              suggestions: menuItems,
            });
          }
        },
      );
    }
  };

  handleSelect = (value, item) => {
    if (item.kind === dropdownEnum.SEARCH_RESULT) {
      this.props.navigator.navigateTo(`/experiment/${item.data.id}`);
    } else if (item.kind === dropdownEnum.SEARCH_ALL) {
      this.props.onSearchAll(this.state.keyword);
    }
  };

  renderMenu = (items) => {
    const menuContents = {
      [stateEnum.EMPTY]: (
        <div className="information-label">
          <i>
            Search for experiments{" "}
            {this.props.isProjectPage ? "in the project " : null}by experiment
            name or user name.
          </i>
        </div>
      ),
      [stateEnum.LOADING]: (
        <Spinner className="search-spinner" size={7} position="relative" />
      ),
      [stateEnum.FILL]:
        items.length > 0 ? (
          items
        ) : (
          <div className="information-label no-results">
            <i>No experiments found.</i>
          </div>
        ),
    }[this.state.menuState];

    return (
      <div
        className={classNames(
          "search-box-menu",
          (this.state.menuState === stateEnum.EMPTY ||
            this.state.menuState === stateEnum.LOADING) &&
            "disable-click",
        )}
      >
        {menuContents}
      </div>
    );
  };

  renderItem = (item, isHighlighted) => {
    if (item.kind === dropdownEnum.SEARCH_RESULT) {
      return (
        <SearchBoxMenuItem
          experiment={item.data}
          isHighlighted={isHighlighted}
          key={item.data ? item.data.id : undefined}
          keyword={this.state.keyword}
          userDataSources={this.props.userDataSources}
        />
      );
    } else if (item.kind === dropdownEnum.SEARCH_ALL) {
      return (
        <div
          key={dropdownEnum.SEARCH_ALL}
          className={classNames(
            "search-box-menu-item",
            "search-all-item",
            isHighlighted && "highlight",
          )}
        >
          <MagnifyingGlassGlyph />
          <span className="experiment-name">
            Search all results for <em key="1">{this.state.keyword}</em>
          </span>
          <div className="divider" />
        </div>
      );
    } else {
      return null;
    }
  };

  getItemValue = (item) =>
    ({
      [dropdownEnum.SEARCH_RESULT]: item.data ? item.data.name : undefined,
      [dropdownEnum.SEARCH_ALL]: this.state.keyword,
    }[item.kind]);

  render() {
    return (
      <Autocomplete
        autoHighlight={true}
        getItemValue={this.getItemValue}
        inputProps={this.inputProps()}
        items={this.state.suggestions}
        name={this.props.name}
        onChange={this.handleChange}
        onMenuVisibilityChange={this.handleChange}
        onSelect={this.handleSelect}
        renderMenu={this.renderMenu}
        renderItem={this.renderItem}
        value={this.state.keyword}
        wrapperProps={this.wrapperProps()}
      />
    );
  }
}

export default SearchBox;

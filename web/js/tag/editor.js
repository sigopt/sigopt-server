/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./editor.less";

import _ from "underscore";
import CreatableSelect from "react-select/creatable";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import {CirclePicker} from "react-color";
import {components} from "react-select";

import PencilGlyph from "../component/glyph/pencil";
import PlusGlyph from "../component/glyph/plus";
import Tag from "./component";

const DEFAULT_TAG_COLOR = "#343740";
const PALETTE = [
  "#0098d1",
  "#772a90",
  "#a23d97",
  "#f5811f",
  "#ffe739",
  "#00b140",
  "#96ca4f",
  DEFAULT_TAG_COLOR,
];
const CIRCLE_SWATCH_WIDTH = 42;

class TagColorPicker extends React.Component {
  onSelect = (color) =>
    this.props.onSelect(_.extend({}, this.props.tag, {color: color.hex}));
  onSelectCurrent = () => this.props.onSelect(this.props.tag);
  onHover = (color) =>
    this.props.onHover(_.extend({}, this.props.tag, {color: color.hex}));

  render() {
    return (
      <>
        <div>
          Choose a color for{" "}
          <Tag
            data={this.props.tag}
            innerProps={{onClick: this.onSelectCurrent}}
          />
        </div>
        <div className="color-picker">
          <CirclePicker
            colors={PALETTE}
            hex={this.props.tag.color}
            onChangeComplete={this.onSelect}
            onSwatchHover={this.onHover}
            width={CIRCLE_SWATCH_WIDTH * _.size(PALETTE)}
          />
        </div>
      </>
    );
  }
}

const TagOption = (props) => {
  if (props.data.object === "tag") {
    return <Tag {...props} />;
  }
  return (
    <div className="create-tag-option">
      Create tag <Tag {...props} />
    </div>
  );
};

const NullComponent = () => null;

const InputComponent = (props) => (
  <components.Input {...props} autoFocus={true} />
);

const MenuListComponent = (props) => (
  <components.MenuList
    {...props}
    className={classNames("menu-list", props.className)}
  />
);

const AddTagsHint = ({expand}) => {
  const plusGlyph = <PlusGlyph />;
  if (expand) {
    return <a className="add-tags-hint btn">Add Tags {plusGlyph}</a>;
  }
  return plusGlyph;
};

class InnerTagEditor extends React.Component {
  static propTypes = {
    addTagsHintExpand: PropTypes.bool,
    onApplyTag: PropTypes.func.isRequired,
    onCreateTag: PropTypes.func.isRequired,
    onRemoveTag: PropTypes.func.isRequired,
    reloadTags: PropTypes.func,
    selectedTagIds: PropTypes.arrayOf(PropTypes.string.isRequired),
    tags: PropTypes.objectOf(PropTypes.object.isRequired),
  };

  static defaultProps = {
    reloadTags: _.noop,
  };

  state = {editing: false, newTag: null};

  componentDidUpdate(prevProps, prevState) {
    if (this.state.editing && !prevState.editing) {
      this.props.reloadTags();
    }
  }

  onChange = (newValues, change) => {
    if (change.action === "remove-value") {
      this.props.onRemoveTag(change.removedValue);
    }
    if (change.action === "select-option") {
      this.props.onApplyTag(change.option);
    }
    if (change.action === "create-option") {
      const newTag = _.find(newValues, "newOption");
      if (newTag) {
        this.setState({newTag});
      }
    }
  };

  onHoverNewTag = (newTag) => this.setState({newTag});
  onSelectNewTag = (newTag) =>
    this.setState({newTag: null}, () =>
      this.props.onCreateTag(newTag).then(this.props.onApplyTag),
    );
  onCancelNewTag = () => this.setState({newTag: null});
  startEditing = () => this.setState({editing: true});
  stopEditing = () => this.setState({editing: false});
  getNewOptionData = (inputValue) => ({
    color: DEFAULT_TAG_COLOR,
    name: inputValue,
    value: inputValue,
    label: inputValue,
    newOption: true,
  });

  render() {
    if (!this.props.tags) {
      return null;
    }
    if (this.state.newTag) {
      return (
        <TagColorPicker
          tag={this.state.newTag}
          onHover={this.onHoverNewTag}
          onSelect={this.onSelectNewTag}
          onCancel={this.onCancelNewTag}
        />
      );
    }
    if (!this.state.editing) {
      return (
        <div>
          {_.map(this.props.selectedTagIds, (tagId) => (
            <Tag
              key={tagId}
              data={this.props.tags[tagId]}
              innerProps={{onClick: this.startEditing}}
            />
          ))}
          <div className="toggle-editing" onClick={this.startEditing}>
            {_.isEmpty(this.props.selectedTagIds) ? (
              <AddTagsHint expand={this.props.addTagsHintExpand} />
            ) : (
              <PencilGlyph />
            )}
          </div>
        </div>
      );
    }
    const extendedTags = _.mapObject(this.props.tags, (tag) =>
      _.extend({label: tag.name, value: tag.name}, tag),
    );
    const selectedTags = _.map(
      this.props.selectedTagIds,
      (tagId) => extendedTags[tagId],
    );
    return (
      <CreatableSelect
        menuIsOpen={true}
        components={{
          IndicatorsContainer: NullComponent,
          Input: InputComponent,
          MenuList: MenuListComponent,
          MultiValue: Tag,
          Option: TagOption,
        }}
        createOptionPosition="first"
        isMulti={true}
        placeholder="Add tags"
        onBlur={this.stopEditing}
        options={_.values(extendedTags)}
        value={selectedTags}
        onChange={this.onChange}
        getNewOptionData={this.getNewOptionData}
      />
    );
  }
}

export default function TagEditor(props) {
  return (
    <div className="tag-editor">
      <InnerTagEditor {...props} />
    </div>
  );
}

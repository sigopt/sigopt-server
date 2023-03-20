/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Tooltip from "../component/tooltip";
import XmarkGlyph from "../component/glyph/xmark";
import ui from "./ui";
import {Section} from "./section.js";

const MetadataHeading = function () {
  return (
    <Tooltip tooltip="Metadata is a key-value store for notes about your experiment">
      Metadata
    </Tooltip>
  );
};

const MetadataReadOnlyTable = function (props) {
  return (
    !_.isEmpty(props.metadata) && (
      <Section
        heading={<MetadataHeading />}
        sectionBody={
          <div className="experiment-table-holder">
            <table className="table header-as-row">
              {!_.isEmpty(props.metadata) && (
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Value</th>
                  </tr>
                </thead>
              )}
              <tbody>
                {_.map(props.metadata, (m) => (
                  <tr key={m.key}>
                    <td>{m.key}</td>
                    <td>
                      <span>{m.value}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        }
      />
    )
  );
};

class MetadataEditTable extends React.Component {
  static propTypes() {
    return {
      metadata: PropTypes.arrayOf(
        PropTypes.Shape({
          number: PropTypes.bool,
          new: PropTypes.bool.isRequired,
          key: PropTypes.string.isRequired,
          value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
        }),
      ),
      onAdd: PropTypes.function.isRequired,
      onChange: PropTypes.function.isRequired,
      onRemove: PropTypes.function.isRequired,
    };
  }

  onValueChange = (idx, key, isNew, number) => (e) => {
    const value = number ? Number(e.target.value) : e.target.value;
    this.props.onChange(idx, key, value, isNew, number);
  };

  onKeyChange = (idx, value, isNew) => (e) => {
    this.props.onChange(idx, e.target.value, value, isNew);
  };

  render() {
    const [newMetadata, existingMetadata] = _.partition(
      this.props.metadata,
      (m) => m.new,
    );

    return (
      <Section
        heading={<MetadataHeading />}
        sectionBody={
          <div className="experiment-table-holder">
            <table className="table header-as-row">
              {!_.isEmpty(this.props.metadata) && (
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Value</th>
                    <th className="remove-row-column" />
                  </tr>
                </thead>
              )}
              <tbody>
                {_.map(existingMetadata, (m, idx) => (
                  <tr key={m.key}>
                    <td>{m.key}</td>
                    <td>
                      <input
                        className="form-control"
                        onChange={this.onValueChange(
                          idx,
                          m.key,
                          false,
                          m.number,
                        )}
                        type={m.number ? "number" : "text"}
                        value={m.value}
                      />
                    </td>
                    <td className="remove-row-column">
                      <button
                        className="btn btn-xs btn-remove"
                        onClick={() => this.props.onRemove(idx)}
                        type="button"
                      >
                        <XmarkGlyph />
                      </button>
                    </td>
                  </tr>
                ))}
                {_.map(newMetadata, (m, idx) => (
                  <tr key={idx}>
                    <td>
                      <input
                        className="form-control"
                        onChange={this.onKeyChange(
                          idx + existingMetadata.length,
                          m.value,
                          true,
                        )}
                        type="text"
                        value={m.key}
                      />
                    </td>
                    <td>
                      <input
                        className="form-control"
                        onChange={this.onValueChange(
                          idx + existingMetadata.length,
                          m.key,
                          true,
                        )}
                        type="text"
                        value={m.value}
                      />
                    </td>
                    <td>
                      <button
                        className="btn btn-xs btn-remove"
                        onClick={() =>
                          this.props.onRemove(idx + existingMetadata.length)
                        }
                        type="button"
                      >
                        <XmarkGlyph />
                      </button>
                    </td>
                  </tr>
                ))}
                <tr className="button-container">
                  <td colSpan="3">
                    <button
                      className="btn btn-secondary"
                      onClick={this.props.onAdd}
                      type="button"
                    >
                      Add Metadata
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        }
      />
    );
  }
}

export const MetadataSection = function (props) {
  return ui.inputInteraction(props.interactionState) ? (
    <MetadataEditTable
      metadata={props.metadata}
      onAdd={props.onAdd}
      onChange={props.onChange}
      onRemove={props.onRemove}
    />
  ) : (
    <MetadataReadOnlyTable metadata={props.metadata} />
  );
};

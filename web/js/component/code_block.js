/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../render/bootstrap";

import $ from "jquery";
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Clipboard from "../render/clipboard";
import Component from "../react/component";
import CopyGlyph from "../component/glyph/copy";
import Spinner from "../component/spinner";
import forceRemountOnUpdate from "../react/force-remount";
import hljs from "../highlight/index";
import {isDefinedAndNotNull, replaceAll} from "../utils";

// NOTE: If you extend this enum, it won't work unless you update highlight/index.js
// since that file is a custom build that includes only the languages we use.
const LANGUAGE_PROP_TYPE = PropTypes.oneOf([
  "r",
  "python",
  "bash",
  "json",
  "matlab",
  "yaml",
  "dockerfile",
  "plaintext",
]);

export class Highlight extends React.PureComponent {
  static propTypes = {
    code: PropTypes.string.isRequired,
    language: LANGUAGE_PROP_TYPE,
    linkMap: PropTypes.object,
  };

  static defaultProps = {
    language: "plaintext",
  };

  render() {
    let highlightedCode = hljs.highlight(
      this.props.language,
      this.props.code,
    ).value;
    _.each(this.props.linkMap, (value, key) => {
      highlightedCode = replaceAll(highlightedCode, key, value);
    });
    return <span dangerouslySetInnerHTML={{__html: highlightedCode}} />;
  }
}

export const CopyButton = forceRemountOnUpdate(
  class CopyButton extends React.Component {
    static defaultProps = {
      title: "Click to copy",
    };

    constructor(...args) {
      super(...args);
      this._node = React.createRef();
    }

    componentDidMount() {
      // Can provide one of target or text
      // A ref whose content is used to generate the clipboard text
      const target = this.props.target;
      // A string whose value is placed in the clipboard
      const text = this.props.text;
      const oneOfExists =
        isDefinedAndNotNull(target) || isDefinedAndNotNull(text);

      if (oneOfExists) {
        const node = this._node.current;
        $(node).tooltip();
        this.clipboard = new Clipboard(node, {
          container: node,
          target: () => target && target.current,
          text: () => text,
        });
        this.clipboard.on("success", (e) => e.clearSelection());
      }
    }

    componentWillUnmount() {
      if (this.clipboard) {
        this.clipboard.destroy();
      }
    }

    render() {
      return (
        <span
          className="copy-btn"
          data-placement="left"
          data-toggle="tooltip"
          ref={this._node}
          title={this.props.title}
        >
          <CopyGlyph weight="regular" />
        </span>
      );
    }
  },
);

export class CopyableText extends React.Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
  };

  constructor(...args) {
    super(...args);
    this._codeBlockRef = React.createRef();
  }

  render() {
    return (
      <pre className="code-holder">
        <CopyButton target={this._codeBlockRef} />
        <span className="code-block" ref={this._codeBlockRef}>
          {this.props.children}
        </span>
      </pre>
    );
  }
}

export class CodeBlock extends React.Component {
  static propTypes = {
    children: PropTypes.string.isRequired,
    language: PropTypes.string,
    linkMap: PropTypes.object,
  };

  render() {
    return (
      <CopyableText>
        <Highlight
          code={this.props.children}
          language={this.props.language}
          linkMap={this.props.linkMap}
        />
      </CopyableText>
    );
  }
}

export class GitHubCodeBlock extends Component {
  static propTypes = {
    language: PropTypes.string,
    url: PropTypes.string,
  };

  state = {
    gitHubCode: null,
    failed: false,
  };

  componentDidMount() {
    this.services.netRequestor.request(
      {
        method: "GET",
        url: this.baseGitHubFetchUrl + this.props.url,
      },
      (body, code) => {
        if (code === 200) {
          this.setState({gitHubCode: body});
        } else {
          this.setState({failed: true});
        }
      },
      () => this.setState({failed: true}),
    );
  }

  baseGitHubHash = "b73b2332a1975291267c417cd2c070555ea66d86"; // NOTE: as of 2022-10-26
  baseGitHubFetchUrl = `https://raw.githubusercontent.com/sigopt/sigopt-examples/${this.baseGitHubHash}/`;
  baseGitHubViewUrl = `https://github.com/sigopt/sigopt-examples/blob/${this.baseGitHubHash}/`;

  render() {
    if (this.state.failed) {
      const url = this.baseGitHubViewUrl + this.props.url;
      return (
        <pre>
          Ooops! Something went wrong while trying to load a code block. Please
          click{" "}
          <a href={url} target="_blank" rel="noopener noreferrer">
            here
          </a>{" "}
          to view the code on GitHub.
        </pre>
      );
    } else if (this.state.gitHubCode === null) {
      return <Spinner />;
    } else {
      return (
        <CodeBlock language={this.props.language}>
          {this.state.gitHubCode}
        </CodeBlock>
      );
    }
  }
}

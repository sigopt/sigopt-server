/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Section from "../../../component/section";

const DefaultEmptyMessage = () => <p>Nothing to see here.</p>;

class RunPageSectionContent extends React.Component {
  static propTypes = {
    ActiveMessage: PropTypes.func,
    Content: PropTypes.func.isRequired,
    Disclaimer: PropTypes.func,
    EmptyMessage: PropTypes.func,
    empty: PropTypes.bool.isRequired,
    trainingRun: PropTypes.object.isRequired,
  };

  static defaultProps = {
    EmptyMessage: DefaultEmptyMessage,
  };

  render() {
    const {ActiveMessage, Content, Disclaimer, EmptyMessage} = this.props;
    let content = null;
    if (this.props.empty) {
      if (ActiveMessage && this.props.trainingRun.state === "active") {
        content = (
          <div className="alert alert-info">
            <ActiveMessage {...this.props} />
          </div>
        );
      } else {
        content = <EmptyMessage {...this.props} />;
      }
    } else {
      content = <Content {...this.props} />;
    }
    return (
      <>
        {Disclaimer ? (
          <div className="alert alert-warning">
            <Disclaimer />
          </div>
        ) : null}
        {content}
      </>
    );
  }
}

export default (props) => (
  <Section {...props}>
    <RunPageSectionContent {...props} />
  </Section>
);

/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../react/component";
import TolerateErrors from "../react/tolerate-errors";

class ReactChart extends Component {
  static displayName = "ReactChart";

  static propTypes = {
    args: PropTypes.object.isRequired,
    cls: PropTypes.func.isRequired,
    fullChartHeight: PropTypes.bool,
  };

  static defaultProps = {
    fullChartHeight: true,
  };

  constructor(...args) {
    super(...args);
    this._el = React.createRef();
  }

  componentDidMount() {
    this.redraw();
  }

  // Redrawing the chart is expensive
  shouldComponentUpdate(nextProps) {
    return !_.isEqual(this.props, nextProps);
  }

  componentDidUpdate() {
    this.redraw();
  }

  componentWillUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
    const el = this._el.current;
    const $chart = $(el).find(".chart");
    if ($chart) {
      $chart.empty();
    }
  }

  _handleError =
    (func) =>
    (...args) => {
      try {
        func(...args);
      } catch (err) {
        // NOTE: this brings the error back into the React lifecycle so that it can get picked up by
        // TolerateErrors
        this.setState(() => {
          throw err;
        });
      }
    };

  redraw = () => {
    const el = this._el.current;
    if (this.chart && this.chart.constructor === this.props.cls) {
      this.chart.setArgs(this.props.args);
      _.defer(this._handleError(() => this.chart.redrawChart()));
    } else {
      const Cls = this.props.cls;
      this.chart = new Cls(_.extend({el: $(el)}, this.props.args));
      _.defer(this._handleError(() => this.chart.initialize()));
    }
  };

  render() {
    const {fullChartHeight} = this.props;
    const style = {};
    if (fullChartHeight) {
      style.height = "100%";
    }
    return (
      <div ref={this._el} style={style}>
        <div className="chart" style={style} />
      </div>
    );
  }
}

const WrappedChart = React.forwardRef((props, ref) => (
  <TolerateErrors
    errorState={
      <div style={{textAlign: "center"}}>
        Something went wrong while making this chart!
        {""}
        <br />
        {""}Try reloading the page.
      </div>
    }
  >
    <ReactChart ref={ref} {...props} />
  </TolerateErrors>
));

export default WrappedChart;

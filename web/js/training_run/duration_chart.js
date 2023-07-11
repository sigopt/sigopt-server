/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./duration_chart.less";

import _ from "underscore";
import React from "react";
import classNames from "classnames";

import Component from "../react/component";
import {compactDuration} from "../render/nice-times";
import {isDefinedAndNotNull} from "../utils";

/*
 * The DurationChart component consists of a few essential components
 *
 *  * duration-chart-wrapper: A div that contains the chart bars and exactly fits the required width of all the bars.
 *  * minimap: Includes the scaled chart and scroll window. The chart is scaled so that it fits in the available space.
 *  * scroll-window: The light background on the minimap, highlighting the currently visible area, rendered behind the minimap chart bars.
 *  * scroll-window-border: The scroll window border is rendered on top of the minimap chart bars.
 *  * chart: The main full-sized chart window. Horizontal scrolling and minimap interactions allow the user to see the overflow content.
 *  * duration-bar-click-target: The zone for triggering hover actions and allowing the user to navigate to the run.
 *  * run-duration-bar: Visible bars on the chart.
 *  * hover-info-window: An overlay for rendering the information when hovering over bars.
 *  * hover-info: The information box shown when hovering over bars.
 *  * hover-arrow: The small triangle that extends from the border of the hover-info box is a 45deg rotated square.
 */

const CHART_HEIGHT_PX = 150;
const MAX_BAR_VALUE = 0.95;
const MIN_BAR_VALUE = 0.2;
const MINIMAP_HEIGHT_PX = 50;
const MIN_BAR_WIDTH_PX = 8;
const MAX_BAR_WIDTH_PX = 32;
const BAR_SPACING = 2;
const HOVER_INFO_WIDTH_PX = 140;

const getRunDuration = (run) =>
  Math.max(0, (run.completed || Date.now() / 1000) - run.created);

class RunDuration extends React.Component {
  state = {duration: 0};

  componentDidMount() {
    this.interval = setInterval(this.updateDuration, 1000);
    this.updateDuration();
  }

  componentDidUpdate(prevProps) {
    if (this.props.run.completed !== prevProps.run.completed) {
      this.updateDuration();
    }
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  updateDuration = () => {
    this.setState(() => {
      if (isDefinedAndNotNull(this.props.run.completed)) {
        clearInterval(this.interval);
      }
      return {
        duration: getRunDuration(this.props.run),
      };
    });
  };

  render() {
    const duration = this.state.duration;
    return compactDuration(duration);
  }
}

const HoverInfo = ({
  barWidth,
  index,
  run,
  point,
  visibleChartWidth,
  visibleChartHeight,
  scrollLeft,
  yPos,
}) => {
  // NOTE: this inexplicable constant is required to align the hover info up with the center of the chart bar
  const magic = 1.5;
  const hoverXPos =
    (index + 0.5) * (barWidth + BAR_SPACING * 2) - scrollLeft + magic;
  const hoverArrowVisibleWidth = 3; // Portion of the hover arrow that sticks out of the hover info.
  const spacing = 1 + (barWidth + BAR_SPACING * 2) / 2 + hoverArrowVisibleWidth; // distance on the left or right of the hover info from the center of the bar.
  const leftInfo =
    hoverXPos + HOVER_INFO_WIDTH_PX + spacing >= visibleChartWidth; // does the hover info need to be on the left side?
  const hoverInfoLeft =
    hoverXPos + (leftInfo ? -HOVER_INFO_WIDTH_PX - spacing : spacing);
  const hoverArrowLeft =
    hoverXPos - hoverArrowVisibleWidth + (leftInfo ? -spacing : spacing);
  const hoverInfoHeight = 52; // a bit hacky, 3 lines of 14px text + 5px padding on top and bottom
  // NOTE: not sure why margins are asymmetric, but 3 == 2 * 1.5 so it might be related to the magic number
  const hoverInfoMarginTop = 0;
  const hoverInfoMarginBottom = 3;
  const verticalCenterOffset = hoverInfoHeight / 2;
  let clampedYPos = yPos;
  const barHeight = point.value * visibleChartHeight;
  clampedYPos = Math.max(clampedYPos, visibleChartHeight - barHeight); // don't exceed bar height
  clampedYPos = Math.max(
    clampedYPos,
    verticalCenterOffset + hoverInfoMarginTop,
  ); // don't clip out of the top
  clampedYPos = Math.min(
    clampedYPos,
    visibleChartHeight - verticalCenterOffset - hoverInfoMarginBottom,
  ); // don't clip out of the bottom
  return (
    <>
      <div
        className={classNames("hover-arrow", {
          left: leftInfo,
          right: !leftInfo,
        })}
        style={{
          left: hoverArrowLeft,
          width: 7,
          height: 7,
          top: clampedYPos - hoverArrowVisibleWidth,
        }}
      />
      <div
        className="hover-info"
        style={{
          left: hoverInfoLeft,
          width: HOVER_INFO_WIDTH_PX,
          top: clampedYPos - verticalCenterOffset,
        }}
      >
        <b>Run ID:</b> {run.id}
        <br />
        <b>Status:</b> {run.state}
        <br />
        <b>Duration:</b> <RunDuration key={run.id} run={run} />
      </div>
    </>
  );
};

class ChartBar extends Component {
  // the bar renders once with 0 height so that it can animate in
  state = {value: 0};

  componentDidMount() {
    _.defer(() => this.setValue(this.props.value));
  }

  componentDidUpdate(prevProps) {
    if (prevProps.value !== this.props.value) {
      this.setValue(this.props.value);
    }
  }

  setValue = (value) => this.setState({value});

  onPointerEvent = (event) =>
    this.props.setHoverState?.({
      id: this.props.id,
      index: this.props.index,
      yPos: event.clientY,
    });

  render() {
    const {id, index, state, chartHeight, barWidth} = this.props;
    const left = index * (barWidth + BAR_SPACING * 2) + BAR_SPACING;
    const Element = this.props.includeLinks ? "a" : "span";
    return (
      <Element
        className={classNames("duration-bar-click-target", {
          hover: this.props.hover,
        })}
        href={`/run/${id}`}
        style={{
          height: chartHeight,
          width: barWidth + BAR_SPACING * 2,
          left,
        }}
        onPointerEnter={this.onPointerEvent}
        onPointerMove={this.onPointerEvent}
      >
        <div
          className={classNames("run-duration-bar", "full", state)}
          style={{
            height: this.state.value * chartHeight,
            width: barWidth,
            bottom: 0,
            left: BAR_SPACING,
          }}
        />
      </Element>
    );
  }
}

class InnerChart extends React.Component {
  shouldComponentUpdate(prevProps) {
    // required for performance, otherwise this component will re-render every time the parent renders,
    // which happens every time the pointer moves over the chart (when the hover state is updated).
    const propKeys = [
      "chartWidth",
      "chartHeight",
      "points",
      "includeLinks",
      "setHoverState",
      "barWidth",
    ];
    return !_.isEqual(
      _.pick(this.props, propKeys),
      _.pick(prevProps, propKeys),
    );
  }

  render() {
    const {
      chartWidth,
      chartHeight,
      points,
      includeLinks,
      setHoverState,
      barWidth,
    } = this.props;
    return (
      <div
        className="duration-chart-wrapper"
        style={{
          height: chartHeight,
          width: chartWidth,
        }}
        onPointerLeave={this.props.resetHoverState}
      >
        {_.map(points, ({id, value, state}, idx) => (
          <ChartBar
            key={id}
            id={id}
            value={value}
            barWidth={barWidth}
            chartHeight={chartHeight}
            index={idx}
            state={state}
            includeLinks={includeLinks}
            setHoverState={setHoverState}
          />
        ))}
      </div>
    );
  }
}

export default class DurationChart extends Component {
  state = {
    chartHorizontalSpace: null,
    fixedToRightSide: true,
    scrollLeft: null,
  };

  innerChartRef = React.createRef();
  outerChartRef = React.createRef();

  componentDidMount() {
    window.addEventListener("resize", this.updateChartWidth);
    window.addEventListener("pointerup", this.stopMinimapScroll);
    window.addEventListener("pointermove", this.onPointerMove);
    this.updateChartWidth();
    this.scrollRight();
    this.calculatePoints();
  }

  componentDidUpdate(prevProps, prevState) {
    this.updateChartWidth();
    if (!_.isEqual(this.props.runs, prevProps.runs)) {
      this.calculatePoints();
    }
    if (
      (!_.isEqual(this.state.points, prevState.points) ||
        this.state.chartHorizontalSpace !== prevState.chartHorizontalSpace) &&
      !this.state.minimapPointerDown &&
      this.state.fixedToRightSide
    ) {
      // new runs came in and the scroll is fixed to the right side, so scroll to the right
      this.scrollRight();
    }
    if (!this.state.minimapPointerDown && prevState.minimapPointerDown) {
      // to check if the scroll window is fixed to the right side when the minimap is de-selected
      this.onScroll();
    }
    if (
      this.state.minimapPointerDown &&
      this.state.scrollLeft !== prevState.scrollLeft
    ) {
      // minimap scrolling
      this.innerChartRef.current.scrollTo(this.state.scrollLeft, 0);
    }
  }

  componentWillUnmount() {
    window.removeEventListener("resize", this.updateChartWidth);
    window.removeEventListener("pointerup", this.stopMinimapScroll);
    window.removeEventListener("pointermove", this.onPointerMove);
  }

  calculatePoints = () => {
    const runs = this.props.runs.slice().reverse();
    const points = _.map(runs, (run) => ({
      id: run.id,
      duration: Math.log(getRunDuration(run) + 1),
      state: run.state,
    }));
    const durations = _.pluck(points, "duration");
    const maxDuration = _.max(durations);
    const minDuration = _.min(durations);
    const maxDelta = maxDuration - minDuration || 1;
    _.each(points, (point) =>
      _.extend(point, {
        value:
          ((point.duration - minDuration) * (MAX_BAR_VALUE - MIN_BAR_VALUE)) /
            maxDelta +
          MIN_BAR_VALUE,
      }),
    );
    this.setState({points});
  };

  scrollRight = () => {
    const chart = this.innerChartRef.current;
    chart.scrollTo(chart.scrollWidth, 0);
  };

  updateChartWidth = _.debounce(() => {
    if (this.outerChartRef.current) {
      this.setState((state) => {
        if (
          state.chartHorizontalSpace !== this.outerChartRef.current.clientWidth
        ) {
          return {chartHorizontalSpace: this.outerChartRef.current.clientWidth};
        }
        return null;
      });
    }
  }, 250);

  getChartDimensions = () => {
    const {chartHorizontalSpace} = this.state;
    if (!chartHorizontalSpace) {
      return null;
    }
    const runCount = _.size(this.props.runs);
    let barWidth =
      (chartHorizontalSpace - BAR_SPACING * 2) / runCount - BAR_SPACING * 2;
    barWidth = Math.min(barWidth, MAX_BAR_WIDTH_PX);
    barWidth = Math.max(barWidth, MIN_BAR_WIDTH_PX);
    const fullChartWidth =
      (barWidth + BAR_SPACING * 2) * _.size(this.props.runs) + BAR_SPACING * 2;
    const hideMinimap = fullChartWidth <= chartHorizontalSpace + 1;
    return {
      barWidth,
      fullChartWidth,
      hideMinimap,
    };
  };

  onScroll = () => {
    const chart = this.innerChartRef.current;
    const chartDimensions = this.getChartDimensions();
    if (chartDimensions) {
      this.setState({
        fixedToRightSide:
          chart.scrollLeft + chart.clientWidth >=
          chartDimensions.fullChartWidth,
        scrollLeft: chart.scrollLeft,
      });
    }
  };

  getScrollLeftFromPointer = (pointerX) => {
    // Given the pointer X location from the minimap, return the left scroll position on the full sized chart.
    // This is clamped so that the scroll window is contained within the chart area.
    const chartDimensions = this.getChartDimensions();
    if (!chartDimensions) {
      return null;
    }
    const {fullChartWidth} = chartDimensions;
    const chartLeft = this.innerChartRef.current.getBoundingClientRect().left;
    const pointerLocationOnFullChart =
      ((pointerX - chartLeft) * fullChartWidth) /
      this.innerChartRef.current.clientWidth;
    const scrollLeftOffsetFromPointer =
      -this.innerChartRef.current.clientWidth / 2;
    return Math.max(
      0,
      Math.min(
        fullChartWidth - this.innerChartRef.current.clientWidth,
        pointerLocationOnFullChart + scrollLeftOffsetFromPointer,
      ),
    );
  };

  onPointerDownMinimap = (event) => {
    this.setState({
      minimapPointerDown: true,
      scrollLeft: this.getScrollLeftFromPointer(event.clientX),
    });
  };

  onPointerMove = (event) => {
    const pointerX = event.clientX;
    this.setState((state) => {
      if (state.minimapPointerDown) {
        return {scrollLeft: this.getScrollLeftFromPointer(pointerX)};
      }
      return null;
    });
  };

  stopMinimapScroll = () => {
    this.setState({
      minimapPointerDown: false,
    });
  };

  setHoverState = ({id, index, yPos}) =>
    this.setState({
      hoverState: {
        index,
        id,
        yPos: yPos - this.innerChartRef.current.getBoundingClientRect().top,
      },
    });

  resetHoverState = () => this.setState({hoverState: null});

  render() {
    const chartDimensions = this.getChartDimensions();
    const points = this.state.points;
    let minimapParams = null;
    let hideMinimap = true;
    if (chartDimensions) {
      const {fullChartWidth} = chartDimensions;
      hideMinimap = chartDimensions.hideMinimap;
      if (!hideMinimap) {
        minimapParams = {
          xScale: this.state.chartHorizontalSpace / fullChartWidth,
          yScale: MINIMAP_HEIGHT_PX / CHART_HEIGHT_PX,
          xTranslation: (this.state.chartHorizontalSpace - fullChartWidth) / 2,
          yTranslation: (MINIMAP_HEIGHT_PX - CHART_HEIGHT_PX) / 2,
        };
      }
    }
    const innerChartTop = hideMinimap ? 0 : MINIMAP_HEIGHT_PX;
    const innerChartHeight =
      CHART_HEIGHT_PX + MINIMAP_HEIGHT_PX - innerChartTop;
    return (
      <div
        className="duration-chart"
        style={{height: CHART_HEIGHT_PX + MINIMAP_HEIGHT_PX}}
      >
        <div className="axis-label vertical">Run Duration</div>
        <div className="axis-label horizontal">Run ID</div>
        <div
          className="outer-chart"
          style={{height: CHART_HEIGHT_PX + MINIMAP_HEIGHT_PX}}
          ref={this.outerChartRef}
        >
          {minimapParams ? (
            <div
              className="minimap"
              onPointerDown={this.onPointerDownMinimap}
              style={{
                height: MINIMAP_HEIGHT_PX,
              }}
            >
              <div
                className="scroll-window"
                style={{
                  height: MINIMAP_HEIGHT_PX,
                  width: this.state.chartHorizontalSpace * minimapParams.xScale,
                  left: this.state.scrollLeft * minimapParams.xScale,
                }}
              />
              <div
                style={{
                  height: CHART_HEIGHT_PX,
                  width: chartDimensions.fullChartWidth,
                  transform: `matrix(${minimapParams.xScale},0,0,${minimapParams.yScale},${minimapParams.xTranslation},${minimapParams.yTranslation})`,
                }}
              >
                <InnerChart
                  barWidth={chartDimensions.barWidth}
                  chartWidth={chartDimensions.fullChartWidth}
                  chartHeight={innerChartHeight}
                  points={points}
                  includeLinks={false}
                />
              </div>
              <div
                className="scroll-window-border"
                style={{
                  top: 0,
                  height: MINIMAP_HEIGHT_PX,
                  width:
                    Math.min(
                      this.state.chartHorizontalSpace,
                      chartDimensions.fullChartWidth,
                    ) * minimapParams.xScale,
                  left: this.state.scrollLeft * minimapParams.xScale,
                }}
                onPointerDown={this.onPointerDownMinimap}
              />
            </div>
          ) : null}
          <div
            className="chart"
            style={{
              height: innerChartHeight,
              width: this.state.chartHorizontalSpace,
              top: innerChartTop,
            }}
            onScroll={this.onScroll}
            ref={this.innerChartRef}
          >
            {chartDimensions ? (
              <InnerChart
                barWidth={chartDimensions.barWidth}
                chartWidth={chartDimensions.fullChartWidth}
                chartHeight={innerChartHeight}
                points={points}
                includeLinks={true}
                setHoverState={this.setHoverState}
                resetHoverState={this.resetHoverState}
              />
            ) : null}
          </div>
          {this.state.hoverState && chartDimensions ? (
            <div
              className="hover-info-window"
              style={{
                height: innerChartHeight,
                width: this.state.chartHorizontalSpace,
                top: innerChartTop,
              }}
            >
              <HoverInfo
                index={this.state.hoverState.index}
                yPos={this.state.hoverState.yPos}
                run={_.find(
                  this.props.runs,
                  ({id}) => id === this.state.hoverState.id,
                )}
                point={_.find(
                  this.state.points,
                  ({id}) => id === this.state.hoverState.id,
                )}
                barWidth={chartDimensions.barWidth}
                scrollLeft={this.state.scrollLeft}
                fullChartWidth={chartDimensions.fullChartWidth}
                visibleChartWidth={this.state.chartHorizontalSpace}
                visibleChartHeight={innerChartHeight}
              />
            </div>
          ) : null}
        </div>
      </div>
    );
  }
}

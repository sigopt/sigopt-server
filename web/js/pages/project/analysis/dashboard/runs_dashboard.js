/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import "./runs_dashboard.less";
import "../../styles/tools_glyph.less";

import _ from "underscore";
import React from "react";
import Select from "react-select";
import classNames from "classnames";
import {Responsive, WidthProvider} from "react-grid-layout";
import {connect} from "react-redux";

import Component from "../../../../react/component";
import FilterGlyph from "../../../../component/glyph/filter";
import GetStartedContent from "../../../../project/get_started";
import RefreshButton from "../../../../component/refresh_button";
import Section from "../../../../component/section";
import {BigWidgetModal} from "./big_widget_modal";
import {ConnectedWidgetContainer} from "../widgets/widget_container";
import {ConnectedWidgetEditorModal} from "./new_widget_modal";
import {WidgetDefinitions} from "../widgets/widgets";
import {
  buildDashboard,
  changeDashboard,
  createDefaultDashboards,
  updateLayouts,
  updateWidget,
} from "../state/dashboards_slice";
import {
  changeFilterModel,
  fetchCheckpoints,
  fetchRuns,
  toggleDimensionsToFiltered,
} from "../../state/dimensions_slice";
import {fetchViews} from "../../state/views_slice";

const GraphFilteredToggle = ({showTableFiltered, tableFiltered}) => {
  const className = classNames(
    "btn basic-button-white mpm-border dropdown-button",
    {
      "basic-button-active-green": tableFiltered,
    },
  );
  return (
    <button onClick={showTableFiltered} type="button" className={className}>
      <FilterGlyph className="tools-glyph" />
      Graph Runs Filtered By Table
    </button>
  );
};

const NewWidgetButton = ({
  openNewWidgetModal,
  resetEditorState,
  editorState,
}) => {
  // Reset if previous state was editing a widget, leave as is otherwise
  const onClick = () => {
    if (editorState.widgetId) {
      resetEditorState();
    }
    openNewWidgetModal();
  };

  return (
    <button
      onClick={onClick}
      style={{marginLeft: 20}}
      type="button"
      className="btn basic-button-white mpm-border noGridDrag"
    >
      Add New Dashboard Widget
    </button>
  );
};

const DashboardSelect = ({dashboards, currentDashboardId, switchDashboard}) => {
  const options = dashboards.map((dashboard, i) => ({
    value: i,
    label: dashboard.name,
  }));

  const currentSelectedDashboard = _.filter(
    options,
    (o) => currentDashboardId === o.value,
  );

  const onChange = React.useCallback(
    (selection) => switchDashboard(selection.value),
    [switchDashboard],
  );

  return (
    <Select
      options={options}
      value={currentSelectedDashboard}
      onChange={onChange}
    >
      Change Dashboard
    </Select>
  );
};

const NoRunsDisplay = () => (
  <Section className="getstarted-section" fullWidth={true} title="Get Started">
    <GetStartedContent />
  </Section>
);

const ResponsiveGridLayout = WidthProvider(Responsive);

// Number of frames to wait until starting to render widgets on load/dashboard change
const WIDGET_FRAME_RENDER_BUFFER = 2;

// TODO(SN-1048): Should be split into 2 components, 1 wrapper for managing data and 1 renderer
class RunsDashboard extends Component {
  constructor(props) {
    super(props);

    const newWidgetRef = React.createRef();
    const bigWidgetModalRef = React.createRef();

    this.state = {
      renderBigModal: false,
      bigWidgetModalRef,
      newWidgetRef,
      widgetRenderedNumber: -WIDGET_FRAME_RENDER_BUFFER,
      editorState: {widgetDefinition: null, widgetData: null, widgetId: null},
      modalWidgetId: null,
      modalWidget: null,
    };
  }

  componentDidMount() {
    this.props.fetchRuns();
    this.props.fetchViews();
  }

  componentDidUpdate(prevProps) {
    // Runs have loaded, can now create default dashboards
    if (
      this.props.dashboards.length === 0 &&
      this.props.allRuns &&
      this.props.allRuns.length > 0
    ) {
      this.props.createDefaultDashboards({allRuns: this.props.allRuns});
    }

    // Default dashboards are not all created immediately but only after selecting
    // Initial load can get slowed down otherwise.
    // Want to make sure the filter model for the dashboard is correct before building.
    if (
      !_.isEqual(
        this.props.currentDashboard.filterModel,
        this.props.filterModel,
      )
    ) {
      this.props.changeFilterModel(this.props.currentDashboard.filterModel);
    } else if (this.props.currentDashboard.builder) {
      this.props.buildDashboard({
        runs: this.props.runs,
        dimensions: this.props.dims,
        dashboardId: this.props.currentDashboardId,
      });
    }

    if (this.props.allRuns !== prevProps.allRuns) {
      this.props.fetchCheckpoints();
    }

    // Renders widgets 1 by 1, prevents hang on dashboard change/lagging when lots of plots
    // TODO: Could change this to only render what is in view, would be a medium amount of work and mess with printing
    if (
      this.props.currentDashboard &&
      this.props.currentDashboard.widgets &&
      this.state.widgetRenderedNumber <
        Object.keys(this.props.currentDashboard.widgets).length
    ) {
      window.requestAnimationFrame(() =>
        this.setState((prevState) => ({
          widgetRenderedNumber: prevState.widgetRenderedNumber + 1,
        })),
      );
    }
  }

  // redirects resizes coming from react-grid-layout to the widget
  resizeEventHandler(unused1, unused2, newItem) {
    const element = document.getElementById(newItem.i).firstElementChild;
    const event = new CustomEvent("resize");
    element.dispatchEvent(event);
  }

  toggleTableFiltered = () => {
    this.props.toggleDimensionsToFiltered();
  };

  openNewWidgetModal = () => {
    if (this.state.newWidgetRef.current) {
      this.state.newWidgetRef.current.show();
    }
  };

  openBigWidgetModal = (modalWidget, modalWidgetId) => {
    this.setState({modalWidget, modalWidgetId, renderBigModal: false}, () => {
      if (this.state.bigWidgetModalRef.current) {
        this.state.bigWidgetModalRef.current.show();
      }
      // TODO: Should be a way to expose a callback from show() ?
      setTimeout(() => {
        this.setState({renderBigModal: true});
      }, 500);
    });
  };

  onLayoutChange = (layout) => {
    this.props.updateLayouts(layout);
  };

  updateWidgetState = (widgetId, updateFunc) => {
    this.props.updateWidget({widgetId, updateFunc});
  };

  changeDashboard = (nextDashboard) => {
    this.setState(
      () => ({widgetRenderedNumber: -WIDGET_FRAME_RENDER_BUFFER}),
      () => this.props.changeDashboard(nextDashboard),
    );
  };

  editWidget = (widgetInstance, widgetId) => {
    const widgetDefinition = WidgetDefinitions[widgetInstance.type];
    this.setState(
      {editorState: {widgetDefinition, widgetData: widgetInstance, widgetId}},
      this.openNewWidgetModal,
    );
  };

  setEditorState = (widgetDefinition, widgetData, widgetId) => {
    this.setState({editorState: {widgetDefinition, widgetData, widgetId}});
  };

  resetEditorState = () => {
    this.setState({
      editorState: {widget: null, widgetData: null, widgetId: null},
    });
  };

  refreshRuns = () =>
    new Promise((success, error) => {
      this.props.fetchRuns(
        () => this.props.fetchCheckpoints(success, error),
        error,
        null,
        null,
        true,
      );
    });

  render() {
    if (this.props.allRuns && this.props.allRuns.length === 0) {
      return <NoRunsDisplay />;
    }
    if (!this.props.currentDashboard || !this.props.currentDashboard.widgets) {
      return "";
    }

    const {widgets} = this.props.currentDashboard;
    const layout = _.map(Object.entries(widgets), ([id, widget]) => ({
      ..._.extend({}, widget.layout),
      i: id,
    }));

    return (
      <div>
        <ConnectedWidgetEditorModal
          setEditorState={this.setEditorState}
          editorState={this.state.editorState}
          resetEditorState={this.resetEditorState}
          modalRef={this.state.newWidgetRef}
        />
        <BigWidgetModal
          modalRef={this.state.bigWidgetModalRef}
          updateWidget={this.updateWidgetState}
          widget={this.state.modalWidget}
          widgetId={this.state.modalWidgetId}
          render={this.state.renderBigModal}
        />
        <div className="project-analysis-controls">
          <GraphFilteredToggle
            showTableFiltered={this.toggleTableFiltered}
            tableFiltered={this.props.tableFiltered}
          />
          <NewWidgetButton
            openNewWidgetModal={this.openNewWidgetModal}
            resetEditorState={this.resetEditorState}
            editorState={this.state.editorState}
          />
          <div className="dashboard-select">
            <DashboardSelect
              currentDashboardId={this.props.currentDashboardId}
              dashboards={this.props.dashboards}
              switchDashboard={this.changeDashboard}
            />
          </div>
          <span className="refresh-button-wrapper">
            <RefreshButton refresh={this.refreshRuns} />
          </span>
        </div>

        <ResponsiveGridLayout
          className="layout"
          layouts={{lg: layout}}
          rowHeight={50}
          margin={[10, 20]}
          autoSize={true}
          breakpoints={{lg: 1000, sm: 600}}
          cols={{lg: 2, sm: 1}}
          measureBeforeMount={true}
          draggableHandle=".dashboard-drag-handle"
          onResizeStop={this.resizeEventHandler}
          onLayoutChange={this.onLayoutChange}
        >
          {_.map(Object.entries(widgets), ([id, widget], index) => {
            const WidgetComponent = WidgetDefinitions[widget.type].component;
            const shouldRender = index <= this.state.widgetRenderedNumber;
            return (
              <div id={id} key={id}>
                <ConnectedWidgetContainer
                  id={id}
                  key={id}
                  widgetInstance={widget}
                  openBigWidgetModal={this.openBigWidgetModal}
                  openEditor={this.editWidget}
                >
                  {shouldRender ? (
                    <WidgetComponent
                      widget={widget}
                      updateWidget={this.updateWidgetState.bind(null, id)}
                    />
                  ) : null}
                </ConnectedWidgetContainer>
              </div>
            );
          })}
        </ResponsiveGridLayout>
      </div>
    );
  }
}

const mapDispatchToProps = {
  fetchRuns,
  fetchViews,
  fetchCheckpoints,
  toggleDimensionsToFiltered,
  updateLayouts,
  updateWidget,
  createDefaultDashboards,
  changeDashboard,
  changeFilterModel,
  buildDashboard,
};

const mapStateToProps = (state) => {
  const currentDashboard =
    state.dashboards.currentDashboardId !== null &&
    state.dashboards.dashboards[state.dashboards.currentDashboardId];
  return {
    dims: state.dimensions.dimensions,
    project: state.resources.project,
    currentDashboard,
    currentDashboardId: state.dashboards.currentDashboardId,
    dashboards: state.dashboards.dashboards,
    runsById: state.dimensions.runsById,
    runs: state.dimensions.runs,
    allRuns: state.dimensions.allRuns,
    definedFields: state.dimensions.definedFields,
    tableFiltered: state.dimensions.tableFiltered,
    filterModel: state.dimensions.filterModel,
    state,
  };
};

export const ConnectedRunsDashboard = connect(
  mapStateToProps,
  mapDispatchToProps,
)(RunsDashboard);

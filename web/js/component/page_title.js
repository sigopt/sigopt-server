/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import {Breadcrumb, BreadcrumbContainer} from "./breadcrumb";

/**
 * A PageSection that is styled as a page title.
 */
const gradientStyles = {
  admin: "admin-header-gradient",
  experiment: "experiment-header-gradient",
  project: "project-header-gradient",
  regular: "regular-header-gradient",
  run: "run-header-gradient",
};
export default function PageTitle(props) {
  const navBarStyle = props.hideBorder ? "borderless" : "";
  const gradientStyle =
    gradientStyles[props.gradientStyle] || "regular-header-gradient";

  return (
    <section className={classNames("page-title", gradientStyle)}>
      <div className="page-title-pre">
        <BreadcrumbContainer>
          {_.map(props.breadcrumbs, (breadcrumbProps, i) => (
            <Breadcrumb key={i} {...breadcrumbProps} />
          ))}
        </BreadcrumbContainer>
        <span className="page-title-secondary">{props.secondaryButtons}</span>
      </div>
      <div className="title">{props.title}</div>
      {props.info && <div className="info">{props.info}</div>}
      {props.children && (
        <div className={classNames("page-nav", navBarStyle)}>
          {props.children}
        </div>
      )}
    </section>
  );
}

export const TitlePropTypes = {
  breadcrumbs: PropTypes.arrayOf(
    PropTypes.shape({
      href: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    }),
  ),
  children: PropTypes.node,
  gradientStyle: PropTypes.oneOf(_.keys(gradientStyles)),
  hideBorder: PropTypes.bool,
  info: PropTypes.node,
  secondaryButtons: PropTypes.node,
  title: PropTypes.node.isRequired,
};

PageTitle.propTypes = TitlePropTypes;

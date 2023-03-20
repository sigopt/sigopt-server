/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import smoothscroll from "smoothscroll";

import ParsedUrl from "../net/url";
import schemas from "../react/schemas";

const Navlink = function (props) {
  const parsedPath = new ParsedUrl(props.path);
  const parsedHref = new ParsedUrl(props.href);
  const className = classNames({
    "nav-link": true,
    active: parsedPath.path === parsedHref.path,
    [props.className || ""]: props.className,
    empty: props.isEmpty,
  });
  return (
    <a
      className={className}
      href={props.href}
      onClick={(e) => {
        if (props.onClick) {
          props.onClick(e);
        } else {
          const newTab = e.which === 2 || e.metaKey || e.ctrlKey;
          if (!newTab) {
            e.preventDefault();
            const element =
              parsedHref.path === parsedPath.path &&
              parsedHref.hash &&
              document.querySelector(parsedHref.hash);
            if (element) {
              smoothscroll(element);
            } else {
              props.navigator.navigateToAllowExternal(props.href);
            }
          }
        }
      }}
    >
      {props.children}
    </a>
  );
};
Navlink.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  href: PropTypes.string,
  isEmpty: PropTypes.bool,
  navigator: schemas.Navigator.isRequired,
  onClick: PropTypes.func,
  path: PropTypes.string.isRequired,
};
export default Navlink;

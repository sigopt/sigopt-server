/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import schemas from "../react/schemas";
import ui from "./ui";
import {Section} from "./section.js";
import {isDefinedAndNotNull} from "../utils";

const ParameterPriorsTable = function (props) {
  const parameters = props.experiment.parameters;
  return (
    <table className="table experiment-edit-table">
      <thead>
        <tr>
          <th>Parameter Name</th>
          <th>Prior Name</th>
          {/* Note: 2 empty headers here. 2 is current max attributes on priors, but names differ so no header */}
          <th />
          <th />
        </tr>
      </thead>
      <tbody>
        {_.chain(parameters)
          .filter((p) => p.prior)
          .map((p) => (
            <tr key={p.name}>
              <td>{p.name}</td>
              <td>{p.prior.name}</td>
              {isDefinedAndNotNull(p.prior.mean) && (
                <td>mean = {p.prior.mean}</td>
              )}
              {isDefinedAndNotNull(p.prior.scale) && (
                <td>scale = {p.prior.scale}</td>
              )}
              {isDefinedAndNotNull(p.prior.shape_a) && (
                <td>shape_a = {p.prior.shape_a}</td>
              )}
              {isDefinedAndNotNull(p.prior.shape_b) && (
                <td>shape_b = {p.prior.shape_b}</td>
              )}
            </tr>
          ))
          .value()}
      </tbody>
    </table>
  );
};
ParameterPriorsTable.propTypes = {
  experiment: schemas.Experiment.isRequired,
};

const ParameterPriorsReadOnlySection = function (props) {
  return (
    <Section
      infoClassName="parameter-prior-info"
      heading="Priors"
      sectionBody={<ParameterPriorsTable experiment={props.experiment} />}
    />
  );
};

export const ParameterPriorsSection = function (props) {
  const anyPriors = _.any(props.parameters, (p) => p.prior);
  const showPriors =
    anyPriors && ui.existingInteraction(props.interactionState);
  return (
    showPriors && (
      <ParameterPriorsReadOnlySection experiment={props.experiment} />
    )
  );
};

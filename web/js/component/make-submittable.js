/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

/**
 * A Higher-Order component that grants a component the ability to "Submit".
 * Tracks state of submission with `submitting` and `submitted` flags.
 * Useful for showing a loading spinner while submitting, and/or
 * success/error states after submission succeeds or fails.
 *
 * The most common usage will look like
 *
 * const Form = makeSubmittableComponent(class extends React.Component {
 *   render() {
 *     return [
 *       <button onClick={this.props.submit(submitFunction, successHandler, errorHandler)}/>,
 *       {this.props.submitting && <Spinner/>},
 *       {this.props.submitted &&  <CheckGlyph/>},
 *     ]
 *   }
 * }
 *
 * `submitFunction` will be a function that takes (success, error) callbacks.
 *   This is typically your submission logic (such as an API call)
 * Your `successHandler` will be called on submission success.
 * Your `errorHandler will be called on submission failure.
 *
 * The HOC provides the following props to the WrappedComponent:
 *   resetSubmissionState: A function the WrappedComponent can call to reset to the original state.
 *   submitted: True if this component has succesfully submitted. False otherwise
 *   submitting: True if there is a submission in progress. False otherwise
 *   submit: A function the WrappedComponent can call to trigger submission
 */
export default function makeSubmittableComponent(WrappedComponent) {
  const defaultState = {
    submitted: false,
    submitting: false,
  };

  class SubmittableComponent extends React.Component {
    static displayName = `Submittable(${WrappedComponent.displayName})`;

    state = _.clone(defaultState);

    resetSubmissionState = () => this.setState(defaultState);

    submit = (submitter, success, error) => {
      if (!this.state.submitting) {
        this.setState({submitting: true}, () => {
          submitter(
            (...args) => {
              this.setState({
                submitting: false,
                submitted: true,
              });
              return success && success(...args);
            },
            (...args) => {
              this.setState({submitting: false});
              return error && error(...args);
            },
          );
        });
      }
    };

    render() {
      const {fref} = this.props;
      return (
        <WrappedComponent
          {..._.omit(this.props, ["fref"])}
          resetSubmissionState={this.resetSubmissionState}
          submitted={this.state.submitted}
          submitting={this.state.submitting}
          submit={this.submit}
          ref={fref}
        />
      );
    }
  }

  return React.forwardRef((props, ref) => (
    <SubmittableComponent {...props} fref={ref} />
  ));
}

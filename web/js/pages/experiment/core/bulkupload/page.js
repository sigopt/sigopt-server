/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/report_file.less";

import _ from "underscore";
import React from "react";
import {parse} from "csv-parse";

import ExperimentPage from "../../page_wrapper";
import Spinner from "../../../../component/spinner";
import schemas from "../../../../react/schemas";
import ui from "../../../../experiment/ui";
import {DOCS_URL} from "../../../../net/constant";
import {excelUnsanitize} from "../../csvutils";
import {
  isDefinedAndNotNull,
  isUndefinedOrNull,
  maybeAsNumber,
  startsWith,
} from "../../../../utils";

class CsvDownloadForm extends React.Component {
  state = {
    loading: false,
    file: null,
  };

  propTypes = () => ({
    alertBroker: schemas.AlertBroker.isRequired,
    experiment: schemas.Experiment.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    loginState: schemas.LoginState.isRequired,
  });

  handleChange = (e) => {
    const file = e.target.files[0];
    this.setState({file});
  };

  handleSubmit = () => {
    if (this.state.file) {
      this.setState({loading: true});
      const reader = new FileReader();
      reader.onload = () => {
        const items = [];
        const parser = parse({
          cast: excelUnsanitize,
          columns: true,
          relax_column_count_less: true,
        });
        parser.on("readable", () => {
          let record;
          while ((record = parser.read()) !== null) {
            items.push(record);
          }
        });
        parser.on("end", () => {
          this.bulkUpload(null, items);
        });
        parser.on("error", (e) => {
          this.bulkUpload(e);
        });
        parser.write(reader.result);
        parser.end();
      };

      reader.readAsText(this.state.file);
    }
  };

  maybeAsBoolean = (text) => {
    if (_.isString(text)) {
      const lowered = text.toLowerCase();
      if (lowered === "true") {
        return true;
      } else if (lowered === "false" || lowered === "") {
        return false;
      }
    }
    return text;
  };

  maybeAsNumber = (text) => {
    if (text === "") {
      return null;
    } else {
      return maybeAsNumber(text);
    }
  };

  asAssignment = (experiment, assignmentName, value) => {
    const parameter = _.find(
      experiment.parameters,
      (p) => p.name === assignmentName,
    );

    if (parameter && _.contains(["int", "double"], parameter.type)) {
      return this.maybeAsNumber(value);
    } else {
      return value;
    }
  };

  parseAssignmentName = (k) => {
    if (startsWith(k, "parameter-")) {
      return k.slice("parameter-".length);
    } else if (startsWith(k, "conditional-")) {
      return k.slice("conditional-".length);
    } else {
      return k;
    }
  };

  bulkUpload = (err, data) => {
    if (err) {
      this.handleError(err);
      return;
    }

    const reservedColumns = [
      "failed",
      "created",
      "id",
      "task_name",
      "task_cost",
    ];
    const observations = _.map(data.reverse(), (d) => {
      const assignments = _.chain(d)
        .omit(reservedColumns)
        .omit((v, k) => startsWith(k, "metadata-"))
        .omit((v, k) => startsWith(k, "value"))
        .pairs()
        .map(([k, v]) => [this.parseAssignmentName(k), v])
        .map(([k, v]) => [k, this.asAssignment(this.props.experiment, k, v)])
        .filter((assignmentPair) => isDefinedAndNotNull(assignmentPair[1]))
        .object()
        .value();

      const metadata = _.chain(d)
        .pick((v, k) => startsWith(k, "metadata-"))
        .pairs()
        .map(([k, v]) => [k.slice("metadata-".length), v])
        .object()
        .mapObject(this.maybeAsNumber)
        .omit((v) => isUndefinedOrNull(v))
        .omit((v) => v === "")
        .value();

      const valuesByName = _.chain(d)
        .pick((v, k) => k === "value" || startsWith(k, "value-"))
        .pairs()
        .map(([k, v]) => ({
          name: startsWith(k, "value-") ? k.slice("value-".length) : "",
          value: this.maybeAsNumber(v),
        }))
        .map((value) => [value.name, value])
        .object()
        .value();

      _.each(d, (v, k) => {
        if (startsWith(k, "value_stddev")) {
          const metricName = k.slice("value_stddev-".length);
          const value = valuesByName[metricName];
          value.value_stddev = this.maybeAsNumber(v);
        }
      });

      const failed = this.maybeAsBoolean(d.failed);

      return {
        assignments: assignments,
        failed: failed,
        metadata: _.isEmpty(metadata) ? null : metadata,
        values: failed ? null : _.values(valuesByName),
        task: d.task_name,
      };
    });

    const upload = (remaining, dryRun) => {
      if (_.isEmpty(remaining)) {
        return Promise.resolve(null);
      } else {
        const batchSize = this.props.batchSize;
        if (!batchSize) {
          return Promise.reject(new Error("Missing batch size"));
        }
        const thisBatch = _.head(remaining, batchSize);
        const rest = _.tail(remaining, batchSize);
        return this.props.promiseApiClient
          .experiments(this.props.experiment.id)
          .observations("batch")
          .create({observations: thisBatch, dry_run: dryRun})
          .then(() => upload(rest, dryRun));
      }
    };

    upload(observations, true)
      .then(() => upload(observations, false))
      .then(this.handleSuccess, this.handleError);
  };

  handleSuccess = () => {
    this.fileUpload.value = "";
    this.setState({loading: false, file: null});
    this.props.alertBroker.show("Successfully uploaded CSV", "success");
  };

  handleError = (err) => {
    this.fileUpload.value = "";
    this.setState({loading: false, file: null});
    if (!err.message) {
      err.message = "There was an error during the upload process.";
    }
    this.props.alertBroker.show(err.message);
  };

  render() {
    return (
      <div className="input-form">
        <div className="form-group">
          <input
            className="file-input"
            name="bulk-file"
            onChange={this.handleChange}
            ref={(c) => (this.fileUpload = c)}
            type="file"
          />
        </div>
        <div className="form-group">
          {this.state.loading ? (
            <Spinner position="absolute" />
          ) : (
            <input
              className="btn btn-primary"
              disabled={!this.state.file}
              value="Import"
              onClick={this.handleSubmit}
            />
          )}
        </div>
      </div>
    );
  }
}

export default function ExperimentReportPage(props) {
  const headerLine = _.map(
    props.experiment.parameters,
    (p) => `parameter-${p.name}`,
  )
    .concat(
      _.flatten(
        _.map(props.experiment.metrics, (m) =>
          isDefinedAndNotNull(m.name)
            ? [`value-${m.name}`, `value_stddev-${m.name}`]
            : ["value", "value_stddev"],
        ),
      ).join(","),
    )
    .concat(props.experiment.tasks ? ["task_name,"] : []);

  const parameterLine = _.map(props.experiment.parameters, (p) => {
    if (!_.isEmpty(p.categorical_values)) {
      return p.categorical_values[0].name;
    } else if (p.type === "int") {
      return 1;
    } else {
      return 2.0;
    }
  })
    .concat(_.flatten(_.map(props.experiment.metrics, () => [1.2, 0.1])))
    .concat(
      props.experiment.tasks ? ui.getInitialTask(props.experiment).name : [],
    )
    .join(",");

  const exampleText = `${headerLine}\n${parameterLine}`;
  const historyDownloadLink = (
    <a href={`/experiment/${props.experiment.id}/historydownload`}>
      download your existing data
    </a>
  );
  const metadataLink = (
    <a href={`${DOCS_URL}/core-module-api-references/api-topics/metadata`}>
      metadata
    </a>
  );

  return (
    <ExperimentPage {...props} className="experiment-report-file-page">
      <div className="file-upload-help">
        <p>
          You can upload a CSV file to import your historical data. The CSV file
          must be in the following format:
        </p>
        <ul className="file-format">
          <li>
            The first row is headers, every row after that is an observation.
          </li>
          <li>
            There should be exactly one column per parameter, and the column
            should be titled <code>parameter-</code> + parameter name.
          </li>
          <li>
            The value for each row should be in a column titled{" "}
            <code>value</code>.
          </li>
          <li>
            To include a standard deviation, use the (optional) column{" "}
            <code>value_stddev</code>. You can leave values in this column blank
            to indicate that there is no standard deviation.
          </li>
          {props.experiment.tasks && (
            <li>
              The <code>Task</code> name for each row should be in a column
              titled <code>task_name</code>.
            </li>
          )}
          <li>
            To report failed observations, include the (optional) column{" "}
            <code>failed</code>. For failed observations, the value in the{" "}
            <code>failed</code> column is <code>true</code>, and the{" "}
            <code>value</code> and <code>value_stddev</code> columns are blank.
          </li>
          <li>
            Any columns with names that begin with <code>metadata-</code> will
            be interpreted as {metadataLink}.
          </li>
        </ul>
        <div className="download">
          <p>You can also {historyDownloadLink} in the same format.</p>
        </div>
        <div className="example-holder">
          <p className="example-description">Example:</p>
          <pre>{exampleText}</pre>
        </div>
        <CsvDownloadForm
          alertBroker={props.alertBroker}
          batchSize={props.batchSize}
          experiment={props.experiment}
          loginState={props.loginState}
          promiseApiClient={props.promiseApiClient}
        />
      </div>
    </ExperimentPage>
  );
}

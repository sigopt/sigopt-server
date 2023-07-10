/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/training_run/view.less";
import "./files.less";

import _ from "underscore";
import React from "react";
import classNames from "classnames";
import filesize from "filesize";

import DownloadGlyph from "../../../component/glyph/download";
import EyeGlyph from "../../../component/glyph/eye";
import FileGlyph from "../../../component/glyph/file";
import ImageGlyph from "../../../component/glyph/image";
import ModalInterior from "../../../component/modal/interior";
import RawModal from "../../../component/modal/raw";
import RunPageSection from "./section";
import SpinnerGif from "../../../component/spinner.gif";
import UpRightAndDownLeftFromCenterGlyph from "../../../component/glyph/up-right-and-down-left-from-center";
import {CodeBlock} from "../../../component/code_block";

const MimeType = ({mimeType}) => {
  const imageTypes = {
    apng: "APNG",
    bmp: "BMP",
    gif: "GIF",
    jpeg: "JPEG",
    png: "PNG",
    "svg+xml": "SVG",
    webp: "WebP",
  };
  const [type, subtype] = mimeType.split("/");
  if (type === "image") {
    return (
      <span>
        <ImageGlyph /> {imageTypes[subtype] || subtype}
      </span>
    );
  }
  return (
    <span>
      <FileGlyph /> {subtype.toUpperCase()}
    </span>
  );
};

class UserImage extends React.Component {
  state = {unavailable: false};

  componentDidMount() {
    this.mount();
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.state.unavailable && !prevState.unavailable) {
      setTimeout(
        () => this.state.unmounted || this.setState({unavailable: false}),
        10000,
      );
    }
  }

  componentWillUnmount() {
    this.unmount();
  }

  mount = () => this.setState({mounted: true});
  unmount = () => this.setState({unmounted: true});

  render() {
    const {file} = this.props;
    // NOTE: It appears that server-side rendering has an issue with the onError attribute
    // of the img element. Rendering the component after it is mounted fixes the issue.
    return this.state.mounted ? (
      <img
        className="user-file"
        src={this.state.unavailable ? SpinnerGif : file.download.url}
        title={file.filename || file.name}
        onError={() => this.setState({unavailable: true})}
      />
    ) : null;
  }
}

class FilesModal extends React.Component {
  modal = React.createRef();

  componentDidUpdate(prevProps) {
    if (prevProps.fullscreen !== this.props.fullscreen) {
      if (this.props.fullscreen) {
        this.modal.current.show();
      } else {
        this.modal.current.hide();
      }
    }
  }

  render() {
    if (!this.props.selectedFile) {
      return null;
    }
    return (
      <RawModal ref={this.modal} onClose={this.props.exitFullscreen}>
        <ModalInterior
          showClose={true}
          title={
            this.props.selectedFile.name || this.props.selectedFile.filename
          }
        >
          <div className="fullscreen-viewer">
            <UserImage
              key={this.props.selectedFile.id}
              file={this.props.selectedFile}
            />
          </div>
        </ModalInterior>
      </RawModal>
    );
  }
}

class FilesSectionContent extends React.Component {
  state = {fullscreen: false, selectedFile: null};

  onModalClose = () => this.setState({selectedFile: null});

  componentDidMount() {
    this.setDefaultFileSelection();
  }

  componentDidUpdate() {
    this.setDefaultFileSelection();
  }

  setDefaultFileSelection() {
    this.setState((state) => {
      if (!state.selectedFile) {
        return {selectedFile: _.first(this.props.files)};
      }
      return null;
    });
  }

  exitFullscreen = () => this.setState({fullscreen: false});

  selectFile = (file, fullscreen) =>
    this.setState({selectedFile: file, fullscreen});

  onFileRowClicked = (file) => {
    const BOOTSTRAP_SCREEN_MD_MAX = 1200;
    this.selectFile(file, window.innerWidth < BOOTSTRAP_SCREEN_MD_MAX);
  };

  render() {
    const {files} = this.props;
    return (
      <>
        <FilesModal
          files={this.props.files}
          selectedFile={this.state.selectedFile}
          fullscreen={this.state.fullscreen}
          exitFullscreen={this.exitFullscreen}
        />
        <div className="files-section">
          <div className="files">
            <table className="table">
              <thead>
                <tr>
                  <th className="thumbnail-header" />
                  <th className="name-header">Name</th>
                  <th className="filename-header">Filename</th>
                  <th className="type-header">Type</th>
                  <th className="size-header">Size</th>
                  <th className="controls-header" />
                </tr>
              </thead>
              <tbody>
                {_.map(files, (file) => (
                  <tr
                    className={classNames("file", {
                      selected: file === this.state.selectedFile,
                    })}
                    onClick={() => this.onFileRowClicked(file)}
                  >
                    <td>
                      <UserImage file={file} />
                    </td>
                    <td>{file.name}</td>
                    <td>{file.filename}</td>
                    <td>
                      <MimeType mimeType={file.content_type} />
                    </td>
                    <td>
                      <p>{filesize(file.content_length)}</p>
                    </td>
                    <td>
                      <a
                        className="file-control btn download-btn"
                        href={file.download.url}
                        download={true}
                      >
                        <DownloadGlyph />
                      </a>
                      <span className="file-control-spacing preview-btn" />
                      <a
                        className="file-control btn preview-btn"
                        onClick={() => this.selectFile(file, false)}
                      >
                        <EyeGlyph />
                      </a>
                      <span className="file-control-spacing fullscreen-btn" />
                      <a
                        className="file-control btn fullscreen-btn"
                        onClick={() => this.selectFile(file, true)}
                      >
                        <UpRightAndDownLeftFromCenterGlyph />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="preview">
            {this.state.selectedFile ? (
              <>
                <div className="preview-content-wrapper">
                  <UserImage
                    key={this.state.selectedFile.id}
                    file={this.state.selectedFile}
                  />
                  <a
                    className="file-control btn fullscreen-btn"
                    onClick={() => this.setState({fullscreen: true})}
                  >
                    <UpRightAndDownLeftFromCenterGlyph />
                  </a>
                </div>
                <h3>
                  {this.state.selectedFile.name ||
                    this.state.selectedFile.filename}
                </h3>
              </>
            ) : null}
          </div>
        </div>
      </>
    );
  }
}

const ActiveMessage = () => (
  <p>
    Images will be uploaded while the run is active if{" "}
    <code>sigopt.log_image</code> is executed in your code.
  </p>
);

const EmptyMessage = () => (
  <>
    <p>
      No files were uploaded for your run. To upload images and see them in
      future runs, add the following function to your code:
    </p>
    <CodeBlock language="python">sigopt.log_image(image, name=name)</CodeBlock>
  </>
);

export default (props) => (
  <RunPageSection
    ActiveMessage={ActiveMessage}
    Content={FilesSectionContent}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.files)}
    fullWidth={true}
    title="Files"
    {...props}
  />
);

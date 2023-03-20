/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import PageTitle from "../../../component/page_title";
import {Tab, Tabs} from "../../../component/tabs";

export const SignUpLoginTitle = ({currentPage}) => {
  return (
    <>
      <Tabs active={currentPage}>
        <Tab label="Log In" href="/login" />
        <Tab label="Sign Up" href="/signup" />
      </Tabs>
      {currentPage === "Sign Up" && <PageTitle title="Sign Up" />}
    </>
  );
};

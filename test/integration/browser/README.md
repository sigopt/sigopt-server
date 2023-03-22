<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

# Automated Browser Tests

These tests are meant to automate our web flows from an end-user's perspective,
preventing regressions with our UI as well as with front-end code that may not be touched by functional or unit tests.
This way, we can quickly check if our critical flows such as logging in and creating an experiment are not broken on our site.

## Playwright tests

Write browser tests with Playwright by using the `page` or `logged_in_page` fixture.
See documentation for Playwright's page [here](https://playwright.dev/python/docs/api/class-page).
Use the script `./test/playwright_codegen.sh` to help write new tests.

## _Deprecated_ Selenium tests

Selenium tests use the `driver` and `logged_in_driver` fixtures.
These are instances of `SigOptWebDriver`. The `SigOptWebDriver` is deprecated due to flakiness.
Please use Playwright instead.

## Debugging

When the test runner container starts (ie. while `test/test_dev_env.sh` is running) a VNC session will become available at `localhost:5900`.
Use a VNC client like [Real VNC Viewer](https://www.realvnc.com/en/connect/download/viewer/) to view the browser as tests are running.
Use `pdb` to place a breakpoint so that you have time to connect the VNC session and step through each line in the test code.

```python
import pdb; pdb.set_trace()
```

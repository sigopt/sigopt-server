/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "highlight.js/styles/default.css";

import bash from "highlight.js/lib/languages/bash";
import dockerfile from "highlight.js/lib/languages/dockerfile";
import hljs from "highlight.js/lib/core";
import java from "highlight.js/lib/languages/java";
import json from "highlight.js/lib/languages/json";
import matlab from "highlight.js/lib/languages/matlab";
import plaintext from "highlight.js/lib/languages/plaintext";
import python from "highlight.js/lib/languages/python";
import r from "highlight.js/lib/languages/r";
import yaml from "highlight.js/lib/languages/yaml";

hljs.registerLanguage("bash", bash);
hljs.registerLanguage("java", java);
hljs.registerLanguage("python", python);
hljs.registerLanguage("r", r);
hljs.registerLanguage("json", json);
hljs.registerLanguage("matlab", matlab);
hljs.registerLanguage("yaml", yaml);
hljs.registerLanguage("dockerfile", dockerfile);
hljs.registerLanguage("plaintext", plaintext);

export default hljs;

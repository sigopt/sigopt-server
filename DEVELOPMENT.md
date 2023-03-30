<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

# Development Setup

Use these steps if you want to set up to contribute to development of SigOpt. In order to install for local development, you will want to do the following steps, which we've laid out for both Mac and Ubuntu Linux. (We haven't tested on other distros, but we think that the only difference should be the package manager commands.)

## Get the Code

Checkout the repository:

```bash
git clone https://github.com/sigopt/sigopt-server.git
cd sigopt-server
```

<details>
<summary> Development Setup for Mac </summary>

Because OS X doesn't have a command line package manager that comes default, we suggest using the Homebrew package manager. Then you will need to get on the correct development version of Python, and finally install all of the necessary packages for local development.

### Get OS X Packages

First, install Homebrew from http://brew.sh/ to manage your OS X packages. Then run:

```bash
brew update
brew install \
  autoconf \
  automake \
  coreutils \
  gcc@8 \
  jq \
  libffi \
  libtool \
  libxml2 \
  libxmlsec1 \
  node@18 \
  pkg-config \
  pyenv \
  yarn
brew install --cask chromedriver
```

In order to better expose the `libxml2` dependency, run:

```
brew link libxml2 --force
echo 'export PKG_CONFIG_PATH="/usr/local/opt/libxml2/lib/pkgconfig"' | tee -a ~/.bash_profile | tee -a ~/.zshrc
exec "$SHELL"  # to load the changes you just made
```

### Python Setup

We run python 3.10.7

To install this, we use a python version manager called pyenv.

To install 3.10.7 and make it the default pyenv version, you can run `pyenv install 3.10.7 && pyenv global 3.10.7`.

To initialize pyenv whenever you open a terminal window, add the `pyenv init` command to your `.bash_profile` or `.zshrc`

```
echo -e 'if command -v pyenv &>/dev/null; then eval "$(pyenv init --path)"; fi' | tee -a ~/.bash_profile | tee -a ~/.zshrc
exec "$SHELL"  # to load the changes you just made
```

Run `echo $PATH` to confirm that `pyenv` is now part of your `PATH` variable.
If you don't see `pyenv`, then try reloading your shell again and that the desired changes have been made in the shell profile (`.bash_profile` or `.zshrc`).

Next, we add a symlink.
To have the `python` command default to `python3.10`, we symlink python3.10 to python

```bash
mkdir -p ~/bin && ln -s `which python3.10` ~/bin/python
export PATH=~/bin:$PATH
echo 'export PATH=~/bin:$PATH' | tee -a ~/.bash_profile | tee -a ~/.zshrc
```

To confirm the symlink, `which python` should now show the same path as `which python3.10`.

</details>

<details>
<summary>Development Setup for Ubuntu</summary>

## Install OS level Packages

Install the necessary development packages for Ubuntu with this command:

```bash
sudo apt-get install \
              automake \
              autoconf \
              gcc      \
              jq       \
              libffi-dev \
              libxml2-dev \
              libxmlsec1-dev \
              make     \
              nodejs   \
              pkg-config \
              yarn     \
              zlib1g-dev
```

You will need the 3.10.7 version of Python that we use for development, so you will need to run

```
sudo ./scripts/compile/compile_and_install_python.sh
```

Which should install the correct version of python for you. You might need to run wget, get-pip and pip install docker commands again, depending on exactly which version of python you had before and after.

</details>

## Install the Python Packages

In either Mac or Ubuntu, run the following commands to set up a virtualenv, so the dependencies necessary for local development don't get into conflict with other python packages you need for other programs and development.

```bash
pip install virtualenv
cd sigopt-server
virtualenv -p `which python3.10` venv/3.10
```

To start the virtual environment manually, run:

```bash
source venv/3.10/bin/activate
```

Deactivate when finished:

```bash
deactivate
```

## Codebase Setup

First, activate your virtual environment.

Next, run:

```bash
make update
```

## Setting up services

To setup SigOpt services, you must have Docker installed.

To setup and start services required by SigOpt in Docker, run `./scripts/launch/start_zigopt_services.sh`.
Then run `make fix-db` to setup the postgres database in the postgres container.
`docker ps` should show the running services including `postgres` and `redis`.

_Tips_

- You can access Postgresql with `docker exec -ti sigopt-server-postgres-1 psql -U postgres` and Redis with `docker exec -ti sigopt-server-redis-1 redis-cli`.
- View all docker containers with `docker ps -a`.
- Services will automatically start on boot.
- Stop services with `./scripts/launch/stop_zigopt_services.sh`.
- Remove a service with `docker rm -f [container_name]` ex. `docker rm -f sigopt-server-postgres-1` and recreate it with `./scripts/launch/start_zigopt_services.sh`.

## Setting up local TLS certs

In order to provide secure connections you will create new, locally generated TLS certificates, and you will need to add them to your trust stores to be able to interact with SigOpt, either through the client in your code or to view the results of your experiments on the web. If you already have TLS certificates- and if you aren't sure you probably don't- you can place them as `tls.crt` and `tls.key` in the `artifacts/tls` directory of the sigopt-server install and they should work just fine (presuming they are in PEM encoded format). If you are using these generated self-signed certificates, you will need to add the `root-ca.crt` into your keychain or you will get a lot of errors about unsafe and insecure connections.

From the terminal in the `sigopt-server` directory you created in the git clone command above, type:

```bash
./tools/tls/generate_root_ca.sh
./tools/tls/generate_san_cert.sh
shred -u ./artifacts/tls/root-ca.key
```

The two scripts first created a root certificate, then a usable certificate signed by that root-ca. You will need to add the file `root-ca.crt` generated in the `artifacts/tls` directory into your keychain if you are using the generated certificates, and then run

```bash
echo "127.0.0.1 sigopt.ninja" | sudo tee -a /etc/hosts
```

This will make sure that the self-signed certificates match the URL you are using. In order to protect you as much as possible with this self-signed cert, we then did a thorough, over-writing delete on the original key file associated with that certificate after we created a child certificate, so no attacker could cause mischief on your machine with it. If you are using other certificates you can just delete the `root-ca.crt` file and replace the `tls.crt` and `tls.key` files with your own certificates and you should be good to go.

Note that the creation script for both certs will pause in your default editor, most often `vi` to let you edit who owns the certs, if you wish to change the defaults you can. To learn how to navigate vi, click [here](https://www.cs.colostate.edu/helpdocs/vi.html), but if you just want to accept the defaults you can press `<escape>:wq` and it will advance. You should need to do this twice.

<details>
<summary>Local TLS Caveats</summary>

- To run the python-client against your local API, set the appropriate environment variables:

  ```bash
  export SIGOPT_API_TOKEN='YOUR_LOCAL_TOKEN'  # find your token at https://sigopt.ninja:4443/tokens/info, or use the default 'client_token'
  export SIGOPT_API_URL='https://sigopt.ninja:4443/api'
  export SIGOPT_APP_URL='https://sigopt.ninja:4443'
  SIGOPT_SERVER_DIR=/path/to/sigopt-server
  export SIGOPT_API_VERIFY_SSL_CERTS="$SIGOPT_SERVER_DIR/artifacts/tls/root-ca.crt"
  ```

- To run the connection-style python-client against your local API:

  ```python
  sigopt_dir = os.getenv('SIGOPT_SERVER_DIR')
  ca_certs_path = os.path.join(sigopt_dir, 'artifacts', 'tls', 'root-ca.crt')

  conn = Connection(client_token='YOUR_LOCAL_TOKEN')  # find your token at https://sigopt.ninja:4443/tokens/info or use the default 'client_token'
  conn.set_api_url('https://sigopt.ninja:4443/api')
  conn.set_verify_ssl_certs(ca_certs_path)
  ```

- To run the java-client against your local API:

  ```bash
  export JAVA_HOME="$($(dirname $(readlink $(which java)))/java_home)"
  sudo $JAVA_HOME/bin/keytool -import -alias sigopt-root-ci -keystore $JAVA_HOME/jre/lib/security/cacerts -file ./artifacts/tls/root-ca.crt

  ```

  Keystore(not sudo) password is changeit by default

- If you're running the web outside of the provided container environment:
  - set `NODE_EXTRA_CA_CERTS = $SIGOPT_SERVER_DIR/artifacts/tls/root-ca.crt` in the directory running the web
  </details>

## How to run everything locally

```bash
./scripts/launch/all_live.sh [optional_config_file]
```

This will start Web, API and message processors (qworkers) in development mode,
as well as a few other services.
The other services are:

- `nginx`: Reverse proxy that terminates TLS.
- `protowatch`: recompile your protobuf when you make changes to files in `src/protobuf/`.
- `smtp`: SMTP server that includes HTTP endpoints to query inboxes (used by test suite).

After you execute this command the API should be running [here](https://sigopt.ninja:4443/api)!

The website should also be [running](https://sigopt.ninja:4443/)! You may need to wait a few minutes for the code to compile. When you have a proper login page try signing in with either one of our default accounts:

**Organization Owner**

- Email: owner@sigopt.ninja
- Password: owner

**Regular User**

- Email: user@sigopt.ninja
- Password: password
- API Token: `client_token`

## How to run the repl

```bash
./scripts/launch/repl.sh
```

This will start the REPL environment. To quit, type `exit`.

# Linting

We use linting to achieve coding style and consistency.
Linting runs in our test infrastructure on CircleCI.
If you have lint errors your test suite will not pass and you will not be able to merge your changes.

Setup automatic pre-commit linter:

```bash
make setup-pre-commit
```

Lint everything else:

```bash
# attempts to fix errors
./lint
```

# Dead code

We use `vulture` to check for unused python code (methods, variables, property, etc).

```bash
make vulture
```

We use the `webpack-deadcode-plugin` to look for unused files in our web code.

```bash
make web-dead-code
```

# Testing

## Unit tests

To run web unit tests:

```bash
yarn test
```

To run python unit tests:

```bash
./test/unit_tests.sh
```

To run a specific unit test in python:

```bash
./test/unit_tests.sh "./path-to-unit-test-file::TestClass::test_method_name"
```

## Integration tests

```bash
# All integration tests
./test/test_dev_env.sh test/integration

# services
./test/test_dev_env.sh test/integration/service

# api
./test/test_dev_env.sh test/integration/v1

# browser
./test/test_dev_env.sh test/integration/browser

# single integration test
./test/test_dev_env.sh "path-to-file.py::TestClassName::test_method_name"

# local client integration test
./scripts/launch/compose.sh run test-client test/run_client_integration_tests.sh [sigopt-python-git-reference]

```

To see how to debug browser tests, check out the [browser test readme](/test/integration/browser/README.md).

## REST Documentation

We use [Flassger](https://github.com/flasgger/flasgger) to allow us to store REST api documentation (in OpenAPI3 format) as docstrings on endpoints. To view that documentation, visit [our Github pages](https://friendly-disco-6245ceab.pages.github.io/#/). To view the standard [visit swagger.io](https://swagger.io/docs/specification/about/)

If you want to run it locally to check if you have written correct yaml, run

`./scripts/launch/all_live.sh --documentation`

This will leave a copy of the new doc file at `artifacts/swagger.json`. Then to validate, run

`node ./ci/validate_swagger.js`

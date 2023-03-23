<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

## Code Dependencies

Our scripts use the latest version of Bash.
All machines run Python 3.10.7, and pip 22.1.2
Python dependencies are listed in the files: `requirements.txt`, `requirements-dev.txt`.

Our web servers run the latest version of Node 12.
Node dependencies are listed in `yarn.lock`.

We store data in the following:

- Postgres 11.2 for durable application data
- Redis 3.2 for transient suggestion data
- Minio 1.19.2 for user uploaded file data

## Production services

This lists the third party service providers we use to run SigOpt.
The configuration of these services in specfied in the appropriate config file
(such as config/development.json for development).
Most of these can be disabled to run in a minimal environment.

We use redis for queues and storing unprocessed suggestions.
The `"redis":{}` section of the config file points at the redis server.
The "password" field needs to be populated.
Disabling Redis is not supported
The queues are what pass async messages from the API server to the qworker machines.
In development, we set `"queue":{"type": "sync"}`,
which means that we don't use a queue and instead just process the message synchronously.
In production environments, we use `"queue":{"type": "async"}` to processes messages
asynchronously via offline workers.
Redis queue names are configured in the `"queue":{"message_groups": {}}"` section of the config file.
Every queue name must have an associated provider in the `"queues:[]"` section.
Different messages are sent through different queues (to enable prioritizing handling of certain message types).
In production we have two queues -
one for analytics messages, and one for optimization messages.

We use postgres 11.2 for hosting our production data.
The `"db":{}` section of the config file points at the DB.
The default config is already set, but the "username" and "password" fields need to be populated.
The database is initially set up by running `./createdb PATH_TO_CONFIG_FILE --fake-data`.
`--fake-data` will populate the database with placeholder data,
but it critically creates a user with email `owner@sigopt.ninja` and password `owner`
which can be used to invite other users.
You'll want to delete this fake data once you've created a login for yourself.
Disabling the DB is not supported.

We store user-generated files associated with each run in MinIO, version 1.19.2.

Email is sent via sendrid.
Specify the `"sendgrid":{"username":"","password":""}` configs
and set `"email":{"enabled":true,"method":"sendgrid"}` to enable.

You'll need a developer license for AG Grid Enterprise: https://www.ag-grid.com/license-pricing.php
Specify `"ag-grid":{"license":"YOUR_LICENSE_KEY_HERE"}` to include your license key.
Without a license key, the software will be functional but a watermark will be shown on AG Grid Tables.

<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

## Code Dependencies

Our scripts use the latest version of Bash.
The API requires Python 3.10 and the website requires Node 18.
Python dependencies are listed in the files: `requirements.txt`, `requirements-dev.txt`.
Node dependencies are listed in `yarn.lock`.

We store data in the following:

- Postgres 11.2 for durable application data
- Redis 5 for transient suggestion data
- Minio 1.19 for user uploaded file data

## Services

This lists the services we use to run SigOpt.
The configuration of these services in specfied in the appropriate config file
(such as config/development.json for development).
Most of these can be disabled to run in a minimal environment.

We use redis for queues and storing unprocessed suggestions.
The `"redis":{}` section of the config file points at the redis server.
Disabling Redis is not supported
The queues are what pass async messages from the API server to the qworker machines.
We use `"queue":{"type": "async"}` to processes messages asynchronously via offline workers.
Changing `"type"` to `"sync"` will process messages synchronously during API requests.
Redis queue names are configured in the `"queue":{"message_groups": {}}"` section of the config file.
Every queue name must have an associated provider in the `"queues:[]"` section.
Different messages are sent through different queues (to enable prioritizing handling of certain message types).
In production we have two queues -
one for analytics messages, and one for optimization messages.

We use postgres 11.2 as the DBMS for most of our persistent data.
The `"db":{}` section of the config file points at the DB.
The database is initially set up by running `python -m zigopt.utils.create_database PATH_TO_CONFIG_FILE`.
`--fake-data` will populate the database with placeholder data,
but it critically creates a user with email `owner@sigopt.ninja` and password `owner`
which can be used to invite other users.
Disabling the DB is not supported.

We store user-generated files associated with each run in MinIO, version 1.19.
User-generated files can be disabled with `"user_uploads": {"s3": {"enabled": false}}".

We also store web session data in MinIO. This is required for running the website and cannot be disabled.

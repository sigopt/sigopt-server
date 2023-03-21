# Requirements scripts

The scripts in this directory were created to make updating requirements easy.

## Freezing python requirements

After editing requirements in `requirements-to-freeze.txt`, you will need to freeze the requirements to persist them.
This can be done by running `./scripts/requirements/freeze_requirements.sh`, which will update `requirements.txt`.
Finally, commit both `requirements-to-freeze.txt` and `requirements.txt`.

## Editing yarn packages

Run `./scripts/requirements/yarn_command.sh add X` to add the package `X`.
All yarn commands should work.
Finally, commit both `package.json` and `yarn.lock`.
Your `node` image will be updated, so you can now start using this new package configuration in development.

#!/usr/bin/env bash
set -e
set -o pipefail

python3 docker/image_builder.py --build-tag freeze-reqs python

# NOTE: qmcpy gets frozen as the following every time:
#   # Editable install with no version control (qmcpy==1.2)
#   -e /usr/local/lib/python3.10/site-packages
# need to filter it out and replace with qmcpy==1.2
docker run -i --rm \
  --volume="$(pwd):/sigopt-server" \
  sigopt/python:freeze-reqs \
  bash -eo pipefail \
  <<EOF
apt-get update -yqq
apt-get install -yqq build-essential
python -mvenv /tmp/venv
source /tmp/venv/bin/activate
pip install --no-cache-dir --upgrade -r /sigopt-server/requirements-to-freeze.txt
pip freeze | sed --expression='/^-e \\/usr\\/local\\/lib\\/python.*\\/site-packages$/d' --expression='s/^.*(qmcpy==\\(.*\\))$/qmcpy==\\1/g' >/sigopt-server/requirements.txt
EOF

# make sure we're using a secure version of setuptools
echo "setuptools==65.6.3" >>requirements.txt

# sort the lines and add a comment
_tmp="$(mktemp)"
sort --ignore-case requirements.txt | grep -v site-packages >>"$_tmp"
echo '# auto-generated from scripts/requirements/freeze_requirements' >requirements.txt
cat "$_tmp" >>requirements.txt
rm "$_tmp"

echo "Please commit changes to requirements.txt, rebuild images and restart your development environment to use the new modules"

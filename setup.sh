#!/usr/bin/env bash

set -e
set -o pipefail

export COMPOSE_PROJECT_NAME=sigopt-server
echo "build-docker-images"
if ! ./scripts/compile/build_docker_images.sh; then
  echo "Failed to build-docker-images. This is most likely because of a disk space error with your docker allocation. You can try running: docker system prune -a to clear up space."
  exit 1
fi
echo "protocompile"
if ! ./scripts/dev/compile_protobuf_in_docker.sh; then
  echo "Failed to protocompile"
  exit 1
fi
echo "start zigopt_services"
if ! ./scripts/launch/start_zigopt_services.sh; then 
  echo "Failed to start zigopt services"
  exit 1
fi
echo "Initializing database..."
if ./scripts/dev/createdb_in_docker.sh config/development.json --fake-data --drop-tables; then 
  echo "Database ready."
else
  echo "Failed to initialize database!"
  exit 1
fi
echo "Initializing file storage..."
if ./scripts/launch/compose.sh run --rm init-minio-filestorage; then
  echo "File storage ready."
else
  echo "Failed to initialize file storage!"
  exit 1
fi
echo "Initializing session storage..."
if ./scripts/launch/compose.sh run --rm init-minio-cookiejar; then
  echo "Session storage ready."
else
  echo "Failed to initialize session storage!"
  exit 1
fi
echo "make root cert"
if ! ./tools/tls/generate_root_ca.sh; then
  echo "Failed to generate root cert"
  exit 1
fi

CA_PATH="$(pwd)/artifacts/tls/root-ca.crt"
export SIGOPT_API_VERIFY_SSL_CERTS=$CA_PATH
export NODE_EXTRA_CA_CERTS=$CA_PATH
echo "make leaf cert"
if ./tools/tls/generate_san_cert.sh; then 
  echo "Secure root cert"
  shred -u ./artifacts/tls/root-ca.key  
else
  echo "Failed to generate leaf cert"
  exit 1
fi

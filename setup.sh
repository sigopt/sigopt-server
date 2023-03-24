#!/usr/bin/env bash

set -e
set -o pipefail

export COMPOSE_PROJECT_NAME=sigopt-server-deploy
export sigopt_server_config_file="${sigopt_server_config_file:-config/sigopt.yml}"
export TAG=latest
echo "Checking docker..."
if docker ps -q >/dev/null; then
  echo "Docker is running."
else
  echo "Could not connect to Docker! It might not be running or you might not have permission to access the Docker socket."
  exit 1
fi
echo "build-docker-images"
if ! ./scripts/compile/build_docker_images.sh; then
  echo "Failed to build-docker-images. This is most likely because of a disk space error with your docker allocation. You can try running: docker system prune -a to clear up space."
  exit 1
fi

echo "Generating root certificate and key..."
if ./tools/tls/generate_root_ca.sh; then
  echo "Root certificate at artifacts/tls/root-ca.crt"
else
  echo "Failed to generate root certificate!"
  exit 1
fi
CA_PATH="$(pwd)/artifacts/tls/root-ca.crt"
export SIGOPT_API_VERIFY_SSL_CERTS=$CA_PATH
export NODE_EXTRA_CA_CERTS=$CA_PATH
echo "Generating leaf certificate and key..."
if ./tools/tls/generate_san_cert.sh; then 
  echo "Leaf certificate and key at artifacts/tls/tls.*"
  shred -u ./artifacts/tls/root-ca.key  
  rm -f artifacts/tls/root-ca.srl
else
  echo "Failed to generate leaf certificate!"
  exit 1
fi

MINIO_ROOT_PASSWORD="$(./tools/secure/generate_random_string.sh)"
export MINIO_ROOT_PASSWORD
echo "Starting required services..."
if docker-compose --file=docker-compose.yml up --detach minio postgres redis; then 
  echo "Required services have started."
else
  echo "Failed to start required services!"
  exit 1
fi
echo "Initializing database..."
if docker-compose --file=docker-compose.yml run --rm createdb; then 
  echo "Database ready."
else
  echo "Failed to initialize database!"
  exit 1
fi
echo "Initializing file storage..."
if docker-compose --file=docker-compose.yml run --rm init-minio-filestorage; then
  echo "File storage ready."
else
  echo "Failed to initialize file storage!"
  exit 1
fi
echo "Initializing session storage..."
if docker-compose --file=docker-compose.yml run --rm init-minio-cookiejar; then
  echo "Session storage ready."
else
  echo "Failed to initialize session storage!"
  exit 1
fi

echo "Setup complete. You are now ready to start SigOpt Server with ./start.sh"

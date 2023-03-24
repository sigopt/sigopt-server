#!/usr/bin/env bash
set -e
set -o pipefail

: "${TLS_PATH:=artifacts/tls}"
: "${ROOT_CA:="${TLS_PATH}/root-ca.crt"}"
: "${ROOT_CA_KEY:="${TLS_PATH}/root-ca.key"}"
: "${NAME:=tls}"
: "${CN:=sigopt.ninja}"

if [ ! -f "$ROOT_CA" ] || [ ! -f "$ROOT_CA_KEY" ]; then
  >&2 echo "Please create a root certificate authority with ./tools/tls/generate_root_ca.sh"
  exit 1
fi

CONFIG="$(mktemp)"

cat >"$CONFIG" <<EOF
# SigOpt leaf certificate configuration

[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = US
ST = California
L = San Francisco
O = SigOpt Inc.
OU = Engineering
CN = $CN

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = $CN
DNS.2 = *.$CN
EOF

"${EDITOR:-vim}" "$CONFIG"

mkdir -p "$TLS_PATH"

openssl genrsa \
  -out "${TLS_PATH}/${NAME}.key" \
  2048

openssl req \
  -new \
  -key "${TLS_PATH}/${NAME}.key" \
  -out "${TLS_PATH}/${NAME}.csr" \
  -reqexts req_ext \
  -config "$CONFIG"

# NOTE: TLS certs starting Sept 1 2020, can't be more than 398 days
# https://www.ssl.com/blogs/apple-limits-ssl-tls-certificate-lifetimes-to-398-days/
openssl x509 \
  -req \
  -in "${TLS_PATH}/${NAME}.csr" \
  -CA "$ROOT_CA" \
  -CAkey "$ROOT_CA_KEY" \
  -CAcreateserial \
  -out "${TLS_PATH}/${NAME}.crt" \
  -days 397 \
  -extfile "$CONFIG" \
  -extensions req_ext \
  -sha256

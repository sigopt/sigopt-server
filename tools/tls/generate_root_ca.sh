#!/usr/bin/env bash
set -e
set -o pipefail

: "${TLS_PATH:=artifacts/tls}"
: "${NAME:=root}"

CONFIG="$(mktemp)"

CN="SigOpt ${NAME} $(date +%F) CA"
cat >"$CONFIG" <<EOF
# SigOpt root certificate configuration

[ req ]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn

[ dn ]
C = US
ST = California
L = San Francisco
O = SigOpt Inc.
OU = Engineering
CN = $CN
EOF

"${EDITOR:-vim}" "$CONFIG"

mkdir -p "$TLS_PATH"

openssl genrsa \
  -out "${TLS_PATH}/${NAME}-ca.key" \
  4096

openssl req \
  -x509 \
  -new \
  -nodes \
  -key "${TLS_PATH}/${NAME}-ca.key" \
  -sha256 \
  -days 4096 \
  -out "${TLS_PATH}/${NAME}-ca.crt" \
  -config "$CONFIG"

if [ "$(uname -a)" = "Darwin" ]; then
  cat > "$TLS_PATH/_README" <<EOF
1.Open Keychain Access app
2.Drag ${NAME}-ca.crt into Keychain Access
3.Locate $CN and double click
4.Open the "Trust" section
5.Under "Secure Sockets Layer (SSL)" set to "Always Trust"
EOF
  open "$TLS_PATH"
fi

#!/usr/bin/env bash
# Generate a self-signed TLS certificate for local development.
# Run once before `docker compose up`:
#
#   bash infra/nginx/gen-dev-certs.sh
#
# Produces:
#   infra/nginx/ssl/cert.pem
#   infra/nginx/ssl/key.pem
#
# These files are gitignored. In production use real certs from Let's Encrypt
# or your CA and mount them at the same paths.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="$SCRIPT_DIR/ssl"

mkdir -p "$SSL_DIR"

if [[ -f "$SSL_DIR/cert.pem" && -f "$SSL_DIR/key.pem" ]]; then
  echo "Certificates already exist at $SSL_DIR — skipping generation."
  echo "Delete them and re-run this script to regenerate."
  exit 0
fi

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$SSL_DIR/key.pem" \
  -out    "$SSL_DIR/cert.pem" \
  -subj   "/C=RU/ST=Moscow/L=Moscow/O=Attribly/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo ""
echo "Self-signed certificate generated:"
echo "  cert: $SSL_DIR/cert.pem"
echo "  key:  $SSL_DIR/key.pem"
echo ""
echo "Valid for 365 days. Browser will show a security warning — this is expected for local dev."

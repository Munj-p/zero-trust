#!/bin/bash
# Wrapper script to handle authentication
if [ -z "$1" ]; then
  echo "Usage: zt-login <password>"
  exit 1
fi

curl --noproxy "*" -s -X POST -H "Content-Type: application/json" \
  -d "{\"method\": \"login\", \"user\": \"dev_user\", \"password\": \"$1\"}" \
  http://localhost:5000/login

echo "" # New line for clean output

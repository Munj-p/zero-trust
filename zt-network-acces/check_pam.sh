#!/bin/bash
SESSION_FILE="/var/run/zt_session"

if [ ! -f "$SESSION_FILE" ]; then
  exit 1
fi

EXPIRY=$(cat "$SESSION_FILE")
CURRENT=$(date +%s)

# Check if current time is less than expiry time
if (($(echo "$CURRENT < $EXPIRY" | bc -l))); then
  exit 0 # Allow Sudo
else
  echo "Zero Trust: Session Expired. Run 'zt-login <password>' to renew."
  exit 1 # Deny Sudo
fi

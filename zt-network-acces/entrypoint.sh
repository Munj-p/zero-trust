#!/bin/bash

echo "[INIT] Starting OPA Policy Engine..."
# Start OPA in background
/usr/local/bin/opa run --server --addr :8181 /opt/zt/policy.rego &
sleep 2

echo "[INIT] Starting Zero Trust Controller..."
# Start Python Controller in background
python3 /opt/zt/zt_controller.py &
sleep 2

echo "[INIT] Locking Network (IPTables)..."
# 1. Allow Loopback (Localhost traffic)
iptables -A OUTPUT -o lo -j ACCEPT
# 2. Allow the Root user (who runs the Proxy) to talk to the internet
iptables -A OUTPUT -m owner --uid-owner root -j ACCEPT
# 3. DROP everything else (Block dev_user from direct internet)
iptables -A OUTPUT -j DROP

echo "[INIT] Environment Secured. Switching to dev_user."
# Switch to the unprivileged user
su - dev_user

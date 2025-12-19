# Zero Trust Docker Security Implementation

This repository implements a complete Zero Trust security model for Docker-based
environments where **no user is trusted by default**. Network access, Docker
operations, and sudo privileges are all denied initially and granted only after
successful policy-based authentication.

The implementation uses Open Policy Agent (OPA) as the policy engine, a Python
controller as the enforcement point, iptables for network isolation, and PAM for
sudo access control.

---

## Prerequisites

- Linux system
- Docker installed and running
- Python 3
- Open Policy Agent (OPA)
- Root or sudo privileges

---

## Step 1: Create Users and Docker Access

Create two users and add them to the Docker group so they can interact with Docker
without sudo.

```bash
sudo adduser 1
sudo adduser rmrf
sudo usermod -aG docker 1
sudo usermod -aG docker rmrf
```
The user 1 will have full Docker access while rmrf will be restricted by
policy.

## Step 2: Install Open Policy Agent

Install OPA on the host system.
```bash
sudo apt install opa
chmod +x opa
opa version
```

OPA will act as the policy decision engine.
## Step 3: Define Docker Authorization Policy

Create an authorization policy using Rego to define which users are allowed to
perform specific Docker actions.

policy.rego
```bash
package docker.authz

default allow = false

allow {
    input.User == "1"
}

allow {
    input.User == "rmrf"
    input.RequestMethod == "GET"
}
```
This ensures rmrf can only perform read-only Docker operations.
## Step 4: Configure OPA Policy Bundle

Place the policy into a bundle and configure OPA to load it.

Create opa-config.yaml:
```bash
services:
  docker_authz:
    url: http://localhost:8181
bundles:
  authz:
    service: docker_authz
    resource: bundle.tar.gz
```
## Step 5: Enable Docker Authorization Plugin

Install and configure the Docker OPA authorization plugin.
```bash
docker plugin install --alias opa-docker-authz \
ghcr.io/open-policy-agent/opa-docker-authz:v0.10 \
opa-args="-config-file /opa/config/opa-config.yaml"
```
Update Docker daemon configuration:

/etc/docker/daemon.json
```bash
{
  "authorization-plugins": ["opa-docker-authz"]
}
```
Restart Docker:
```bash
sudo systemctl restart docker
```
## Step 6: Zero Trust Network Isolation

Block all outbound traffic by default using iptables.

iptables -A OUTPUT -j DROP
iptables -A OUTPUT -m owner --uid-owner root -j ACCEPT

Only trusted processes running as root are allowed to access the network.
## Step 7: OPA Authentication Policy

Define authentication rules and session duration.

policy.rego
```bash
package zt.auth

default allow = false

allow {
    input.user == "dev_user"
    input.password == "securePass123"
}

session_duration = 300
```
### Step 8: Python Zero Trust Controller

Run a Python controller that:

    Authenticates users via OPA

    Creates a session with expiry

    Acts as a controlled network proxy

The controller writes session data to /var/run/zt_session and checks it before
allowing traffic.
## Step 9: PAM Enforcement for Sudo

Intercept sudo requests using PAM.

Edit /etc/pam.d/sudo and add:
```bash
auth required pam_exec.so /usr/local/bin/check_pam.sh
```
The script validates session status before allowing sudo.
## Step 10: Container Build and Execution

Build the Docker image:
```bash
docker build -t zt-part2 zt-network-access/
```
Run with required capabilities:
```bash
docker run -it --cap-add=NET_ADMIN zt-part2
```
## Step 11: Authenticate and Verify Access

Authenticate:
```bash
zt-login securePass123
```
Enable proxy and test:
```bash
export http_proxy=http://127.0.0.1:8080
curl -I https://www.google.com
sudo ls /root
```
Stopping the controller or waiting for session expiry revokes all access.

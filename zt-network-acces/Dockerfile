FROM ubuntu

ENV DEBIAN_FRONTEND=noninteractive

# 1. Install tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl wget iptables sudo vim bc \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask requests --break-system-packages
# 2. Install OPA
RUN curl -L -o /usr/local/bin/opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static \
    && chmod 755 /usr/local/bin/opa

# 3. Setup User 'dev_user'
RUN useradd -m -s /bin/bash dev_user && \
    echo "dev_user:password" | chpasswd && \
    usermod -aG sudo dev_user

# 4. Copy Project Files
WORKDIR /opt/zt
COPY policy.rego zt_controller.py /opt/zt/
COPY check_pam.sh /usr/local/bin/
COPY entrypoint.sh /entrypoint.sh

# 5. Permissions & Configuration
RUN chmod +x /usr/local/bin/check_pam.sh /entrypoint.sh && \
    chmod 777 /opt/zt

# 6. Configure PAM to use our script for Sudo
RUN echo "auth required pam_exec.so quiet /usr/local/bin/check_pam.sh" >> /etc/pam.d/sudo

# 7. Configure APT to use our Proxy
RUN echo 'Acquire::http::Proxy "http://127.0.0.1:8080";' >> /etc/apt/apt.conf && \
    echo 'Acquire::https::Proxy "http://127.0.0.1:8080";' >> /etc/apt/apt.conf

# 8. Create a login alias for convenience

COPY zt_client.sh /usr/local/bin/zt-login
RUN chmod +x /usr/local/bin/zt-login

ENTRYPOINT ["/entrypoint.sh"]

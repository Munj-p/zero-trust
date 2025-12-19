import threading, time, requests, socket, select, os
from flask import Flask, request, jsonify
from http.server import BaseHTTPRequestHandler, HTTPServer

# CONFIG
OPA_URL = "http://localhost:8181/v1/data/zero_trust"
PROXY_PORT = 8080
AUTH_PORT = 5000
SESSION_FILE = "/var/run/zt_session"
SESSION_STATE = {"active": False, "expires": 0}

app = Flask(__name__)

# --- AUTH ENDPOINTS ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    # Query OPA
    try:
        opa_resp = requests.post(OPA_URL, json={"input": data}).json()
        result = opa_resp.get('result', {})
    except:
        return jsonify({"error": "OPA Down"}), 500

    if result.get('allow'):
        duration = result.get('session_duration', 60)
        SESSION_STATE['active'] = True
        SESSION_STATE['expires'] = time.time() + duration
        
        # Write token for PAM to read
        with open(SESSION_FILE, 'w') as f:
            f.write(f"{SESSION_STATE['expires']}")
            
        return jsonify({"status": "Authenticated", "valid_for_seconds": duration})
    
    return jsonify({"error": "Invalid Credentials"}), 403

# --- PROXY LOGIC ---
class ZTProxy(BaseHTTPRequestHandler):
    def is_authorized(self):
        # Check if session is valid and not expired
        if SESSION_STATE['active'] and time.time() < SESSION_STATE['expires']:
            return True
        # Cleanup if expired
        if SESSION_STATE['active']:
            SESSION_STATE['active'] = False
            with open(SESSION_FILE, 'w') as f: f.write("0")
        return False

    def do_CONNECT(self): # HTTPS Tunnel
        if not self.is_authorized():
            self.send_error(403, "Zero Trust Block: Please login via zt-login")
            return
        
        self.send_response(200, 'Connection Established')
        self.end_headers()
        
        # Simple Tunnel
        target_host, target_port = self.path.split(':')
        try:
            remote = socket.create_connection((target_host, int(target_port)))
            self.connection.setblocking(0)
            remote.setblocking(0)
            inputs = [self.connection, remote]
            while True:
                readable, _, _ = select.select(inputs, [], [], 5)
                if not readable: break
                for s in readable:
                    other = remote if s is self.connection else self.connection
                    data = s.recv(4096)
                    if not data: return
                    other.sendall(data)
        except: pass

    def do_GET(self): # HTTP Forward
        if not self.is_authorized():
            self.send_error(403, "Zero Trust Block: Please login via zt-login")
            return
        
        url = self.path
        try:
            resp = requests.get(url, headers=self.headers, stream=True, allow_redirects=False)
            self.send_response(resp.status_code)
            self.end_headers()
            self.wfile.write(resp.content)
        except: self.send_error(500)

def start_proxy():
    httpd = HTTPServer(('0.0.0.0', PROXY_PORT), ZTProxy)
    httpd.serve_forever()

if __name__ == "__main__":
    # Create session file
    with open(SESSION_FILE, 'w') as f: f.write("0")
    os.chmod(SESSION_FILE, 0o666) # Readable by everyone

    t1 = threading.Thread(target=start_proxy)
    t1.daemon = True
    t1.start()
    app.run(host='0.0.0.0', port=AUTH_PORT)

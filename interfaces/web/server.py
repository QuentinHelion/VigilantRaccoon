from __future__ import annotations

from datetime import datetime
import logging
import os
from typing import Optional
from flask import Flask, jsonify, request, Response, send_from_directory

from config import AppConfig
from infrastructure.persistence.sqlite_repositories import SQLiteAlertRepository, SQLiteServerRepository
from domain.entities import Server
from scheduler import CollectorThread


def create_app(cfg: AppConfig, collector: Optional[CollectorThread] = None) -> Flask:
    app = Flask(__name__)
    alert_repo = SQLiteAlertRepository(cfg.storage.sqlite_path)
    server_repo = SQLiteServerRepository(cfg.storage.sqlite_path)
    log = logging.getLogger("Web")

    @app.get("/logo.png")
    def serve_logo() -> Response:
        """Serve the logo image."""
        # Get the project root directory (where logo.png is located)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return send_from_directory(project_root, "logo.png")

    @app.get("/favicon.ico")
    def serve_favicon() -> Response:
        """Serve the logo as favicon."""
        # Get the project root directory (where logo.png is located)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return send_from_directory(project_root, "logo.png", mimetype="image/x-icon")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "time": datetime.utcnow().isoformat()}

    @app.get("/")
    def root() -> Response:
        return Response(
            '<html><head><title>VigilantRaccoon</title>'
            '<link rel="icon" type="image/x-icon" href="/favicon.ico">'
            '<style>'
            'body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5;}'
            '.container{max-width:800px;margin:40px auto;background:white;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);padding:40px;text-align:center;}'
            'h1{color:#495057;margin:20px 0;font-size:32px;font-weight:300;}'
            '.nav-links{list-style:none;padding:0;margin:30px 0;}'
            '.nav-links li{margin:15px 0;}'
            '.nav-links a{display:inline-block;padding:15px 25px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;text-decoration:none;border-radius:8px;font-weight:500;transition:transform 0.2s,box-shadow 0.2s;}'
            '.nav-links a:hover{transform:translateY(-2px);box-shadow:0 4px 15px rgba(102,126,234,0.3);}'
            '.description{color:#6c757d;font-size:16px;line-height:1.6;margin:20px 0;}'
            '</style>'
            '</head><body>'
            '<div class="container">'
            '<h1>VigilantRaccoon</h1>'
            '<p class="description">Advanced security monitoring system for Linux servers</p>'
            '<ul class="nav-links">'
            '<li><a href="/ui/alerts">🔒 Security Alerts</a></li>'
            '<li><a href="/ui/servers">🖥️ Server Management</a></li>'
            '<li><a href="/alerts">📊 Alerts API</a></li>'
            '<li><a href="/servers">⚙️ Servers API</a></li>'
            '</ul>'
            '</div>'
            '</body></html>', 
            mimetype="text/html"
        )

    @app.get("/alerts")
    def list_alerts() -> Response:
        limit = int(request.args.get("limit", 200))
        since_param = request.args.get("since")
        since = datetime.fromisoformat(since_param) if since_param else None
        server_filter = request.args.get("server")
        level_filter = request.args.get("level")
        acknowledged_filter = request.args.get("acknowledged")
        
        # Parse acknowledged filter
        acknowledged = None
        if acknowledged_filter == "true":
            acknowledged = True
        elif acknowledged_filter == "false":
            acknowledged = False
        
        alerts = alert_repo.list_alerts(limit=limit, since=since, acknowledged=acknowledged)
        
        # Apply filters
        if server_filter:
            alerts = [a for a in alerts if a.server_name == server_filter]
        if level_filter:
            alerts = [a for a in alerts if a.level == level_filter]
        
        data = [
            {
                "id": a.id,
                "server_name": a.server_name,
                "source_log": a.source_log,
                "timestamp": a.timestamp.isoformat(),
                "level": a.level,
                "message": a.message,
                "ip_address": a.ip_address,
                "rule": a.rule,
                "acknowledged": a.acknowledged,
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "acknowledged_by": a.acknowledged_by,
            }
            for a in alerts
        ]
        return jsonify(data)

    @app.post("/alerts/<int:alert_id>/acknowledge")
    def acknowledge_alert(alert_id: int) -> Response:
        body = request.get_json(force=True, silent=False)
        acknowledged_by = body.get("acknowledged_by", "web_user")
        
        success = alert_repo.acknowledge_alert(alert_id, acknowledged_by)
        if success:
            log.info("Alert %d acknowledged by %s", alert_id, acknowledged_by)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Alert not found"}), 404

    @app.post("/alerts/acknowledge-by-rule")
    def acknowledge_alerts_by_rule() -> Response:
        body = request.get_json(force=True, silent=False)
        rule = body.get("rule")
        acknowledged_by = body.get("acknowledged_by", "web_user")
        
        if not rule:
            return jsonify({"error": "Rule parameter required"}), 400
        
        count = alert_repo.acknowledge_alerts_by_rule(rule, acknowledged_by)
        log.info("Acknowledged %d alerts with rule %s by %s", count, rule, acknowledged_by)
        return jsonify({"status": "ok", "acknowledged_count": count})

    @app.get("/servers")
    def list_servers() -> Response:
        servers = server_repo.list_servers()
        log.debug("List servers (%d)", len(servers))
        data = [
            {
                "name": s.name,
                "host": s.host,
                "port": s.port,
                "username": s.username,
                "private_key_path": s.private_key_path,
                "logs": s.logs or [],
                "has_password": bool(s.password),
            }
            for s in servers
        ]
        return jsonify(data)

    @app.post("/servers")
    def add_server() -> Response:
        body = request.get_json(force=True, silent=False)
        required = ["name", "host", "port", "username"]
        for k in required:
            if k not in body:
                return jsonify({"error": f"Missing field: {k}"}), 400
        logs = body.get("logs")
        if logs is None:
            logs = []  # defaulted at runtime to ssh:auto
        srv = Server(
            name=str(body["name"]).strip(),
            host=str(body["host"]).strip(),
            port=int(body["port"]),
            username=str(body["username"]).strip(),
            password=str(body.get("password") or "") or None,
            private_key_path=str(body.get("private_key_path") or "") or None,
            logs=list(logs),
        )
        server_repo.upsert_server(srv)
        log.info("Upserted server %s (%s:%s)", srv.name, srv.host, srv.port)
        if collector is not None:
            collector.trigger_refresh()
        return jsonify({"status": "ok"})

    @app.delete("/servers/<name>")
    def delete_server(name: str) -> Response:
        server_repo.delete_server(name)
        log.info("Deleted server %s", name)
        if collector is not None:
            collector.trigger_refresh()
        return jsonify({"status": "ok"})

    @app.get("/ui/servers")
    def ui_servers() -> Response:
        html = (
            "<html><head><title>VigilantRaccoon - Server Management</title>"
            "<link rel='icon' type='image/x-icon' href='/favicon.ico'>"
            "<style>"
            "body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5;}"
            ".container{max-width:1000px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.1);overflow:hidden;}"
            ".header{padding:30px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;text-align:center;}"
            ".header h1{margin:0;font-size:28px;font-weight:300;}"
            ".header .subtitle{margin:10px 0 0 0;opacity:0.9;font-size:16px;}"
            ".content{padding:30px;}"
            ".form-section{margin-bottom:30px;}"
            ".form-section h3{margin:0 0 15px 0;color:#495057;font-size:18px;border-bottom:2px solid #e9ecef;padding-bottom:8px;}"
            ".form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;}"
            ".form-group{margin-bottom:20px;}"
            ".form-group label{display:block;margin-bottom:8px;font-weight:600;color:#495057;font-size:14px;}"
            ".form-group input,.form-group select,.form-group textarea{width:100%;padding:12px;border:2px solid #e9ecef;border-radius:8px;font-size:14px;transition:border-color 0.3s,box-shadow 0.3s;box-sizing:border-box;}"
            ".form-group input:focus,.form-group select:focus,.form-group textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);}"
            ".form-group .help-text{font-size:12px;color:#6c757d;margin-top:5px;}"
            ".preset-buttons{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}"
            ".preset-btn{background:#f8f9fa;border:2px solid #e9ecef;color:#495057;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px;transition:all 0.3s;}"
            ".preset-btn:hover{background:#e9ecef;border-color:#adb5bd;}"
            ".preset-btn.active{background:#667eea;border-color:#667eea;color:white;}"
            ".logs-section{background:#f8f9fa;padding:20px;border-radius:8px;border:1px solid #e9ecef;}"
            ".log-item{display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:10px;background:white;border-radius:6px;border:1px solid #e9ecef;}"
            ".log-item input{flex:1;margin:0;}"
            ".log-item button{background:#dc3545;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;}"
            ".log-item button:hover{background:#c82333;}"
            ".add-log-btn{background:#28a745;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px;margin-top:10px;}"
            ".add-log-btn:hover{background:#218838;}"
            ".submit-btn{background:#667eea;color:white;border:none;padding:15px 30px;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;width:100%;margin-top:20px;transition:background 0.3s;}"
            ".submit-btn:hover{background:#5a6fd8;}"
            ".submit-btn:disabled{background:#6c757d;cursor:not-allowed;}"
            ".existing-servers{margin-top:40px;}"
            ".server-card{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:20px;margin-bottom:15px;}"
            ".server-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;}"
            ".server-name{font-size:18px;font-weight:600;color:#495057;}"
            ".server-actions{display:flex;gap:10px;}"
            ".edit-btn,.delete-btn{padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;border:none;}"
            ".edit-btn{background:#17a2b8;color:white;}"
            ".edit-btn:hover{background:#138496;}"
            ".delete-btn{background:#dc3545;color:white;}"
            ".delete-btn:hover{background:#c82333;}"
            ".server-details{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;font-size:14px;}"
            ".detail-item{background:white;padding:10px;border-radius:4px;border:1px solid #e9ecef;}"
            ".detail-label{font-weight:600;color:#6c757d;font-size:12px;text-transform:uppercase;margin-bottom:5px;}"
            ".detail-value{color:#495057;}"
            ".logs-list{display:flex;flex-wrap:wrap;gap:5px;}"
            ".log-tag{background:#e9ecef;color:#495057;padding:2px 8px;border-radius:12px;font-size:11px;font-family:monospace;}"
            "</style>"
            "</head><body>"
            "<div class='container'>"
            "<div class='header'>"
            "<h1>🖥️ Server Management</h1>"
            "<div class='subtitle'>Add and configure monitoring servers</div>"
            "</div>"
            "<div class='content'>"
            "<form id='serverForm'>"
            "<div class='form-section'>"
            "<h3>📋 Basic Information</h3>"
            "<div class='form-grid'>"
            "<div class='form-group'>"
            "<label for='name'>Server Name *</label>"
            "<input type='text' id='name' name='name' required placeholder='e.g., web-server, db-server'>"
            "<div class='help-text'>Unique identifier for this server</div>"
            "</div>"
            "<div class='form-group'>"
            "<label for='host'>Host/IP Address *</label>"
            "<input type='text' id='host' name='host' required placeholder='192.168.1.100 or server.example.com'>"
            "<div class='help-text'>Server IP address or hostname</div>"
            "</div>"
            "<div class='form-group'>"
            "<label for='port'>SSH Port</label>"
            "<input type='number' id='port' name='port' value='22' min='1' max='65535'>"
            "<div class='help-text'>SSH port (default: 22)</div>"
            "</div>"
            "<div class='form-group'>"
            "<label for='username'>Username *</label>"
            "<input type='text' id='username' name='username' required placeholder='root, admin, or service user'>"
            "<div class='help-text'>SSH username for authentication</div>"
            "</div>"
            "</div>"
            "</div>"
            ""
            "<div class='form-section'>"
            "<h3>🔐 Authentication</h3>"
            "<div class='form-grid'>"
            "<div class='form-group'>"
            "<label for='authType'>Authentication Method</label>"
            "<select id='authType' name='authType' onchange='toggleAuthFields()'>"
            "<option value='password'>Password</option>"
            "<option value='key'>SSH Private Key</option>"
            "</select>"
            "<div class='help-text'>Choose between password or SSH key authentication</div>"
            "</div>"
            "<div class='form-group' id='passwordGroup'>"
            "<label for='password'>Password</label>"
            "<input type='password' id='password' name='password' placeholder='Enter SSH password'>"
            "<div class='help-text'>SSH password for the user</div>"
            "</div>"
            "<div class='form-group' id='keyGroup' style='display:none;'>"
            "<label for='privateKeyPath'>Private Key Path</label>"
            "<input type='text' id='privateKeyPath' name='privateKeyPath' placeholder='~/.ssh/id_rsa'>"
            "<div class='help-text'>Path to SSH private key file</div>"
            "</div>"
            "</div>"
            "</div>"
            ""
            "<div class='form-section'>"
            "<h3>📊 Log Sources</h3>"
            "<div class='preset-buttons'>"
            "<button type='button' class='preset-btn active' onclick='applyPreset(\"debian\")'>Debian/Ubuntu</button>"
            "<button type='button' class='preset-btn' onclick='applyPreset(\"rhel\")'>RHEL/CentOS</button>"
            "<button type='button' class='preset-btn' onclick='applyPreset(\"custom\")'>Custom</button>"
            "</div>"
            "<div class='logs-section'>"
            "<div id='logsContainer'>"
            "<div class='log-item'>"
            "<input type='text' name='logs[]' value='journal:ssh' placeholder='Log source (e.g., journal:ssh, /var/log/auth.log)'>"
            "<button type='button' onclick='removeLog(this)'>&times;</button>"
            "</div>"
            "<div class='log-item'>"
            "<input type='text' name='logs[]' value='/var/log/fail2ban.log' placeholder='Log source'>"
            "<button type='button' onclick='removeLog(this)'>&times;</button>"
            "</div>"
            "</div>"
            "<button type='button' class='add-log-btn' onclick='addLog()'>+ Add Log Source</button>"
            "<div class='help-text' style='margin-top:10px;'>"
            "<strong>Common log sources:</strong><br>"
            "• <code>journal:ssh</code> - Systemd SSH service logs (Debian/Ubuntu)<br>"
            "• <code>journal:sshd</code> - Systemd SSH service logs (RHEL/CentOS)<br>"
            "• <code>/var/log/auth.log</code> - Authentication logs (Debian/Ubuntu)<br>"
            "• <code>/var/log/secure</code> - Authentication logs (RHEL/CentOS)<br>"
            "• <code>/var/log/fail2ban.log</code> - Fail2Ban logs<br>"
            "• <code>ssh:auto</code> - Auto-detect best SSH log source"
            "</div>"
            "</div>"
            "</div>"
            ""
            "<button type='submit' class='submit-btn' id='submitBtn'>🚀 Add Server</button>"
            "</form>"
            ""
            "<div class='existing-servers'>"
            "<h3>📋 Existing Servers</h3>"
            "<div id='serversList'>Loading...</div>"
            "</div>"
            "</div>"
            "</div>"
            ""
            "<script>"
            "let currentPreset = 'debian';"
            "let editingServer = null;"
            ""
            "function toggleAuthFields() {"
            "  const authType = document.getElementById('authType').value;"
            "  const passwordGroup = document.getElementById('passwordGroup');"
            "  const keyGroup = document.getElementById('keyGroup');"
            "  "
            "  if (authType === 'password') {"
            "    passwordGroup.style.display = 'block';"
            "    keyGroup.style.display = 'none';"
            "    document.getElementById('password').required = true;"
            "    document.getElementById('privateKeyPath').required = false;"
            "  } else {"
            "    passwordGroup.style.display = 'none';"
            "    keyGroup.style.display = 'block';"
            "    document.getElementById('password').required = false;"
            "    document.getElementById('privateKeyPath').required = true;"
            "  }"
            "}"
            ""
            "function applyPreset(preset) {"
            "  currentPreset = preset;"
            "  document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));"
            "  event.target.classList.add('active');"
            "  "
            "  const logsContainer = document.getElementById('logsContainer');"
            "  logsContainer.innerHTML = '';"
            "  "
            "  let logs = [];"
            "  if (preset === 'debian') {"
            "    logs = ['journal:ssh', '/var/log/fail2ban.log', '/var/log/auth.log'];"
            "  } else if (preset === 'rhel') {"
            "    logs = ['journal:sshd', '/var/log/fail2ban.log', '/var/log/secure'];"
            "  } else if (preset === 'custom') {"
            "    logs = ['ssh:auto'];"
            "  }"
            "  "
            "  logs.forEach(log => addLog(log));"
            "}"
            ""
            "function addLog(value = '') {"
            "  const container = document.getElementById('logsContainer');"
            "  const logItem = document.createElement('div');"
            "  logItem.className = 'log-item';"
            "  logItem.innerHTML = `"
            "    <input type='text' name='logs[]' value='${value}' placeholder='Log source'>"
            "    <button type='button' onclick='removeLog(this)'>&times;</button>"
            "  `;"
            "  container.appendChild(logItem);"
            "}"
            ""
            "function removeLog(button) {"
            "  const container = document.getElementById('logsContainer');"
            "  if (container.children.length > 1) {"
            "    button.parentElement.remove();"
            "  }"
            "}"
            ""
            "function loadServers() {"
            "  fetch('/servers')"
            "    .then(response => response.json())"
            "    .then(servers => {"
            "      const container = document.getElementById('serversList');"
            "      if (servers.length === 0) {"
            "        container.innerHTML = '<p style=\"text-align:center;color:#6c757d;\">No servers configured yet</p>';"
            "        return;"
            "      }"
            "      "
            "      container.innerHTML = servers.map(server => `"
            "        <div class='server-card'>"
            "          <div class='server-header'>"
            "            <div class='server-name'>${server.name}</div>"
            "            <div class='server-actions'>"
            "              <button class='edit-btn' onclick='editServer(${JSON.stringify(server).replace(/\"/g, '&quot;')})'>✏️ Edit</button>"
            "              <button class='delete-btn' onclick='deleteServer(\"${server.name}\")'>🗑️ Delete</button>"
            "            </div>"
            "          </div>"
            "          <div class='server-details'>"
            "            <div class='detail-item'>"
            "              <div class='detail-label'>Host</div>"
            "              <div class='detail-value'>${server.host}:${server.port}</div>"
            "            </div>"
            "            <div class='detail-item'>"
            "              <div class='detail-label'>Username</div>"
            "              <div class='detail-value'>${server.username}</div>"
            "            </div>"
            "            <div class='detail-item'>"
            "              <div class='detail-label'>Authentication</div>"
            "              <div class='detail-value'>${server.has_password ? 'Password' : 'SSH Key'}</div>"
            "            </div>"
            "            <div class='detail-item'>"
            "              <div class='detail-label'>Log Sources</div>"
            "              <div class='detail-value'>"
            "                <div class='logs-list'>"
            "                  ${server.logs.map(log => `<span class='log-tag'>${log}</span>`).join('')}"
            "                </div>"
            "              </div>"
            "            </div>"
            "          </div>"
            "        </div>"
            "      `).join('');"
            "    })"
            "    .catch(error => {"
            "      console.error('Failed to load servers:', error);"
            "      document.getElementById('serversList').innerHTML = '<p style=\"color:#dc3545;\">Failed to load servers</p>';"
            "    });"
            "}"
            ""
            "function editServer(server) {"
            "  editingServer = server;"
            "  document.getElementById('name').value = server.name;"
            "  document.getElementById('host').value = server.host;"
            "  document.getElementById('port').value = server.port;"
            "  document.getElementById('username').value = server.username;"
            "  "
            "  if (server.has_password) {"
            "    document.getElementById('authType').value = 'password';"
            "    document.getElementById('password').value = '';"
            "  } else {"
            "    document.getElementById('authType').value = 'key';"
            "    document.getElementById('privateKeyPath').value = server.private_key_path || '';"
            "  }"
            "  toggleAuthFields();"
            "  "
            "  // Clear and populate logs"
            "  const logsContainer = document.getElementById('logsContainer');"
            "  logsContainer.innerHTML = '';"
            "  server.logs.forEach(log => addLog(log));"
            "  "
            "  document.getElementById('submitBtn').textContent = '💾 Update Server';"
            "  document.getElementById('submitBtn').style.background = '#28a745';"
            "}"
            ""
            "function deleteServer(name) {"
            "  if (!confirm(`Are you sure you want to delete server '${name}'?`)) return;"
            "  "
            "  fetch(`/servers/${name}`, {{ method: 'DELETE' }})"
            "    .then(response => {"
            "      if (response.ok) {"
            "        loadServers();"
            "        alert('Server deleted successfully');"
            "      } else {"
            "        alert('Failed to delete server');"
            "      }"
            "    })"
            "    .catch(error => {"
            "      console.error('Failed to delete server:', error);"
            "      alert('Failed to delete server');"
            "    });"
            "}"
            ""
            "function resetForm() {"
            "  editingServer = null;"
            "  document.getElementById('serverForm').reset();"
            "  document.getElementById('submitBtn').textContent = '🚀 Add Server';"
            "  document.getElementById('submitBtn').style.background = '#667eea';"
            "  applyPreset('debian');"
            "  toggleAuthFields();"
            "}"
            ""
            "document.getElementById('serverForm').addEventListener('submit', async (e) => {"
            "  e.preventDefault();"
            "  "
            "  const formData = new FormData(e.target);"
            "  const logs = Array.from(formData.getAll('logs[]')).filter(log => log.trim());"
            "  "
            "  if (logs.length === 0) {"
            "    alert('Please add at least one log source');"
            "    return;"
            "  }"
            "  "
            "  const authType = document.getElementById('authType').value;"
            "  const body = {"
            "    name: formData.get('name'),"
            "    host: formData.get('host'),"
            "    port: Number(formData.get('port')),"
            "    username: formData.get('username'),"
            "    password: authType === 'password' ? formData.get('password') : null,"
            "    private_key_path: authType === 'key' ? formData.get('privateKeyPath') : null,"
            "    logs: logs"
            "  };"
            "  "
            "  try {"
            "    const response = await fetch('/servers', {{"
            "      method: 'POST',"
            "      headers: {{ 'Content-Type': 'application/json' }},"
            "      body: JSON.stringify(body)"
            "    }});"
            "    "
            "    if (response.ok) {"
            "      alert(editingServer ? 'Server updated successfully!' : 'Server added successfully!');"
            "      resetForm();"
            "      loadServers();"
            "    } else {"
            "      const error = await response.text();"
            "      alert('Error: ' + error);"
            "    }"
            "  } catch (error) {"
            "    console.error('Failed to save server:', error);"
            "    alert('Failed to save server');"
            "  }"
            "});"
            ""
            "// Initialize form"
            "toggleAuthFields();"
            "loadServers();"
            "</script>"
            "</body></html>"
        )
        return Response(html, mimetype="text/html")

    @app.get("/ui/alerts")
    def ui_alerts() -> Response:
        html = (
            "<html><head><title>VigilantRaccoon - Alerts</title>"
            "<link rel='icon' type='image/x-icon' href='/favicon.ico'>"
            "<style>"
            "body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5;}"
            ".container{max-width:1400px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);overflow:hidden;}"
            ".header{padding:20px;border-bottom:1px solid #eee;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;}"
            ".header h1{margin:0;font-size:24px;}"
            ".filters{padding:20px;background:#fafafa;border-bottom:1px solid #eee;display:flex;gap:15px;align-items:center;flex-wrap:wrap;}"
            ".filter-group{display:flex;flex-direction:column;gap:5px;}"
            ".filter-group label{font-size:12px;font-weight:600;color:#666;}"
            ".filter-group select,.filter-group input{padding:8px 12px;border:1px solid #ddd;border-radius:4px;font-size:14px;min-width:120px;}"
            ".filter-group select:focus,.filter-group input:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);}"
            ".stats{padding:15px 20px;background:#f8f9fa;border-bottom:1px solid #eee;font-size:14px;color:#666;}"
            ".table-container{overflow-x:auto;}"
            "table{width:100%;border-collapse:collapse;font-size:14px;}"
            "th{background:#f8f9fa;padding:12px 8px;text-align:left;font-weight:600;color:#495057;border-bottom:2px solid #dee2e6;position:sticky;top:0;z-index:10;}"
            "td{padding:10px 8px;border-bottom:1px solid #eee;vertical-align:top;}"
            "tr:hover{background:#f8f9fa;}"
            ".level-high{color:#dc3545;font-weight:600;}"
            ".level-medium{color:#fd7e14;font-weight:600;}"
            ".level-info{color:#17a2b8;font-weight:600;}"
            ".message{max-width:300px;word-break:break-word;}"
            ".timestamp{white-space:nowrap;font-family:monospace;font-size:12px;color:#666;}"
            ".server{font-weight:600;color:#495057;}"
            ".ip{font-family:monospace;background:#f8f9fa;padding:2px 6px;border-radius:3px;font-size:12px;}"
            ".rule{font-size:12px;color:#6c757d;background:#e9ecef;padding:2px 6px;border-radius:3px;}"
            ".refresh-btn{background:#667eea;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-size:14px;}"
            ".refresh-btn:hover{background:#5a6fd8;}"
            ".refresh-btn:active{transform:translateY(1px);}"
            ".ack-btn{background:#28a745;color:white;border:none;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:12px;margin:2px;}"
            ".ack-btn:hover{background:#218838;}"
            ".ack-btn:disabled{background:#6c757d;cursor:not-allowed;}"
            ".acknowledged{opacity:0.6;background:#f8f9fa;}"
            ".acknowledged .ack-btn{display:none;}"
            ".ack-status{font-size:11px;color:#6c757d;font-style:italic;}"
            ".bulk-ack{background:#17a2b8;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:12px;margin-left:10px;}"
            ".bulk-ack:hover{background:#138496;}"
            "</style>"
            "</head><body>"
            "<div class='container'>"
            "<div class='header'>"
            "<h1>🔒 VigilantRaccoon - Security Alerts</h1>"
            "</div>"
            "<div class='filters'>"
            "<div class='filter-group'><label>Server</label><select id='serverFilter'><option value=''>All servers</option></select></div>"
            "<div class='filter-group'><label>Level</label><select id='levelFilter'><option value=''>All levels</option><option value='high'>High</option><option value='medium'>Medium</option><option value='info'>Info</option></select></div>"
            "<div class='filter-group'><label>Status</label><select id='ackFilter'><option value=''>All</option><option value='false'>Unacknowledged</option><option value='true'>Acknowledged</option></select></div>"
            "<div class='filter-group'><label>Limit</label><select id='limitFilter'><option value='100'>100</option><option value='200' selected>200</option><option value='500'>500</option><option value='1000'>1000</option></select></div>"
            "<button class='refresh-btn' onclick='loadAlerts()'>🔄 Refresh</button>"
            "</div>"
            "<div class='stats' id='stats'>Loading...</div>"
            "<div class='table-container'>"
            "<table><thead><tr>"
            "<th>ID</th><th>Timestamp</th><th>Level</th><th>Server</th><th>Log Source</th><th>IP Address</th><th>Rule</th><th>Message</th><th>Actions</th>"
            "</tr></thead><tbody id='alertsTable'>"
            "</tbody></table></div>"
            "</div>"
            "<script>"
            "let currentAlerts = [];"
            "let servers = [];"
            ""
            "async function loadServers() {"
            "  try {"
            "    const response = await fetch('/servers');"
            "    servers = await response.json();"
            "    const serverFilter = document.getElementById('serverFilter');"
            "    serverFilter.innerHTML = '<option value=\"\">All servers</option>';"
            "    servers.forEach(s => {"
            "      const option = document.createElement('option');"
            "        option.value = s.name;"
            "        option.textContent = s.name;"
            "        serverFilter.appendChild(option);"
            "    });"
            "  } catch (e) {"
            "    console.error('Failed to load servers:', e);"
            "  }"
            "}"
            ""
            "async function loadAlerts() {"
            "  try {"
            "    const serverFilter = document.getElementById('serverFilter').value;"
            "    const levelFilter = document.getElementById('levelFilter').value;"
            "    const ackFilter = document.getElementById('ackFilter').value;"
            "    const limitFilter = document.getElementById('limitFilter').value;"
            "    "
            "    let url = `/alerts?limit=${limitFilter}`;"
            "    if (serverFilter) url += `&server=${encodeURIComponent(serverFilter)}`;"
            "    if (levelFilter) url += `&level=${encodeURIComponent(levelFilter)}`;"
            "    if (ackFilter) url += `&acknowledged=${ackFilter}`;"
            "    "
            "    const response = await fetch(url);"
            "    currentAlerts = await response.json();"
            "    renderAlerts();"
            "    updateStats();"
            "  } catch (e) {"
            "    console.error('Failed to load alerts:', e);"
            "    document.getElementById('alertsTable').innerHTML = '<tr><td colspan=\"9\" style=\"text-align:center;color:#666;\">Failed to load alerts</td></tr>';"
            "  }"
            "}"
            ""
            "async function acknowledgeAlert(alertId) {"
            "  try {"
            "    const response = await fetch(`/alerts/${alertId}/acknowledge`, {"
            "      method: 'POST',"
            "      headers: { 'Content-Type': 'application/json' },"
            "      body: JSON.stringify({ acknowledged_by: 'web_user' })"
            "    });"
            "    if (response.ok) {"
            "      loadAlerts();"
            "    } else {"
            "      alert('Failed to acknowledge alert');"
            "    }"
            "  } catch (e) {"
            "    console.error('Failed to acknowledge alert:', e);"
            "    alert('Failed to acknowledge alert');"
            "  }"
            "}"
            ""
            "async function acknowledgeByRule(rule) {"
            "  if (!confirm(`Acknowledge all unacknowledged alerts with rule '${rule}'?`)) return;"
            "  try {"
            "    const response = await fetch('/alerts/acknowledge-by-rule', {"
            "      method: 'POST',"
            "      headers: { 'Content-Type': 'application/json' },"
            "      body: JSON.stringify({ rule: rule, acknowledged_by: 'web_user' })"
            "    });"
            "    if (response.ok) {"
            "      const result = await response.json();"
            "      alert(`Acknowledged ${result.acknowledged_count} alerts`);"
            "      loadAlerts();"
            "    } else {"
            "      alert('Failed to acknowledge alerts');"
            "    }"
            "  } catch (e) {"
            "    console.error('Failed to acknowledge alerts:', e);"
            "    alert('Failed to acknowledge alerts');"
            "  }"
            "}"
            ""
            "function renderAlerts() {"
            "  const tbody = document.getElementById('alertsTable');"
            "  if (currentAlerts.length === 0) {"
            "    tbody.innerHTML = '<tr><td colspan=\"9\" style=\"text-align:center;color:#666;\">No alerts found</td></tr>';"
            "    return;"
            "  }"
            "  "
            "  tbody.innerHTML = currentAlerts.map(alert => {"
            "    const levelClass = `level-${alert.level}`;"
            "    const timestamp = new Date(alert.timestamp).toLocaleString();"
            "    const rowClass = alert.acknowledged ? 'acknowledged' : '';"
            "    const ackStatus = alert.acknowledged ? `Acknowledged by ${alert.acknowledged_by} at ${new Date(alert.acknowledged_at).toLocaleString()}` : '';"
            "    "
            "    return `"
            "      <tr class='${rowClass}'>"
            "        <td>${alert.id || ''}</td>"
            "        <td class='timestamp'>${timestamp}</td>"
            "        <td><span class='${levelClass}'>${alert.level.toUpperCase()}</span></td>"
            "        <td class='server'>${alert.server_name}</td>"
            "        <td>${alert.source_log}</td>"
            "        <td>${alert.ip_address ? `<span class='ip'>${alert.ip_address}</span>` : ''}</td>"
            "        <td><span class='rule'>${alert.rule || ''}</span></td>"
            "        <td class='message'>${escapeHtml(alert.message)}</td>"
            "        <td>"
            "          ${alert.acknowledged ? '' : `<button class='ack-btn' onclick='acknowledgeAlert(${alert.id})'>✓ Ack</button>`}"
            "          ${alert.rule ? `<button class='bulk-ack' onclick='acknowledgeByRule(\"${alert.rule}\")'>Ack All ${alert.rule}</button>` : ''}"
            "          ${ackStatus ? `<div class='ack-status'>${ackStatus}</div>` : ''}"
            "        </td>"
            "      </tr>"
            "    `;"
            "  }).join('');"
            "}"
            ""
            "function updateStats() {"
            "  const stats = document.getElementById('stats');"
            "  const total = currentAlerts.length;"
            "  const acknowledged = currentAlerts.filter(a => a.acknowledged).length;"
            "  const unacknowledged = total - acknowledged;"
            "  const byLevel = currentAlerts.reduce((acc, a) => {"
            "    acc[a.level] = (acc[a.level] || 0) + 1;"
            "    return acc;"
            "  }, {});"
            "  const byServer = currentAlerts.reduce((acc, a) => {"
            "    acc[a.server_name] = (acc[a.server_name] || 0) + 1;"
            "    return acc;"
            "  }, {});"
            "  "
            "  stats.innerHTML = `"
            "    <strong>${total}</strong> total alerts | "
            "    <span style='color:#28a745'>${acknowledged} acknowledged</span> | "
            "    <span style='color:#dc3545'>${unacknowledged} unacknowledged</span> | "
            "    High: <span class='level-high'>${byLevel.high || 0}</span> | "
            "    Medium: <span class='level-medium'>${byLevel.medium || 0}</span> | "
            "    Info: <span class='level-info'>${byLevel.info || 0}</span> | "
            "    Servers: ${Object.keys(byServer).length}"
            "  `;"
            "}"
            ""
            "function escapeHtml(text) {"
            "  const div = document.createElement('div');"
            "  div.textContent = text;"
            "  return div.innerHTML;"
            "}"
            ""
            "document.getElementById('serverFilter').addEventListener('change', loadAlerts);"
            "document.getElementById('levelFilter').addEventListener('change', loadAlerts);"
            "document.getElementById('ackFilter').addEventListener('change', loadAlerts);"
            "document.getElementById('limitFilter').addEventListener('change', loadAlerts);"
            ""
            "loadServers();"
            "loadAlerts();"
            "setInterval(loadAlerts, 30000);"
            "</script>"
            "</body></html>"
        )
        return Response(html, mimetype="text/html")

    return app


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )

from __future__ import annotations

from datetime import datetime
import logging
from typing import Optional
from flask import Flask, jsonify, request, Response

from config import AppConfig
from infrastructure.persistence.sqlite_repositories import SQLiteAlertRepository, SQLiteServerRepository
from domain.entities import Server
from scheduler import CollectorThread


def create_app(cfg: AppConfig, collector: Optional[CollectorThread] = None) -> Flask:
    app = Flask(__name__)
    alert_repo = SQLiteAlertRepository(cfg.storage.sqlite_path)
    server_repo = SQLiteServerRepository(cfg.storage.sqlite_path)
    log = logging.getLogger("Web")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "time": datetime.utcnow().isoformat()}

    @app.get("/")
    def root() -> Response:
        return Response('<html><head><title>VigilantRaccoon</title></head><body><h1>VigilantRaccoon</h1><ul><li><a href="/alerts">/alerts</a></li><li><a href="/ui/alerts">/ui/alerts</a></li><li><a href="/servers">/servers</a></li><li><a href="/ui/servers">/ui/servers</a></li></ul></body></html>', mimetype="text/html")

    @app.get("/alerts")
    def list_alerts() -> Response:
        limit = int(request.args.get("limit", 200))
        since_param = request.args.get("since")
        since = datetime.fromisoformat(since_param) if since_param else None
        alerts = alert_repo.list_alerts(limit=limit, since=since)
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
            }
            for a in alerts
        ]
        return jsonify(data)

    @app.get("/ui/alerts")
    def ui_alerts() -> Response:
        alerts = alert_repo.list_alerts(limit=300)
        rows = []
        for a in alerts:
            rows.append(
                f"<tr><td>{a.id or ''}</td><td>{a.timestamp.isoformat()}</td><td>{a.level}</td><td>{a.server_name}</td><td>{a.source_log}</td><td>{a.ip_address or ''}</td><td>{a.rule or ''}</td><td><pre style='white-space:pre-wrap;margin:0'>{_html_escape(a.message)}</pre></td></tr>"
            )
        html = (
            "<html><head><title>VigilantRaccoon - Alerts</title>"
            "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:6px;font-size:13px;}th{background:#f5f5f5;position:sticky;top:0;}tr:nth-child(even){background:#fafafa;}code,pre{font-family:ui-monospace,Consolas,monospace;}</style>"
            "</head><body><h2>Alerts</h2><table><thead><tr>"
            "<th>ID</th><th>Timestamp</th><th>Level</th><th>Server</th><th>Log</th><th>IP</th><th>Rule</th><th>Message</th>"
            "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></body></html>"
        )
        return Response(html, mimetype="text/html")

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

    @app.get("/ui/servers")
    def ui_servers() -> Response:
        html = (
            "<html><head><title>VigilantRaccoon - Servers</title>"
            "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:900px;margin:20px auto;padding:0 12px;}label{display:block;margin-top:8px;}input,textarea{width:100%;padding:6px;}pre{white-space:pre-wrap;}button{margin-top:12px;padding:8px 12px;}</style>"
            "</head><body><h2>Add server</h2>"
            "<form id='f'><label>Name<input name='name' required></label>"
            "<label>Host<input name='host' required></label>"
            "<label>Port<input type='number' name='port' value='22' required></label>"
            "<label>Username<input name='username' required></label>"
            "<label>Password (optional)<input name='password' type='password'></label>"
            "<label>Private key path (optional)<input name='private_key_path'></label>"
            "<label>Logs (JSON array, leave empty for auto) <textarea name='logs'>[\"journal:ssh\", \"/var/log/fail2ban.log\"]</textarea></label>"
            "<button type='submit'>Save</button></form>"
            "<script>document.getElementById('f').addEventListener('submit', async (e)=>{e.preventDefault(); const fd=new FormData(e.target); const logsTxt=(fd.get('logs')||'').trim(); const logs=logsTxt?JSON.parse(logsTxt):[]; const body={name:fd.get('name'),host:fd.get('host'),port:Number(fd.get('port')),username:fd.get('username'),password:fd.get('password')||null,private_key_path:fd.get('private_key_path')||null,logs:logs}; const r=await fetch('/servers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); if(r.ok){alert('Saved'); e.target.reset();} else {alert('Error: '+(await r.text()));}});</script>"
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

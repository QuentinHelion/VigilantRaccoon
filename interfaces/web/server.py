from __future__ import annotations

from datetime import datetime
import logging
import os
from typing import Optional
from flask import Flask, jsonify, request, Response, send_from_directory, redirect, render_template

from config import AppConfig
from infrastructure.persistence.sqlite_repositories import SQLiteAlertRepository, SQLiteServerRepository, SQLiteAlertExceptionRepository
from domain.entities import Server
from scheduler import CollectorThread


def create_app(cfg: AppConfig, collector: Optional[CollectorThread] = None) -> Flask:
    # Get the project root directory (where templates/ is located)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = Flask(__name__, template_folder=os.path.join(project_root, "templates"))
    alert_repo = SQLiteAlertRepository(cfg.storage.sqlite_path)
    server_repo = SQLiteServerRepository(cfg.storage.sqlite_path)
    exception_repo = SQLiteAlertExceptionRepository(cfg.storage.sqlite_path)
    log = logging.getLogger("Web")

    @app.get("/logo.png")
    def serve_logo() -> Response:
        """Serve the logo image."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return send_from_directory(project_root, "logo.png")

    @app.get("/favicon.ico")
    def serve_favicon() -> Response:
        """Serve the logo as favicon."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return send_from_directory(project_root, "logo.png", mimetype="image/x-icon")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "time": datetime.utcnow().isoformat()}

    @app.get("/api/status")
    def get_status() -> Response:
        """Get current application status including collection status."""
        try:
            # Get collection status from collector thread
            collection_running = collector is not None and collector.is_alive()
            
            # Get detailed status from collector
            last_check = None
            next_check = None
            if collector and hasattr(collector, 'get_status'):
                status = collector.get_status()
                last_check = status.get('last_check_time')
                next_check = status.get('next_check_time')
            
            # Get active servers count
            active_servers = len(server_repo.list_servers())
            
            return jsonify({
                "collection_running": collection_running,
                "last_check": last_check,
                "next_check": next_check,
                "active_servers": active_servers,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            log.error("Failed to get status: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.get("/api/config")
    def get_config() -> Response:
        """Get current application configuration."""
        try:
            return jsonify({
                "poll_interval_seconds": cfg.poll_interval_seconds,
                "collection": {
                    "tail_lines": cfg.collection.tail_lines,
                    "ignore_source_ips": cfg.collection.ignore_source_ips
                },
                "email": {
                    "enabled": cfg.email.enabled,
                    "smtp_host": cfg.email.smtp_host,
                    "smtp_port": cfg.email.smtp_port,
                    "use_tls": cfg.email.use_tls,
                    "username": cfg.email.username,
                    "from_addr": cfg.email.from_addr,
                    "to_addrs": cfg.email.to_addrs
                },
                "storage": {
                    "sqlite_path": cfg.storage.sqlite_path
                },
                "logging": {
                    "file_path": cfg.logging.file_path
                }
            })
        except Exception as e:
            log.error("Failed to get config: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.put("/api/config")
    def update_config() -> Response:
        """Update application configuration."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Update poll interval if provided
            if "poll_interval_seconds" in data:
                cfg.poll_interval_seconds = int(data["poll_interval_seconds"])
                if collector and hasattr(collector, 'update_config'):
                    collector.update_config(cfg)  # Use the proper update method
            
            # Update collection settings if provided
            if "collection" in data:
                collection_data = data["collection"]
                if "tail_lines" in collection_data:
                    cfg.collection.tail_lines = int(collection_data["tail_lines"])
                if "ignore_source_ips" in collection_data:
                    cfg.collection.ignore_source_ips = collection_data["ignore_source_ips"]
            
            # Update email settings if provided
            if "email" in data:
                email_data = data["email"]
                if "enabled" in email_data:
                    cfg.email.enabled = bool(email_data["enabled"])
                if "smtp_host" in email_data:
                    cfg.email.smtp_host = str(email_data["smtp_host"])
                if "smtp_port" in email_data:
                    cfg.email.smtp_port = int(email_data["smtp_port"])
                if "use_tls" in email_data:
                    cfg.email.use_tls = bool(email_data["use_tls"])
                if "username" in email_data:
                    cfg.email.username = str(email_data["username"])
                if "password" in email_data and email_data["password"]:
                    cfg.email.password = str(email_data["password"])
                if "from_addr" in email_data:
                    cfg.email.from_addr = str(email_data["from_addr"])
                if "to_addrs" in email_data:
                    cfg.email.to_addrs = email_data["to_addrs"]
                
                # Update notifier with new email config
                if collector and hasattr(collector, '_notifier'):
                    from infrastructure.notifiers.email_notifier import EmailNotifier
                    collector._notifier = EmailNotifier(cfg.email)
            
            log.info("Configuration updated successfully")
            return jsonify({"message": "Configuration updated successfully"})
            
        except Exception as e:
            log.error("Failed to update config: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.post("/api/collection/trigger")
    def trigger_collection() -> Response:
        """Manually trigger a collection cycle."""
        try:
            if collector and hasattr(collector, 'trigger_refresh'):
                collector.trigger_refresh()
                log.info("Manual collection cycle triggered")
                return jsonify({"message": "Collection cycle triggered successfully"})
            else:
                return jsonify({"error": "Collector not available"}), 500
        except Exception as e:
            log.error("Failed to trigger collection: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.get("/api/collection/debug")
    def get_collection_debug() -> Response:
        """Get debug information about collection state."""
        try:
            if not collector:
                return jsonify({"error": "Collector not available"}), 500
            
            debug_info = {
                "collector_alive": collector.is_alive(),
                "collector_status": collector.get_status() if hasattr(collector, 'get_status') else None,
                "servers": []
            }
            
            # Get debug info for each server
            servers = server_repo.list_servers()
            for server in servers:
                server_debug = {
                    "name": server.name,
                    "host": server.host,
                    "logs": server.logs or ["ssh:auto"],
                    "collection_state": {}
                }
                
                # Get collection state for each log source
                for log_source in (server.logs or ["ssh:auto"]):
                    if log_source == "ssh:auto":
                        actual_source = "ssh:auto"
                    elif log_source.startswith("journal:"):
                        actual_source = f"journal:{log_source.split(':', 1)[1]}"
                    else:
                        actual_source = log_source
                    
                    # Try to get state from collector's state repo
                    last_ts = None
                    if hasattr(collector, '_state_repo'):
                        try:
                            last_ts = collector._state_repo.get_last_seen_timestamp(server.name, actual_source)
                        except Exception as e:
                            log.debug("Could not get state from collector: %s", e)
                    
                    server_debug["collection_state"][actual_source] = {
                        "last_seen_timestamp": last_ts,
                        "last_seen_parsed": None
                    }
                    
                    if last_ts:
                        try:
                            from datetime import datetime
                            parsed_ts = datetime.fromisoformat(last_ts)
                            server_debug["collection_state"][actual_source]["last_seen_parsed"] = parsed_ts.isoformat()
                        except Exception as e:
                            server_debug["collection_state"][actual_source]["parse_error"] = str(e)
                
                debug_info["servers"].append(server_debug)
            
            return jsonify(debug_info)
            
        except Exception as e:
            log.error("Failed to get collection debug info: %s", e)
            return jsonify({"error": str(e)}), 500

    # Frontend routes
    @app.get("/")
    def root() -> Response:
        """Redirect root to dashboard."""
        return redirect("/dashboard")

    @app.get("/dashboard")
    def dashboard() -> Response:
        """Dashboard page with statistics and quick actions."""
        return render_template("dashboard.html", active_page="dashboard")

    @app.get("/alerts")
    def alerts_page() -> Response:
        """Alerts page with filtering and management."""
        return render_template("alerts.html", active_page="alerts")

    @app.get("/servers")
    def servers_page() -> Response:
        """Server management page."""
        return render_template("servers.html", active_page="servers")

    @app.get("/exceptions")
    def exceptions_page() -> Response:
        """Alert exceptions management page."""
        return render_template("exceptions.html", active_page="exceptions")

    @app.get("/settings")
    def settings_page() -> Response:
        """Settings page for application configuration."""
        return render_template("settings.html", active_page="settings")

    # API routes
    @app.get("/api/alerts")
    def list_alerts() -> Response:
        limit = int(request.args.get("limit", 200))
        server_filter = request.args.get("server")
        level_filter = request.args.get("level")
        acknowledged_filter = request.args.get("acknowledged")
        
        # Parse acknowledged filter
        acknowledged = None
        if acknowledged_filter == "true":
            acknowledged = True
        elif acknowledged_filter == "false":
            acknowledged = False
        
        alerts = alert_repo.list_alerts(limit=limit, acknowledged=acknowledged)
        
        # Apply filters
        if server_filter:
            alerts = [a for a in alerts if a.server_name == server_filter]
        if level_filter:
            alerts = [a for a in alerts if a.level == level_filter]
        
        data = [
            {
                "id": a.id,
                "server_name": a.server_name,
                "source_log": a.log_source,
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

    @app.post("/api/alerts/<int:alert_id>/acknowledge")
    def acknowledge_alert(alert_id: int) -> Response:
        body = request.get_json(force=True, silent=False)
        acknowledged_by = body.get("acknowledged_by", "web_user")
        
        success = alert_repo.acknowledge_alert(alert_id, acknowledged_by)
        if success:
            log.info("Alert %d acknowledged by %s", alert_id, acknowledged_by)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Alert not found"}), 404

    @app.post("/api/alerts/acknowledge-by-rule")
    def acknowledge_alerts_by_rule() -> Response:
        body = request.get_json(force=True, silent=False)
        rule = body.get("rule")
        acknowledged_by = body.get("acknowledged_by", "web_user")
        
        if not rule:
            return jsonify({"error": "Rule parameter required"}), 400
        
        count = alert_repo.acknowledge_alerts_by_rule(rule, acknowledged_by)
        log.info("Acknowledged %d alerts with rule %s by %s", count, rule, acknowledged_by)
        return jsonify({"status": "ok", "acknowledged_count": count})

    @app.get("/api/servers")
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

    @app.post("/api/servers")
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
        server_repo.save_server(srv)
        log.info("Upserted server %s (%s:%s)", srv.name, srv.host, srv.port)
        if collector is not None:
            collector.trigger_refresh()
        return jsonify({"status": "ok"})

    @app.delete("/api/servers/<name>")
    def delete_server(name: str) -> Response:
        server_repo.delete_server(name)
        log.info("Deleted server %s", name)
        if collector is not None:
            collector.trigger_refresh()
        return jsonify({"status": "ok"})

    @app.get("/api/exceptions")
    def list_exceptions() -> Response:
        """API endpoint to list all alert exceptions."""
        exceptions = exception_repo.list_exceptions()
        data = [
            {
                "id": e.id,
                "rule_type": e.rule_type,
                "value": e.value,
                "description": e.description,
                "enabled": e.enabled,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat() if e.updated_at else None
            }
            for e in exceptions
        ]
        return jsonify(data)

    @app.post("/api/exceptions")
    def create_exception() -> Response:
        """API endpoint to create a new alert exception."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        from domain.entities import AlertException
        exception = AlertException(
            rule_type=data.get("rule_type", ""),
            value=data.get("value", ""),
            description=data.get("description", ""),
            enabled=data.get("enabled", True)
        )
        
        if exception_repo.save_exception(exception):
            return jsonify({"message": "Exception created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create exception"}), 500

    @app.put("/api/exceptions/<int:exception_id>")
    def update_exception(exception_id: int) -> Response:
        """API endpoint to update an existing alert exception."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        existing = exception_repo.get_exception(exception_id)
        if not existing:
            return jsonify({"error": "Exception not found"}), 404
        
        existing.rule_type = data.get("rule_type", existing.rule_type)
        existing.value = data.get("value", existing.value)
        existing.description = data.get("description", existing.description)
        existing.enabled = data.get("enabled", existing.enabled)
        
        if exception_repo.update_exception(existing):
            return jsonify({"message": "Exception updated successfully"})
        else:
            return jsonify({"error": "Failed to update exception"}), 500

    @app.delete("/api/exceptions/<int:exception_id>")
    def delete_exception(exception_id: int) -> Response:
        """API endpoint to delete an alert exception."""
        if exception_repo.delete_exception(exception_id):
            return jsonify({"message": "Exception deleted successfully"})
        else:
            return jsonify({"error": "Exception not found or could not be deleted"}), 404

    @app.post("/admin/recreate-db")
    def recreate_database() -> Response:
        """Admin endpoint to recreate the database from scratch."""
        import os
        
        try:
            db_path = cfg.storage.sqlite_path
            
            # Delete existing database file if it exists
            if os.path.exists(db_path):
                os.remove(db_path)
                log.info("Deleted existing database: %s", db_path)
            
            # Reinitialize repositories to create fresh tables
            alert_repo = SQLiteAlertRepository(db_path)
            server_repo = SQLiteServerRepository(db_path)
            exception_repo = SQLiteAlertExceptionRepository(db_path)
            
            log.info("Database recreated successfully with fresh tables")
            return jsonify({"message": "Database recreated successfully"})
            
        except Exception as e:
            log.error("Failed to recreate database: %s", e)
            return jsonify({"error": f"Failed to recreate database: {str(e)}"}), 500

    # Legacy routes for backward compatibility
    @app.get("/ui/alerts")
    def ui_alerts_legacy() -> Response:
        """Legacy route redirecting to new alerts page."""
        return redirect("/alerts")

    @app.get("/ui/servers")
    def ui_servers_legacy() -> Response:
        """Legacy route redirecting to new servers page."""
        return redirect("/servers")

    @app.get("/ui/exceptions")
    def ui_exceptions_legacy() -> Response:
        """Legacy route redirecting to new exceptions page."""
        return redirect("/exceptions")

    return app

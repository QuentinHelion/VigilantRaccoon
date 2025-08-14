from __future__ import annotations

import argparse
import logging

from config import load_config
from interfaces.web.server import create_app
from scheduler import CollectorThread
from infrastructure.logging.setup import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="VigilantRaccoon - security log collector")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file")
    parser.add_argument("--recreate-db", action="store_true", help="Recreate database from scratch (WARNING: This will delete all existing data)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg.logging)

    logging.getLogger(__name__).info("Starting VigilantRaccoon")
    
    if args.recreate_db:
        logging.getLogger(__name__).warning("RECREATING DATABASE - All existing data will be lost!")
        _recreate_database(cfg)

    collector = CollectorThread(cfg)
    collector.start()

    app = create_app(cfg, collector=collector)
    logging.getLogger(__name__).info("Web server listening on %s:%s", cfg.web.host, cfg.web.port)
    app.run(host=cfg.web.host, port=cfg.web.port, debug=False, use_reloader=False)


def _recreate_database(cfg) -> None:
    """Recreate the database by deleting the file and reinitializing repositories."""
    import os
    from infrastructure.persistence.sqlite_repositories import SQLiteAlertRepository, SQLiteServerRepository, SQLiteAlertExceptionRepository
    
    db_path = cfg.storage.sqlite_path
    
    # Delete existing database file if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logging.getLogger(__name__).info("Deleted existing database: %s", db_path)
        except OSError as e:
            logging.getLogger(__name__).error("Failed to delete database: %s", e)
            return
    
    # Reinitialize repositories to create fresh tables
    try:
        alert_repo = SQLiteAlertRepository(db_path)
        server_repo = SQLiteServerRepository(db_path)
        exception_repo = SQLiteAlertExceptionRepository(db_path)
        logging.getLogger(__name__).info("Database recreated successfully with fresh tables")
    except Exception as e:
        logging.getLogger(__name__).error("Failed to recreate database: %s", e)


if __name__ == "__main__":
    main()

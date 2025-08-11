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
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg.logging)

    logging.getLogger(__name__).info("Starting VigilantRaccoon")

    collector = CollectorThread(cfg)
    collector.start()

    app = create_app(cfg, collector=collector)
    logging.getLogger(__name__).info("Web server listening on %s:%s", cfg.web.host, cfg.web.port)
    app.run(host=cfg.web.host, port=cfg.web.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

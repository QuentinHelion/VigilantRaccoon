from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yaml


@dataclass
class ServerConfig:
    name: str
    host: str
    username: str
    port: int = 22
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    logs: List[str] = field(default_factory=list)


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    use_tls: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    from_addr: Optional[str] = None
    to_addrs: List[str] = field(default_factory=list)


@dataclass
class StorageConfig:
    sqlite_path: str = "./data/vigilant_raccoon.db"


@dataclass
class CollectionConfig:
    tail_lines: int = 2000
    ignore_source_ips: List[str] = field(default_factory=list)


@dataclass
class WebConfig:
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass
class LoggingConfig:
    level: str = "INFO"           # DEBUG, INFO, WARNING, ERROR
    file_path: str = "./logs/app.log"
    max_bytes: int = 1_000_000     # 1 MB
    backup_count: int = 3
    console: bool = True


@dataclass
class AppConfig:
    servers: List[ServerConfig]
    poll_interval_seconds: int = 60
    email: EmailConfig = field(default_factory=EmailConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    collection: CollectionConfig = field(default_factory=CollectionConfig)
    web: WebConfig = field(default_factory=WebConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Filtrage des champs valides pour ServerConfig
    def filter_server_config(srv_data):
        valid_fields = {'name', 'host', 'port', 'username', 'password', 'private_key_path', 'logs'}
        return {k: v for k, v in srv_data.items() if k in valid_fields}
    
    servers = [ServerConfig(**filter_server_config(srv)) for srv in raw.get("servers", [])]
    email = EmailConfig(**(raw.get("email") or {}))
    storage = StorageConfig(**(raw.get("storage") or {}))
    collection = CollectionConfig(**(raw.get("collection") or {}))
    web = WebConfig(**(raw.get("web") or {}))
    logging_cfg = LoggingConfig(**(raw.get("logging") or {}))

    return AppConfig(
        servers=servers,
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 60)),
        email=email,
        storage=storage,
        collection=collection,
        web=web,
        logging=logging_cfg,
    )

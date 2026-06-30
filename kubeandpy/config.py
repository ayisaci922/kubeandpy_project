from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

import yaml


@dataclass(slots=True)
class AppConfig:
    app_name: str
    namespace: str = "default"
    replicas: int = 1
    image: str = "nginx:latest"
    container_port: int = 80
    service_port: int = 80
    node_port: int = 30080
    labels: Dict[str, str] = field(default_factory=dict)
    configmap_name: str = ""
    configmap_data: Dict[str, str] = field(default_factory=dict)
    ingress_host: str = ""
    ingress_path: str = "/"

    @property
    def selector(self) -> str:
        return ",".join(f"{key}={value}" for key, value in sorted(self.labels.items()))


def _validate_config(data: Dict[str, Any]) -> None:
    required_fields = ["app_name", "replicas", "image"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required config fields: {joined}")

    if not isinstance(data["replicas"], int) or data["replicas"] < 1:
        raise ValueError("replicas must be a positive integer")

    node_port = data.get("node_port", 30080)
    if not isinstance(node_port, int) or not 30000 <= node_port <= 32767:
        raise ValueError("node_port must be an integer between 30000 and 32767")


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    _validate_config(data)

    labels = data.get("labels") or {"app": data["app_name"]}
    return AppConfig(
        app_name=data["app_name"],
        namespace=data.get("namespace", "default"),
        replicas=data["replicas"],
        image=data["image"],
        container_port=data.get("container_port", 80),
        service_port=data.get("service_port", 80),
        node_port=data.get("node_port", 30080),
        labels=labels,
        configmap_name=data.get("configmap_name", ""),
        configmap_data=data.get("configmap_data", {}),
        ingress_host=data.get("ingress_host", ""),
        ingress_path=data.get("ingress_path", "/")
    )


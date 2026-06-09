from pathlib import Path

import pytest

from kubeandpy.config import load_config


def test_load_config_reads_values(tmp_path: Path) -> None:
    config_file = tmp_path / "app.yaml"
    config_file.write_text(
        "\n".join(
            [
                "app_name: nginx-demo",
                "replicas: 2",
                "image: nginx:1.26.2",
                "node_port: 30080",
            ]
        ),
        encoding="utf-8",
    )

    app_config = load_config(config_file)

    assert app_config.app_name == "nginx-demo"
    assert app_config.replicas == 2
    assert app_config.image == "nginx:1.26.2"
    assert app_config.labels == {"app": "nginx-demo"}


def test_load_config_rejects_invalid_node_port(tmp_path: Path) -> None:
    config_file = tmp_path / "app.yaml"
    config_file.write_text(
        "\n".join(
            [
                "app_name: nginx-demo",
                "replicas: 1",
                "image: nginx:latest",
                "node_port: 29999",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="node_port"):
        load_config(config_file)


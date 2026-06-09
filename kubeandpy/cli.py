from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from kubeandpy.config import AppConfig, load_config

if TYPE_CHECKING:
    from kubeandpy.deployer import KubernetesDeployer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Kubernetes workloads on Minikube with Python.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    deploy_parser = subparsers.add_parser("deploy", help="Create or update Deployment and Service")
    deploy_parser.add_argument("--config", required=True, help="Path to YAML config file")

    update_parser = subparsers.add_parser("update", help="Patch Deployment image and wait for rollout")
    update_parser.add_argument("--config", required=True, help="Path to YAML config file")
    update_parser.add_argument("--image", required=True, help="New container image")

    delete_parser = subparsers.add_parser("delete", help="Delete Deployment and Service")
    delete_parser.add_argument("--config", required=True, help="Path to YAML config file")

    return parser


def run_with_config(app_config: AppConfig, command: str, image: str | None = None) -> None:
    from kubeandpy.deployer import KubernetesDeployer

    deployer = KubernetesDeployer(app_config)
    if command == "deploy":
        deployer.deploy()
        return
    if command == "update":
        if image is None:
            raise ValueError("image is required for update command")
        deployer.update_image(image)
        return
    if command == "delete":
        deployer.delete()
        return
    raise ValueError(f"Unsupported command: {command}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    app_config = load_config(args.config)
    run_with_config(app_config, args.command, getattr(args, "image", None))


if __name__ == "__main__":
    main()

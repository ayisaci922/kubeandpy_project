from __future__ import annotations

import subprocess
import time
from typing import Iterable

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from kubeandpy.config import AppConfig


class KubernetesDeployer:
    def __init__(self, app_config: AppConfig, poll_interval: int = 3, timeout: int = 180) -> None:
        self.app_config = app_config
        self.poll_interval = poll_interval
        self.timeout = timeout

        config.load_kube_config()
        print("[INFO] Loaded kubeconfig from local environment.")
        self.apps_api = client.AppsV1Api()
        self.core_api = client.CoreV1Api()

    def deploy(self) -> None:
        deployment = self._build_deployment()
        service = self._build_service()
        self._apply_deployment(deployment)
        self._apply_service(service)
        self.wait_for_pods_ready()
        self._print_access_url()

    def update_image(self, new_image: str) -> None:
        patch_body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": self.app_config.app_name,
                                "image": new_image,
                            }
                        ]
                    }
                }
            }
        }

        print(f"[INFO] Patching Deployment {self.app_config.app_name} with image {new_image}")
        self.apps_api.patch_namespaced_deployment(
            name=self.app_config.app_name,
            namespace=self.app_config.namespace,
            body=patch_body,
        )
        self.wait_for_rollout(new_image)
        self.wait_for_pods_ready()
        self._print_access_url()

    def delete(self) -> None:
        delete_options = client.V1DeleteOptions(propagation_policy="Foreground")
        for resource_name, deleter in (
            ("Deployment", self.apps_api.delete_namespaced_deployment),
            ("Service", self.core_api.delete_namespaced_service),
        ):
            try:
                deleter(
                    name=self.app_config.app_name,
                    namespace=self.app_config.namespace,
                    body=delete_options,
                )
                print(f"[INFO] Deleted {resource_name}: {self.app_config.app_name}")
            except ApiException as exc:
                if exc.status == 404:
                    print(f"[INFO] {resource_name} not found: {self.app_config.app_name}")
                    continue
                raise

    def wait_for_pods_ready(self) -> None:
        selector = self.app_config.selector
        print(f"[INFO] Waiting for pods with selector: {selector}")
        deadline = time.time() + self.timeout

        while time.time() < deadline:
            pods = self._list_pods()
            if len(pods) < self.app_config.replicas:
                print(f"[INFO] Found {len(pods)}/{self.app_config.replicas} pods.")
                time.sleep(self.poll_interval)
                continue

            ready_pods = [pod for pod in pods if self._is_pod_ready(pod)]
            if len(ready_pods) == self.app_config.replicas:
                for pod in ready_pods:
                    print(f"[INFO] Pod {pod.metadata.name} is Running and Ready.")
                return

            print(f"[INFO] Ready pods: {len(ready_pods)}/{self.app_config.replicas}")
            time.sleep(self.poll_interval)

        raise TimeoutError("Timed out waiting for all pods to become Running and Ready")

    def wait_for_rollout(self, expected_image: str) -> None:
        deadline = time.time() + self.timeout
        print(f"[INFO] Waiting for rollout of image: {expected_image}")

        while time.time() < deadline:
            deployment = self.apps_api.read_namespaced_deployment(
                name=self.app_config.app_name,
                namespace=self.app_config.namespace,
            )

            status = deployment.status
            spec = deployment.spec
            observed = status.observed_generation == deployment.metadata.generation
            available = (status.available_replicas or 0) == spec.replicas
            updated = (status.updated_replicas or 0) == spec.replicas

            containers = deployment.spec.template.spec.containers
            images_match = any(container.image == expected_image for container in containers)

            if observed and available and updated and images_match:
                print("[INFO] Deployment rollout completed.")
                return

            print(
                "[INFO] Rollout status: "
                f"observed={observed}, available={status.available_replicas or 0}/{spec.replicas}, "
                f"updated={status.updated_replicas or 0}/{spec.replicas}"
            )
            time.sleep(self.poll_interval)

        raise TimeoutError("Timed out waiting for deployment rollout")

    def _apply_deployment(self, deployment: client.V1Deployment) -> None:
        namespace = self.app_config.namespace
        name = self.app_config.app_name
        print(f"[INFO] Applying Deployment: {name}")
        try:
            self.apps_api.read_namespaced_deployment(name=name, namespace=namespace)
            self.apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
            print(f"[INFO] Updated existing Deployment: {name}")
        except ApiException as exc:
            if exc.status != 404:
                raise
            self.apps_api.create_namespaced_deployment(namespace=namespace, body=deployment)
            print(f"[INFO] Created Deployment: {name}")

    def _apply_service(self, service: client.V1Service) -> None:
        namespace = self.app_config.namespace
        name = self.app_config.app_name
        print(f"[INFO] Applying Service: {name}")
        try:
            self.core_api.read_namespaced_service(name=name, namespace=namespace)
            self.core_api.patch_namespaced_service(name=name, namespace=namespace, body=service)
            print(f"[INFO] Updated existing Service: {name}")
        except ApiException as exc:
            if exc.status != 404:
                raise
            self.core_api.create_namespaced_service(namespace=namespace, body=service)
            print(f"[INFO] Created Service: {name}")

    def _build_deployment(self) -> client.V1Deployment:
        labels = self.app_config.labels
        container = client.V1Container(
            name=self.app_config.app_name,
            image=self.app_config.image,
            ports=[client.V1ContainerPort(container_port=self.app_config.container_port)],
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels),
            spec=client.V1PodSpec(containers=[container]),
        )

        selector = client.V1LabelSelector(match_labels=labels)
        spec = client.V1DeploymentSpec(
            replicas=self.app_config.replicas,
            selector=selector,
            template=template,
        )

        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=self.app_config.app_name, labels=labels),
            spec=spec,
        )

    def _build_service(self) -> client.V1Service:
        labels = self.app_config.labels
        port = client.V1ServicePort(
            port=self.app_config.service_port,
            target_port=self.app_config.container_port,
            node_port=self.app_config.node_port,
        )
        spec = client.V1ServiceSpec(
            type="NodePort",
            selector=labels,
            ports=[port],
        )
        return client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=self.app_config.app_name, labels=labels),
            spec=spec,
        )

    def _list_pods(self) -> Iterable[client.V1Pod]:
        response = self.core_api.list_namespaced_pod(
            namespace=self.app_config.namespace,
            label_selector=self.app_config.selector,
        )
        return response.items

    @staticmethod
    def _is_pod_ready(pod: client.V1Pod) -> bool:
        if pod.status.phase != "Running":
            return False

        conditions = pod.status.conditions or []
        return any(condition.type == "Ready" and condition.status == "True" for condition in conditions)

    def _print_access_url(self) -> None:
        try:
            minikube_ip = subprocess.check_output(
                ["minikube", "ip"],
                text=True,
                timeout=15,
            ).strip()
            print(f"[INFO] Application is available at http://{minikube_ip}:{self.app_config.node_port}")
        except (FileNotFoundError, subprocess.SubprocessError):
            print(
                "[WARN] Could not resolve Minikube IP automatically. "
                f"Use NodePort {self.app_config.node_port} to access the app."
            )

# 使用说明

## 功能说明

本项目提供三个核心操作：

- `deploy`：创建或更新 Deployment，并创建 NodePort Service
- `update`：通过 patch 修改镜像，等待滚动更新完成
- `delete`：删除 Deployment 和 Service

## 配置字段

| 字段 | 说明 | 示例 |
| --- | --- | --- |
| `app_name` | 应用名称，也是 Deployment 和 Service 名称 | `nginx-demo` |
| `namespace` | 部署命名空间 | `default` |
| `replicas` | 副本数 | `2` |
| `image` | 容器镜像 | `nginx:1.26.2` |
| `container_port` | 容器监听端口 | `80` |
| `service_port` | Service 暴露端口 | `80` |
| `node_port` | NodePort 端口 | `30080` |
| `labels` | 资源标签 | `app: nginx-demo` |

## 运行流程

### deploy

1. 读取 YAML 配置
2. 加载本地 kubeconfig
3. 创建或更新 Deployment
4. 创建或更新 Service
5. 基于 `label_selector` 查询 Pod
6. 等待所有 Pod `Running + Ready`
7. 输出 Minikube 访问地址

### update

1. 读取 YAML 配置
2. 使用新的镜像名构造 patch body
3. 调用 `patch_namespaced_deployment`
4. 轮询 Deployment 状态
5. 再次通过标签选择器检查 Pod 就绪状态

## 典型输出

```text
[INFO] Loaded kubeconfig from local environment.
[INFO] Applying Deployment: nginx-demo
[INFO] Applying Service: nginx-demo
[INFO] Waiting for pods with selector: app=nginx-demo
[INFO] Pod nginx-demo-7dd8b8fd77-bq7ms is Running and Ready.
[INFO] Pod nginx-demo-7dd8b8fd77-z6w7f is Running and Ready.
[INFO] Application is available at http://192.168.49.2:30080
```

## Minikube 验证

```bash
minikube ip
curl http://$(minikube ip):30080
```

如果更新镜像后 Pod 名发生变化，这是正常现象，因为 Deployment 会创建新的 ReplicaSet 并逐步替换旧 Pod。


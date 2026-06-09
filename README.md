# kubeandpy

使用 Python 调用 Kubernetes 官方客户端库，在本地 Minikube 单节点集群中自动完成 `Deployment` 创建、`Service(NodePort)` 暴露、Pod 状态监控，以及基于 `patch` 的滚动更新。

## 项目亮点

- 通过 YAML 配置声明应用名称、副本数、镜像版本、端口和标签
- 一键部署 nginx 应用并创建 NodePort Service
- 使用 `label_selector` 动态查询 Pod 列表
- 轮询等待所有 Pod 进入 `Running` 且容器 `Ready`
- 通过 `patch_namespaced_deployment` 实现镜像滚动更新
- 自动输出 Minikube 访问地址，便于演示

## 技术栈

- Python 3
- Kubernetes `client-python`
- Minikube
- Docker
- YAML

## 目录结构

```text
kubeandpy_project/
├── config/
│   └── nginx-demo.yaml
├── docs/
│   └── usage.md
├── kubeandpy/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── deployer.py
├── tests/
│   └── test_config.py
├── .gitignore
├── README.md
└── requirements.txt
```

## 快速开始

### 1. 准备环境

确保本机已安装并启动：

- Docker
- Minikube
- Python 3.10+
- `kubectl`

启动 Minikube：

```bash
minikube start
kubectl get nodes
```

### 2. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 使用示例配置部署 nginx

```bash
python3 -m kubeandpy.cli deploy --config config/nginx-demo.yaml
```

### 4. 执行滚动更新

```bash
python3 -m kubeandpy.cli update --config config/nginx-demo.yaml --image nginx:1.27.0
```

## 示例配置

```yaml
app_name: nginx-demo
namespace: default
replicas: 2
image: nginx:1.26.2
container_port: 80
service_port: 80
node_port: 30080
labels:
  app: nginx-demo
```

## 常用命令

部署应用：

```bash
python3 -m kubeandpy.cli deploy --config config/nginx-demo.yaml
```

查看 Pod：

```bash
kubectl get pods -l app=nginx-demo -w
```

查看 Service：

```bash
kubectl get svc nginx-demo
```

滚动更新镜像：

```bash
python3 -m kubeandpy.cli update --config config/nginx-demo.yaml --image nginx:stable
```

删除资源：

```bash
python3 -m kubeandpy.cli delete --config config/nginx-demo.yaml
```

## 面试可讲的实现点

1. Python 读取 YAML 配置，构造 Deployment 和 Service 的声明式资源对象。
2. 使用标签选择器 `app=nginx-demo` 查询 Pod，而不是依赖固定 Pod 名。
3. 通过 Deployment 的 `patch` 更新镜像，触发 Kubernetes 的滚动更新机制。
4. 在客户端轮询 Deployment 和 Pod 状态，验证新版本副本已经可用。
5. 结合 Minikube IP 与 NodePort 生成最终访问地址。

## 后续可扩展

- 增加配置校验与更严格的异常处理
- 支持多环境配置
- 支持 HPA、Ingress、ConfigMap
- 增加单元测试和集成测试

详细使用说明见 [docs/usage.md](docs/usage.md)。


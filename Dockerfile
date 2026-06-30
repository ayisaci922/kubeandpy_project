FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY kubeandpy/ ./kubeandpy/

COPY config/ ./config/

CMD ["python", "-m", "kubeandpy.cli", "deploy", "--config", "config/nginx-demo.yaml"]
# 部署指南

## 概述

本文档提供 Realtime RAG 服务的完整部署指南，包括开发环境搭建、生产环境部署、配置管理和监控运维。

## 系统要求

### 硬件要求

| 环境 | CPU | 内存 | 存储 | 网络 |
|------|-----|------|------|------|
| 开发环境 | 2 核 | 4GB | 20GB | 10Mbps |
| 测试环境 | 4 核 | 8GB | 50GB | 50Mbps |
| 生产环境 | 8 核 | 16GB | 100GB | 100Mbps |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+), macOS 10.15+, Windows 10+
- **Python**: 3.8 或更高版本
- **Node.js**: 16+ (可选，用于前端开发)
- **Docker**: 20.10+ (可选，用于容器化部署)

## 开发环境部署

### 1. 克隆项目

```bash
git clone https://github.com/your-org/realtime-rag.git
cd realtime-rag
```

### 2. 创建虚拟环境

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 或使用 conda
conda create -n realtime-rag python=3.9
conda activate realtime-rag
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
vim .env
```

**必需配置**:
```bash
# Context Provider API 配置
CONTEXT_API_KEY=app-your-api-key-here
CONTEXT_BASE_URL=https://api.context.ai/v1
CONTEXT_TIMEOUT=60.0
```

### 5. 启动服务

```bash
# 开发模式启动
python run.py

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# WebSocket 测试
python tests/ws_test_client.py
```

## 生产环境部署

### 1. 系统准备

#### Ubuntu/Debian 系统

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 和依赖
sudo apt install python3.9 python3.9-venv python3-pip nginx -y

# 创建应用用户
sudo useradd -m -s /bin/bash realtime-rag
sudo usermod -aG sudo realtime-rag
```

#### CentOS/RHEL 系统

```bash
# 更新系统
sudo yum update -y

# 安装 Python 和依赖
sudo yum install python39 python39-pip nginx -y

# 创建应用用户
sudo useradd -m -s /bin/bash realtime-rag
sudo usermod -aG wheel realtime-rag
```

### 2. 应用部署

```bash
# 切换到应用用户
sudo su - realtime-rag

# 克隆代码
git clone https://github.com/your-org/realtime-rag.git
cd realtime-rag

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建配置目录
mkdir -p /home/realtime-rag/config
mkdir -p /home/realtime-rag/logs
mkdir -p /home/realtime-rag/data
```

### 3. 配置管理

#### 环境配置文件

```bash
# /home/realtime-rag/config/.env
CONTEXT_API_KEY=app-your-production-api-key
CONTEXT_BASE_URL=https://api.context.ai/v1
CONTEXT_TIMEOUT=60.0

# 应用配置
APP_TITLE=Realtime RAG Production
APP_VERSION=2.0.0
WS_PATH=/ws/realtime-asr

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/home/realtime-rag/logs/app.log
```

#### Systemd 服务配置

```bash
# /etc/systemd/system/realtime-rag.service
[Unit]
Description=Realtime RAG WebSocket Service
After=network.target

[Service]
Type=exec
User=realtime-rag
Group=realtime-rag
WorkingDirectory=/home/realtime-rag/realtime-rag
Environment=PATH=/home/realtime-rag/realtime-rag/venv/bin
ExecStart=/home/realtime-rag/realtime-rag/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/realtime-rag
upstream realtime_rag {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://realtime_rag;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # REST API 代理
    location / {
        proxy_pass http://realtime_rag;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. SSL/TLS 配置

#### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

#### 手动 SSL 配置

```nginx
# /etc/nginx/sites-available/realtime-rag-ssl
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # WebSocket 代理配置
    location /ws/ {
        proxy_pass http://realtime_rag;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # REST API 代理配置
    location / {
        proxy_pass http://realtime_rag;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. 启动服务

```bash
# 启动应用服务
sudo systemctl enable realtime-rag
sudo systemctl start realtime-rag

# 启动 Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# 检查服务状态
sudo systemctl status realtime-rag
sudo systemctl status nginx
```

## Docker 部署

### 1. 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. 创建 docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  realtime-rag:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CONTEXT_API_KEY=${CONTEXT_API_KEY}
      - CONTEXT_BASE_URL=${CONTEXT_BASE_URL:-https://api.context.ai/v1}
      - CONTEXT_TIMEOUT=${CONTEXT_TIMEOUT:-60.0}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - realtime-rag
    restart: unless-stopped
```

### 3. 构建和启动

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## Kubernetes 部署

### 1. 创建 Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: realtime-rag
  labels:
    app: realtime-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: realtime-rag
  template:
    metadata:
      labels:
        app: realtime-rag
    spec:
      containers:
      - name: realtime-rag
        image: your-registry/realtime-rag:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONTEXT_API_KEY
          valueFrom:
            secretKeyRef:
              name: realtime-rag-secrets
              key: context-api-key
        - name: CONTEXT_BASE_URL
          value: "https://api.context.ai/v1"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. 创建 Service

```yaml
# k8s-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: realtime-rag-service
spec:
  selector:
    app: realtime-rag
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. 创建 ConfigMap 和 Secret

```yaml
# k8s-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: realtime-rag-config
data:
  CONTEXT_BASE_URL: "https://api.context.ai/v1"
  CONTEXT_TIMEOUT: "60.0"

---
apiVersion: v1
kind: Secret
metadata:
  name: realtime-rag-secrets
type: Opaque
data:
  context-api-key: <base64-encoded-api-key>
```

### 4. 部署到 Kubernetes

```bash
# 创建命名空间
kubectl create namespace realtime-rag

# 部署配置
kubectl apply -f k8s-config.yaml -n realtime-rag

# 部署应用
kubectl apply -f k8s-deployment.yaml -n realtime-rag

# 部署服务
kubectl apply -f k8s-service.yaml -n realtime-rag

# 检查部署状态
kubectl get pods -n realtime-rag
kubectl get services -n realtime-rag
```

## 监控和运维

### 1. 日志管理

#### 应用日志配置

```python
# app/logging_config.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
```

#### 日志轮转配置

```bash
# /etc/logrotate.d/realtime-rag
/home/realtime-rag/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 realtime-rag realtime-rag
    postrotate
        systemctl reload realtime-rag
    endscript
}
```

### 2. 性能监控

#### Prometheus 指标

```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
ws_connections = Gauge('websocket_connections_total', 'Total WebSocket connections')
ws_messages = Counter('websocket_messages_total', 'Total WebSocket messages', ['type'])
rag_queries = Counter('rag_queries_total', 'Total RAG queries')
rag_duration = Histogram('rag_query_duration_seconds', 'RAG query duration')
```

#### Grafana 仪表板

```json
{
  "dashboard": {
    "title": "Realtime RAG Monitoring",
    "panels": [
      {
        "title": "WebSocket Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "websocket_connections_total"
          }
        ]
      },
      {
        "title": "RAG Query Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rag_query_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

### 3. 健康检查

#### 自定义健康检查

```python
# app/health.py
import asyncio
import httpx
from app.config import config

async def check_context_connectivity():
    """检查 Context Provider API 连接性"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config.CONTEXT_BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False

async def health_check():
    """综合健康检查"""
    context_ok = await check_context_connectivity()
    
    return {
        "status": "healthy" if context_ok else "degraded",
        "version": config.APP_VERSION,
        "context_configured": bool(config.CONTEXT_API_KEY),
        "context_accessible": context_ok,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 4. 备份和恢复

#### 配置备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/realtime-rag"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE

# 备份配置文件
cp -r /home/realtime-rag/config $BACKUP_DIR/$DATE/
cp -r /home/realtime-rag/logs $BACKUP_DIR/$DATE/

# 备份应用代码
tar -czf $BACKUP_DIR/$DATE/code.tar.gz /home/realtime-rag/realtime-rag

# 清理旧备份（保留 30 天）
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

## 故障排除

### 1. 常见问题

#### 连接问题

```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查防火墙
sudo ufw status
sudo firewall-cmd --list-ports

# 检查服务状态
sudo systemctl status realtime-rag
sudo journalctl -u realtime-rag -f
```

#### API 问题

```bash
# 测试 Context Provider API 连接
curl -H "Authorization: Bearer $CONTEXT_API_KEY" \
     -H "Content-Type: application/json" \
     "$CONTEXT_BASE_URL/chat-messages" \
     -d '{"query": "test", "user": "test-user", "response_mode": "blocking"}'
```

#### 性能问题

```bash
# 检查系统资源
htop
iostat -x 1
free -h
df -h

# 检查应用日志
tail -f /home/realtime-rag/logs/app.log
```

### 2. 调试工具

#### WebSocket 测试客户端

```python
# debug_ws_client.py
import asyncio
import websockets
import json

async def debug_client():
    uri = "ws://localhost:8000/ws/realtime-asr"
    async with websockets.connect(uri) as websocket:
        # 发送测试消息
        await websocket.send(json.dumps({
            "type": "asr_chunk",
            "text": "测试问题",
            "is_final": True
        }))
        
        # 接收响应
        async for message in websocket:
            print(f"Received: {message}")

asyncio.run(debug_client())
```

## 安全建议

### 1. 网络安全

- 使用 HTTPS/WSS 加密传输
- 配置防火墙规则限制访问
- 使用 VPN 或内网部署
- 定期更新 SSL 证书

### 2. 应用安全

- 定期更新依赖包
- 使用强密码和 API 密钥
- 启用访问日志和审计
- 实施速率限制

### 3. 数据安全

- 定期备份配置文件
- 加密敏感数据存储
- 实施数据访问控制
- 遵循数据保护法规

## 维护和更新

### 1. 定期维护

```bash
# 每周维护任务
# 1. 检查日志文件大小
du -sh /home/realtime-rag/logs/

# 2. 清理临时文件
find /home/realtime-rag -name "*.tmp" -delete

# 3. 更新系统包
sudo apt update && sudo apt upgrade -y

# 4. 重启服务
sudo systemctl restart realtime-rag
```

### 2. 版本更新

```bash
# 更新流程
# 1. 备份当前版本
./backup.sh

# 2. 拉取新代码
cd /home/realtime-rag/realtime-rag
git pull origin main

# 3. 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 测试新版本
python tests/ws_test_client.py

# 5. 重启服务
sudo systemctl restart realtime-rag
```

这个部署指南提供了从开发到生产的完整部署方案，包括传统部署、容器化部署和 Kubernetes 部署等多种方式，以及相应的监控、运维和安全建议。

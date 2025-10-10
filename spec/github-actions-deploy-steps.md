# GitHub Actions 自动化部署流水线操作说明

本文档说明在合并代码到指定分支（如 `main`）时，GitHub Actions 所执行的全部步骤，帮助你了解各 job、各 step 的作用以及它们之间的依赖关系。

## 工作流触发条件
- **触发事件**：推送（`push`）到 `main` 分支。
- **目的**：当代码合并到主分支后，自动运行测试并依次部署到测试环境与生产环境。

## Job 与 Step 详情

### 1. `build-test` Job —— 构建与测试
| 顺序 | Step | 说明 |
| --- | --- | --- |
| 1 | `actions/checkout@v4` | 拉取最新的仓库代码供后续步骤使用。 |
| 2 | `actions/setup-python@v5` | 安装并设置所需的 Python 版本（示例为 3.10）。 |
| 3 | `pip install -r requirements.txt` | 安装项目依赖，确保环境与本地一致。 |
| 4 | `pytest` | 运行自动化测试，若失败则阻断流水线。 |

- **Job 成功条件**：所有 Step 成功执行。若任一 Step 失败，整个流水线终止，后续部署 Job 不会启动。

### 2. `deploy-staging` Job —— 部署到测试环境
| 顺序 | Step | 说明 |
| --- | --- | --- |
| 1 | `./scripts/deploy-staging.sh` | 通过自定义脚本完成测试环境的部署。 |

- **环境变量**：例如 `DIFY_API_KEY` 等密钥从仓库 Secrets 中注入。
- **依赖**：`needs: build-test`，仅在 `build-test` Job 成功后执行。
- **失败处理**：若部署失败，流水线终止，不会继续部署生产环境。

### 3. `deploy-prod` Job —— 部署到生产环境
| 顺序 | Step | 说明 |
| --- | --- | --- |
| 1 | `./scripts/deploy-prod.sh` | 执行生产环境部署脚本，通常包含镜像发布或服务重启。 |

- **环境变量**：从 GitHub Actions 环境 `production` 注入生产级 Secrets。
- **依赖**：`needs: deploy-staging`，在测试环境部署成功后才会触发。
- **审批**：可配置 `environment` 的审批策略以确保人工确认。

## 可选的脚本内容示例
以下示例展示 `deploy-staging.sh` 可能包含的操作：
```bash
#!/usr/bin/env bash
set -euo pipefail

# 拉取最新镜像或同步代码
# docker pull registry.example.com/realtime-rag:latest

# 更新服务，例如使用 SSH 进入服务器执行部署命令
ssh user@staging.example.com <<'REMOTE'
  cd /opt/services/realtime-rag
  git fetch --all
  git reset --hard origin/main
  source /opt/services/venv/bin/activate
  pip install -r requirements.txt
  systemctl restart realtime-rag
REMOTE
```

生产环境脚本可在此基础上添加更多检查、蓝绿发布或回滚逻辑。

## 成功完成部署后的建议操作
- 结合监控系统验证服务健康状况。
- 关注日志输出，确保新版本稳定运行。
- 若出现问题，可利用 Git 标签、Docker 镜像或脚本自带的回滚机制恢复到上一版本。

## 完整工作流 YAML 示例
```yaml
name: CI-CD Deploy

on:
  push:
    branches: [main]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest

  deploy-staging:
    needs: build-test
    runs-on: ubuntu-latest
    steps:
      - run: ./scripts/deploy-staging.sh
        env:
          DIFY_API_KEY: ${{ secrets.STAGING_DIFY_API_KEY }}

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      deployment_branch_policy: required
    steps:
      - run: ./scripts/deploy-prod.sh
        env:
          DIFY_API_KEY: ${{ secrets.PROD_DIFY_API_KEY }}
```

以上即 GitHub Actions 在自动部署流程中执行的全部核心操作。

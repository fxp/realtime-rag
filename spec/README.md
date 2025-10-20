# 规范文档

本目录包含 Realtime RAG 服务的完整规范文档，遵循 [GitHub spec-kit](https://github.com/github/spec-kit) 标准，采用规范驱动开发（Spec-Driven Development）方法。

## 文档结构

### 核心规范文档 (GitHub Spec-Kit 标准)

#### 规范驱动开发文档
- [**规范文档**](spec.md) - 功能需求、用户故事和验收标准
- [**技术计划**](plan.md) - 架构设计、技术选型和实现计划
- [**任务分解**](tasks.md) - 具体的可执行任务和测试策略
- [**数据模型**](data-model.md) - 数据结构和实体关系定义
- [**技术研究**](research.md) - 技术决策依据和研究过程

#### API 契约文档
- [**API 规范**](contracts/api-spec.yaml) - OpenAPI 3.0 格式的 API 契约
- [**API 参考**](api-reference.md) - REST API 和 WebSocket API 详细说明

### 架构和设计文档

#### 系统架构
- [**架构文档**](architecture.md) - 系统架构和组件设计
- [**实时 WebSocket 协议**](protocols/realtime-websocket.md) - WebSocket 通信协议规范

#### 产品文档
- [**产品概述**](product-overview.md) - 产品功能、特性和应用场景
- [**部署指南**](deployment-guide.md) - 完整的部署和运维指南
- [**提供商扩展指南**](provider-extension-guide.md) - 如何添加新的 RAG 和搜索服务提供商

## 文档结构图

```
spec/
├── README.md                           # 本文件 - 文档导航
├── CONSTITUTION.md                     # 项目宪法 - 架构原则和质量标准
├── CHECKLIST.md                        # 规范完整性检查清单
├── spec.md                            # 核心规范文档 (GitHub Spec-Kit)
├── plan.md                            # 技术实现计划 (GitHub Spec-Kit)
├── tasks.md                           # 任务分解 (GitHub Spec-Kit)
├── data-model.md                      # 数据模型定义 (GitHub Spec-Kit)
├── research.md                        # 技术研究记录 (GitHub Spec-Kit)
├── contracts/                         # API 契约目录 (GitHub Spec-Kit)
│   └── api-spec.yaml                 # OpenAPI 3.0 API 契约
├── architecture.md                    # 系统架构文档
├── api-reference.md                   # API 参考文档
├── product-overview.md                # 产品概述文档
├── deployment-guide.md                # 部署指南文档
├── provider-extension-guide.md        # 提供商扩展指南
└── protocols/                         # 协议规范目录
    └── realtime-websocket.md          # WebSocket 协议规范
```

## 快速导航

### 规范驱动开发流程

#### 1. 需求分析阶段
- **功能需求** → [规范文档](spec.md) - 了解功能需求和验收标准
- **用户故事** → [规范文档 - 用户故事](spec.md#用户故事) - 理解用户需求
- **技术约束** → [规范文档 - 技术约束](spec.md#技术约束) - 了解技术限制

#### 2. 技术设计阶段
- **架构设计** → [技术计划](plan.md) - 查看架构设计和技术选型
- **数据模型** → [数据模型](data-model.md) - 了解数据结构和实体关系
- **技术决策** → [技术研究](research.md) - 理解技术决策依据

#### 3. 开发实施阶段
- **任务规划** → [任务分解](tasks.md) - 查看开发任务和测试策略
- **API 集成** → [API 契约](contracts/api-spec.yaml) - 查看 OpenAPI 规范
- **实现参考** → [架构文档](architecture.md) - 了解系统架构

#### 4. 部署运维阶段
- **部署指南** → [部署指南](deployment-guide.md) - 查看部署和配置说明
- **扩展开发** → [提供商扩展指南](provider-extension-guide.md) - 了解如何扩展服务

### 角色导航

#### 开发者
- **系统理解** → [架构文档](architecture.md) + [技术计划](plan.md)
- **API 集成** → [API 契约](contracts/api-spec.yaml) + [API 参考](api-reference.md)
- **数据模型** → [数据模型](data-model.md)
- **扩展开发** → [提供商扩展指南](provider-extension-guide.md)

#### 产品经理
- **产品功能** → [产品概述](product-overview.md)
- **用户需求** → [规范文档 - 用户故事](spec.md#用户故事)
- **验收标准** → [规范文档 - 验收标准](spec.md#验收标准)

#### 运维人员
- **部署配置** → [部署指南](deployment-guide.md)
- **监控运维** → [部署指南 - 监控章节](deployment-guide.md#监控和运维)
- **架构理解** → [架构文档](architecture.md)

#### 测试人员
- **测试策略** → [任务分解 - 测试策略](tasks.md#测试策略)
- **验收标准** → [规范文档 - 验收标准](spec.md#验收标准)
- **API 测试** → [API 契约](contracts/api-spec.yaml)

## GitHub Spec-Kit 规范

### 规范驱动开发 (SDD) 流程

1. **规范阶段** (`spec.md`)
   - 定义功能需求和用户故事
   - 明确验收标准和技术约束
   - 识别风险和假设

2. **计划阶段** (`plan.md`)
   - 制定技术实现计划
   - 设计系统架构和数据模型
   - 选择技术栈和工具

3. **任务阶段** (`tasks.md`)
   - 分解具体开发任务
   - 定义测试策略和质量标准
   - 制定迭代计划

4. **研究阶段** (`research.md`)
   - 记录技术决策依据
   - 分析权衡取舍
   - 总结经验教训

5. **契约阶段** (`contracts/`)
   - 定义 API 契约
   - 生成 Mock 和测试
   - 维护文档同步

## 文档维护

### 更新原则
- **同步更新**：代码变更时同步更新相关文档
- **版本一致**：保持文档版本与代码版本一致
- **质量保证**：确保文档的准确性和完整性

### 更新流程
1. **需求变更** → 更新 `spec.md`
2. **技术决策** → 更新 `plan.md` 和 `research.md`
3. **任务调整** → 更新 `tasks.md`
4. **API 变更** → 更新 `contracts/api-spec.yaml`
5. **架构调整** → 更新 `architecture.md`

### 版本管理
- 使用语义化版本控制
- 维护变更日志
- 标记重要里程碑

### 质量检查
- 定期审查文档准确性
- 确保文档与实现一致
- 验证链接和引用有效性

# RAG 服务抽象架构总结

## 🎯 重构目标

将原本硬编码的 Dify 集成抽象为通用的 RAG/搜索服务提供商架构，支持：

- **多种 RAG 服务**: Dify、OpenAI、自定义 RAG 服务等
- **多种搜索服务**: Serper、Google Search、自定义搜索服务等
- **灵活配置**: 通过环境变量动态切换服务提供商
- **易于扩展**: 标准化的接口，便于添加新的服务提供商

## 📁 新增文件结构

```
app/services/
├── rag_service.py              # RAG 服务管理器
├── rag_providers/              # 提供商抽象层
│   ├── __init__.py
│   ├── base.py                 # 基础抽象类
│   ├── dify.py                 # Dify 提供商实现
│   ├── serper.py               # Serper 提供商实现
│   └── custom.py               # 自定义提供商示例
└── text_utils.py               # 文本处理工具（保持不变）

examples/
├── rag_service_example.py      # RAG 服务使用示例
└── custom_provider_example.py  # 自定义提供商示例

tests/
└── test_rag_providers.py       # 提供商测试

spec/
└── provider-extension-guide.md # 提供商扩展指南
```

## 🔧 核心组件

### 1. 基础抽象类 (`base.py`)

```python
# RAG 提供商基类
class BaseRAGProvider(ABC):
    @abstractmethod
    async def query(self, text: str, user: str, **kwargs) -> QueryResult:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass

# 搜索提供商基类
class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int, **kwargs) -> QueryResult:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

### 2. 统一结果格式 (`QueryResult`)

```python
@dataclass
class QueryResult:
    content: str                           # 主要回答内容
    metadata: Optional[Dict[str, Any]]     # 元数据（使用统计等）
    sources: Optional[list]                # 来源信息
    usage: Optional[Dict[str, Any]]        # 使用情况统计
```

### 3. 服务管理器 (`rag_service.py`)

```python
class RAGService:
    def __init__(self, config: Dict[str, Any]):
        # 初始化 RAG 和搜索提供商
        
    async def query(self, text: str, use_search: bool = False, **kwargs) -> QueryResult:
        # 统一的查询接口，自动选择 RAG 或搜索服务
        
    async def health_check(self) -> Dict[str, bool]:
        # 检查所有提供商的健康状态
```

## ⚙️ 配置管理

### 环境变量配置

```bash
# 服务提供商选择
RAG_PROVIDER=dify          # 或 custom, openai 等
SEARCH_PROVIDER=serper     # 或 custom, google 等

# Dify 配置（当 RAG_PROVIDER=dify 时）
DIFY_API_KEY=your-api-key
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_TIMEOUT=60.0

# Serper 配置（当 SEARCH_PROVIDER=serper 时）
SERPER_API_KEY=your-serper-key
SERPER_TIMEOUT=30.0
```

### 动态配置生成

```python
class Config:
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        if cls.RAG_PROVIDER == "dify":
            return {
                "provider": "dify",
                "config": {
                    "api_key": cls.DIFY_API_KEY,
                    "base_url": cls.DIFY_BASE_URL,
                    "timeout": cls.DIFY_TIMEOUT
                }
            }
        # 可以扩展其他提供商...
```

## 🚀 使用示例

### 基本使用

```python
from app.services.rag_service import RAGService
from app.config import config

# 初始化服务
service_config = config.get_service_config()
rag_service = RAGService(service_config)

# 执行查询
result = await rag_service.query(
    text="什么是人工智能？",
    user="user123",
    use_search=False  # 使用 RAG 服务
)

print(result.content)
print(result.metadata)
```

### 智能服务选择

```python
# WebSocket 路由中的智能选择逻辑
use_search = any(keyword in question.lower() for keyword in [
    "搜索", "查找", "找", "search", "find", "lookup"
])

result = await rag_service.query(
    text=question,
    user=f"ws-user-{session.session_id}",
    use_search=use_search
)
```

## 🔌 扩展新提供商

### 1. 创建提供商类

```python
class MyRAGProvider(BaseRAGProvider):
    def _validate_config(self) -> None:
        # 验证配置参数
        
    async def query(self, text: str, **kwargs) -> QueryResult:
        # 实现具体的查询逻辑
        return QueryResult(content=answer, metadata=metadata)
    
    async def health_check(self) -> bool:
        # 实现健康检查
        return True
```

### 2. 注册提供商

```python
RAGProviderFactory.register_provider("my_rag", MyRAGProvider)
```

### 3. 配置提供商

```python
config = {
    "rag": {
        "provider": "my_rag",
        "config": {
            "api_key": "your-key",
            "endpoint": "https://api.myrag.com/query"
        }
    }
}
```

## 📊 架构优势

### 1. 解耦合
- **服务抽象**: 业务逻辑与具体服务提供商解耦
- **配置驱动**: 通过配置而非代码切换服务提供商
- **接口统一**: 所有提供商使用相同的接口

### 2. 可扩展性
- **插件化**: 新的提供商可以独立开发和集成
- **工厂模式**: 通过工厂类管理提供商注册和创建
- **标准接口**: 遵循统一的标准接口规范

### 3. 可维护性
- **模块化**: 每个提供商独立成模块
- **测试友好**: 每个提供商可以独立测试
- **文档完善**: 提供详细的扩展指南和示例

### 4. 向后兼容
- **渐进迁移**: 保持原有 Dify 配置的兼容性
- **平滑升级**: 可以逐步迁移到新的抽象架构
- **配置简化**: 通过环境变量简化配置管理

## 🔄 迁移指南

### 从旧版本迁移

1. **保持现有配置**: 原有的 `DIFY_API_KEY` 等配置仍然有效
2. **新增提供商配置**: 可以添加 `SERPER_API_KEY` 等新配置
3. **更新依赖**: 无需额外依赖，使用现有的 `httpx`
4. **测试验证**: 运行测试确保功能正常

### 配置迁移

```bash
# 旧配置（仍然有效）
DIFY_API_KEY=your-dify-key
DIFY_BASE_URL=https://api.dify.ai/v1

# 新配置（可选）
RAG_PROVIDER=dify              # 明确指定 RAG 提供商
SEARCH_PROVIDER=serper         # 新增搜索提供商
SERPER_API_KEY=your-serper-key # 新增搜索配置
```

## 🧪 测试覆盖

### 单元测试
- 每个提供商的配置验证
- 查询方法的功能测试
- 健康检查的测试
- 错误处理的测试

### 集成测试
- RAG 服务管理器的集成测试
- 多提供商切换的测试
- WebSocket 集成的测试

### 示例代码
- 基本使用示例
- 自定义提供商示例
- 配置示例

## 📚 文档更新

### 更新的文档
- **架构文档**: 新增 RAG 提供商抽象层说明
- **API 参考**: 新增多提供商配置说明
- **部署指南**: 新增多提供商部署配置

### 新增文档
- **提供商扩展指南**: 详细的扩展开发指南
- **示例代码**: 完整的使用和扩展示例

## 🎉 总结

通过这次抽象化重构，我们实现了：

✅ **服务解耦**: 将 Dify 硬编码集成抽象为通用 RAG/搜索服务接口  
✅ **多提供商支持**: 支持 Dify、Serper 等多种服务提供商  
✅ **配置驱动**: 通过环境变量动态切换服务提供商  
✅ **易于扩展**: 标准化的接口，便于添加新的服务提供商  
✅ **向后兼容**: 保持原有配置和功能的兼容性  
✅ **文档完善**: 提供详细的扩展指南和使用示例  

这个抽象架构为系统提供了强大的灵活性和可扩展性，使得集成新的 RAG 和搜索服务变得简单而标准化。

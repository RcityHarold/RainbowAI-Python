# 彩虹城 AI 对话管理系统 (RainbowAI Dialogue Management System)

<p align="center">
  <img src="https://via.placeholder.com/200x200?text=RainbowAI" alt="RainbowAI Logo" width="200"/>
</p>

<p align="center">
  <strong>构建智能、自然、多模态的人机对话系统</strong>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#系统架构">系统架构</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#接口文档">接口文档</a> •
  <a href="#开发进度">开发进度</a> •
  <a href="#贡献指南">贡献指南</a>
</p>

## 项目概述

彩虹城 AI 对话管理系统是所有 AI Agent 能力的中枢，负责「输入解析 × 上下文整合 × 响应生成 × 多方调度」，作为人类与 AI 伙伴之间所有交互的基础设施。系统支持多模态输入、上下文管理、工具调用和响应生成，为构建智能对话体验提供完整解决方案。

### 功能特性

- **多轮对话管理**：支持持续的多轮对话，保持上下文连贯性
- **多种对话类型**：支持七种对话类型，包括人类-AI私聊、人类-人类群聊、AI自省等
- **会话与对话分离**：清晰的会话和对话划分，支持多级组织结构
- **多模型支持**：可集成多种 LLM 模型，如 OpenAI、Claude 等
- **数据持久化**：使用 SurrealDB 实现对话和消息的持久化存储
- **分页与筛选**：支持对话和消息的高级筛选、分页和搜索
- **工具调用框架**：模块化的工具系统，支持计算器、天气查询、搜索等功能
- **实时通信**：WebSocket支持，实现消息推送和状态更新
- **流式响应**：支持AI生成内容的实时流式显示
- **多模态处理**：支持图像、音频等多媒体内容的上传和处理
- **全链路日志**：详细的请求跟踪和日志记录，支持请求ID关联
- **RESTful API**：标准的 REST API 接口，支持各种客户端集成与调用
- **可扩展架构**：模块化设计，便于功能扩展和定制
- **完整日志系统**：详细记录系统操作，便于调试和分析

## 系统架构

### 核心三方角色

- **人类用户**：发起交流意图，包括语义/情感/上下文目标
- **AI 模型**：执行推理/生成能力（如 GPT 等 LLM 模型）
- **系统模块**：处理所有中间过程，包括上下文管理、接口协调、插件调用等

### 系统模块划分

| 模块 | 主要职责 | 协作模块 |
| ------ | -------------------- | -------------------- |
| InputHub | 捕获人类输入（包括语音/文本/情感） | 语音识别系统、行为感知系统 |
| DialogueCore | 路由到不同对话类型处理流程 | 用户权限系统、LIO系统 |
| ContextBuilder | 从记忆系统/意识核心/当前对话整合上下文提示 | 记忆系统、人格系统、环境系统 |
| LLMCaller | 执行大模型API调用，支持链式推理、多轮生成 | 插件系统、日志系统 |
| ToolInvoker | 连接外部API工具模块，获取信息，分析处理结果 | 插件系统、能力图谱系统 |
| ResponseMixer | 整合插件内容、模型回复、插入模块形成最终消息 | 插件、翻译器、情感修饰器 |

### 数据结构

系统采用四层数据结构：

- **消息 (Message)**：最小信息单元，支持多模态（文本、图像、音频等）
- **轮次 (Turn)**：意图交互单元，包括发起者、响应者、状态等
- **会话 (Session)**：上下文段落，自动分段或AI自省任务
- **对话 (Dialogue)**：唯一主容器，聚合所有会话

### 技术栈

- **后端**：Python (FastAPI)
- **数据库**：SurrealDB
- **LLM 接口**：支持多种大模型 API
- **部署**：Docker/Kubernetes

## 快速开始

### 环境要求

- Python 3.8+
- SurrealDB (可选，默认使用内存存储)

### 安装

1. 克隆仓库

```bash
git clone https://github.com/yourusername/RainbowAI-Python.git
cd RainbowAI-Python
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

```bash
cp app/.env.example .env
# 编辑 .env 文件，设置必要的配置项
```

4. 启动服务

```bash
python -m app.main
```

服务将在 http://localhost:8000 启动，可以通过 http://localhost:8000/docs 访问 API 文档。

### 使用 Docker 部署

```bash
# 构建镜像
docker build -t rainbowai-python .

# 运行容器
docker run -p 8000:8000 rainbowai-python
```

## 接口文档

系统提供以下主要 API 端点：

### 对话管理

- `POST /api/input` - 处理用户输入并生成响应
  - **输入参数**：
    - `type`: 输入类型（text、image、audio等）
    - `data`: 输入数据（文本内容或媒体文件引用）
    - `user_id`: 用户ID
    - `dialogue_id`: 对话ID
    - `session_id`: 会话ID（可选）
    - `turn_id`: 轮次ID（可选）
  - **输出结果**：
    ```json
    {
      "message_id": "消息ID",
      "status": "processing",
      "content": "内容",
      "content_type": "内容类型"
    }
    ```

- `GET /api/dialogues` - 获取对话列表，支持分页和筛选
  - **输入参数**：
    - `page`: 页码（默认1）
    - `page_size`: 每页数量（默认20）
    - `human_id`: 人类ID（可选）
    - `ai_id`: AI ID（可选）
    - `dialogue_type`: 对话类型（可选）
    - `status`: 状态（active/closed，可选）
    - `start_date`: 开始日期（可选）
    - `end_date`: 结束日期（可选）
    - `search_text`: 搜索文本（可选）
  - **输出结果**：
    ```json
    {
      "items": [对话对象列表],
      "total": 总数量,
      "page": 当前页码,
      "page_size": 每页数量,
      "total_pages": 总页数
    }
    ```

- `GET /api/dialogues/{dialogue_id}` - 获取特定对话
  - **输入参数**：
    - `dialogue_id`: 对话ID（路径参数）
  - **输出结果**：
    ```json
    {
      "dialogue": 对话对象,
      "sessions": [会话对象列表]
    }
    ```

- `POST /api/dialogues/new` - 创建新对话
  - **输入参数**：
    - `dialogue_type`: 对话类型
    - `human_id`: 人类ID（可选）
    - `ai_id`: AI ID（可选）
    - `title`: 标题（可选）
    - `description`: 描述（可选）
    - `metadata`: 元数据（可选）
  - **输出结果**：
    ```json
    {
      "dialogue": 对话对象,
      "sessions": [初始会话对象]
    }
    ```

- `POST /api/dialogues/close/{dialogue_id}` - 关闭对话
  - **输入参数**：
    - `dialogue_id`: 对话ID（路径参数）
  - **输出结果**：
    ```json
    {
      "success": true,
      "dialogue_id": "对话ID",
      "status": "closed"
    }
    ```

- `POST /api/dialogues/ai_self` - 创建 AI 自省对话
  - **输入参数**：
    - `ai_id`: AI ID
    - `goal`: 自省目标
    - `title`: 标题（可选）
    - `metadata`: 元数据（可选）
  - **输出结果**：与创建新对话相同

- `POST /api/dialogues/ai_ai` - 创建 AI ⇄ AI 对话
  - **输入参数**：
    - `ai_id_1`: 第一个AI ID
    - `ai_id_2`: 第二个AI ID
    - `topic`: 对话主题
    - `title`: 标题（可选）
    - `metadata`: 元数据（可选）
  - **输出结果**：与创建新对话相同

- `POST /api/dialogues/human_human_private` - 创建人类 ⇄ 人类私聊对话
  - **输入参数**：
    - `human_id_1`: 第一个人类ID
    - `human_id_2`: 第二个人类ID
    - `title`: 标题（可选）
    - `metadata`: 元数据（可选）
  - **输出结果**：与创建新对话相同

- `POST /api/dialogues/human_human_group` - 创建人类 ⇄ 人类群聊对话
  - **输入参数**：
    - `human_ids`: 人类ID列表
    - `title`: 群聊标题
    - `creator_id`: 创建者ID
    - `metadata`: 元数据（可选）
  - **输出结果**：与创建新对话相同

- `POST /api/dialogues/human_ai_group` - 创建人类 ⇄ AI 群组对话
  - **输入参数**：
    - `human_ids`: 人类ID列表
    - `ai_id`: AI ID
    - `title`: 群组标题
    - `metadata`: 元数据（可选）
  - **输出结果**：与创建新对话相同

- `POST /api/dialogues/ai_multi_human` - 创建 AI ⇄ 多人类群组对话
  - **输入参数**：
    - `ai_id`: AI ID
    - `human_ids`: 人类ID列表
    - `title`: 群组标题
    - `metadata`: 元数据（可选）
  - **输出结果**：与创建新对话相同

### 统一对话查询 API

- `GET /api/query/dialogues` - 查询对话列表，支持高级筛选和分页
  - **输入参数**：
{{ ... }}
    - `query`: 搜索关键词
    - `dialogue_type`: 对话类型
    - `human_id`: 人类ID
    - `ai_id`: AI ID
    - `is_active`: 是否活跃
    - `since`: 开始时间
    - `until`: 结束时间
    - `page`: 页码
    - `page_size`: 每页数量
  - **输出结果**：
    ```json
    {
      "items": [对话对象列表],
      "total": 总数量,
      "page": 当前页码,
      "page_size": 每页数量,
      "total_pages": 总页数
    }
    ```

- `GET /api/query/sessions` - 查询会话列表，支持高级筛选和分页
  - **输入参数**：
    - `dialogue_id`: 对话ID
    - `session_type`: 会话类型
    - `created_by`: 创建者
    - `is_active`: 是否活跃
    - `since`: 开始时间
    - `until`: 结束时间
    - `page`: 页码
    - `page_size`: 每页数量
  - **输出结果**：与对话查询类似的分页响应

- `GET /api/query/turns` - 查询轮次列表，支持高级筛选和分页
  - **输入参数**：
    - `dialogue_id`: 对话ID
    - `session_id`: 会话ID
    - `initiator_role`: 发起者角色
    - `responder_role`: 响应者角色
    - `is_completed`: 是否已完成
    - `since`: 开始时间
    - `until`: 结束时间
    - `page`: 页码
    - `page_size`: 每页数量
  - **输出结果**：与对话查询类似的分页响应

- `GET /api/query/messages` - 查询消息列表，支持高级筛选和分页
  - **输入参数**：
    - `dialogue_id`: 对话ID
    - `session_id`: 会话ID
    - `turn_id`: 轮次ID
    - `sender_role`: 发送者角色
    - `sender_id`: 发送者ID
    - `content_type`: 内容类型
    - `query`: 搜索关键词
    - `since`: 开始时间
    - `until`: 结束时间
    - `page`: 页码
    - `page_size`: 每页数量
  - **输出结果**：与对话查询类似的分页响应

- `GET /api/query/dialogues/{dialogue_id}` - 获取对话详情
  - **输出结果**：
    ```json
    {
      "dialogue": 对话对象,
      "sessions": [会话对象列表],
      "latest_messages": [最新消息列表]
    }
    ```

- `GET /api/query/sessions/{session_id}` - 获取会话详情
  - **输出结果**：
    ```json
    {
      "session": 会话对象,
      "turns": [轮次对象列表],
      "messages": [消息对象列表]
    }
    ```

- `GET /api/query/turns/{turn_id}` - 获取轮次详情
  - **输出结果**：
    ```json
    {
      "turn": 轮次对象,
      "messages": [消息对象列表]
    }
    ```

- `GET /api/query/unresponded_turns` - 获取未回应的轮次
  - **输入参数**：
    - `dialogue_id`: 对话ID（可选）
  - **输出结果**：轮次对象列表

- `GET /api/query/recent_sessions` - 获取最近活跃的会话
  - **输入参数**：
    - `days`: 最近几天（默认7天）
    - `limit`: 限制数量（默认10条）
  - **输出结果**：会话对象列表

- `GET /api/query/search` - 搜索历史对话
  - **输入参数**：与`/api/query/dialogues`相同，但`query`参数是必需的
  - **输出结果**：与对话查询类似的分页响应

- `GET /api/query/user/{user_id}/active` - 获取用户的活跃对话
  - **输入参数**：
    - `user_id`: 用户ID
    - `role_type`: 角色类型（默认为human）
  - **输出结果**：对话对象列表

### 消息管理

- `GET /api/messages/{message_id}` - 获取特定消息
  - **输入参数**：
    - `message_id`: 消息ID（路径参数）
  - **输出结果**：
    ```json
    {
      "id": "消息ID",
      "dialogue_id": "对话ID",
      "session_id": "会话ID",
      "turn_id": "轮次ID",
      "sender_role": "发送者角色",
      "sender_id": "发送者ID",
      "content": "消息内容",
      "content_type": "内容类型",
      "created_at": "创建时间",
      "metadata": {}
    }
    ```

- `GET /api/dialogues/{dialogue_id}/messages` - 获取对话中的消息，支持分页和筛选
  - **输入参数**：
    - `dialogue_id`: 对话ID（路径参数）
    - `page`: 页码（默认1）
    - `page_size`: 每页数量（默认20）
    - `role`: 角色（user/assistant，可选）
    - `content_type`: 内容类型（可选）
    - `start_date`: 开始日期（可选）
    - `end_date`: 结束日期（可选）
    - `search_text`: 搜索文本（可选）
  - **输出结果**：
    ```json
    {
      "items": [消息对象列表],
      "total": 总数量,
      "page": 当前页码,
      "page_size": 每页数量,
      "total_pages": 总页数
    }
    ```

- `GET /api/sessions/{session_id}/messages` - 获取会话中的消息，支持分页和筛选
  - **输入参数**：
    - `session_id`: 会话ID（路径参数）
    - `page`: 页码（默认1）
    - `page_size`: 每页数量（默认20）
    - `role`: 角色（user/assistant，可选）
    - `content_type`: 内容类型（可选）
    - `start_date`: 开始日期（可选）
    - `end_date`: 结束日期（可选）
    - `search_text`: 搜索文本（可选）
  - **输出结果**：与对话消息查询相同

### 工具管理

- `GET /api/tools` - 获取可用工具列表
  - **输入参数**：无
  - **输出结果**：
    ```json
    {
      "tools": [
        {
          "id": "工具ID",
          "name": "工具名称",
          "description": "工具描述",
          "category": "工具类别",
          "parameters": [参数列表],
          "required_permissions": [所需权限]
        }
      ]
    }
    ```

- `POST /api/tools` - 调用指定工具
  - **输入参数**：
    - `tool_id`: 工具ID
    - `parameters`: 工具参数对象
    - `user_id`: 用户ID
    - `dialogue_id`: 对话ID（可选）
  - **输出结果**：
    ```json
    {
      "tool_id": "工具ID",
      "status": "success",
      "result": 工具返回结果,
      "execution_time": 执行时间
    }
    ```

- `GET /api/tools/categories` - 获取工具类别
  - **输入参数**：无
  - **输出结果**：
    ```json
    {
      "categories": [
        {
          "id": "类别ID",
          "name": "类别名称",
          "description": "类别描述"
        }
      ]
    }
    ```

### 实时通信

- `WebSocket /ws` - WebSocket连接端点，支持实时消息推送
  - **连接参数**：
    - `user_id`: 用户ID（查询参数）
    - `token`: 认证令牌（查询参数）
  - **接收消息格式**：
    ```json
    {
      "type": "消息类型",
      "data": 消息数据,
      "timestamp": "时间戳"
    }
    ```
  - **发送消息格式**：
    ```json
    {
      "action": "操作类型",
      "data": 操作数据
    }
    ```

- `POST /api/notify/message` - 通知新消息
  - **输入参数**：
    - `message_id`: 消息ID
    - `dialogue_id`: 对话ID
    - `user_ids`: 需要通知的用户ID列表
  - **输出结果**：
    ```json
    {
      "success": true,
      "notification_id": "通知ID",
      "sent_to": [接收用户ID列表]
    }
    ```

- `POST /api/notify/dialogue_update` - 通知对话更新
  - **输入参数**：
    - `dialogue_id`: 对话ID
    - `update_type`: 更新类型（new_session/closed/status_change等）
    - `user_ids`: 需要通知的用户ID列表
    - `data`: 更新数据（可选）
  - **输出结果**：与通知新消息相同

- `POST /api/notify/stream_response` - 流式响应推送
  - **输入参数**：
    - `dialogue_id`: 对话ID
    - `turn_id`: 轮次ID
    - `content_chunk`: 内容块
    - `is_final`: 是否最终块
    - `user_ids`: 需要推送的用户ID列表
  - **输出结果**：
    ```json
    {
      "success": true,
      "chunk_id": "块ID",
      "sent_to": [接收用户ID列表]
    }
    ```

### 媒体处理

- `POST /api/media/upload` - 上传媒体文件
  - **输入参数**：
    - `file`: 文件数据（表单数据）
    - `category`: 媒体类别（images/audio/video）
    - `user_id`: 用户ID
    - `dialogue_id`: 对话ID（可选）
  - **输出结果**：
    ```json
    {
      "file_id": "文件ID",
      "filename": "文件名",
      "category": "类别",
      "url": "文件URL",
      "size": 文件大小,
      "mime_type": "文件类型",
      "upload_time": "上传时间"
    }
    ```

- `POST /api/media/upload/base64` - 上传Base64编码的媒体数据
  - **输入参数**：
    - `data`: Base64编码的文件数据
    - `filename`: 文件名
    - `category`: 媒体类别（images/audio/video）
    - `mime_type`: 文件MIME类型
    - `user_id`: 用户ID
    - `dialogue_id`: 对话ID（可选）
  - **输出结果**：与普通上传相同

- `GET /media/{category}/{filename}` - 获取媒体文件
  - **输入参数**：
    - `category`: 媒体类别（路径参数）
    - `filename`: 文件名（路径参数）
  - **输出结果**：直接返回文件数据，带有适当的Content-Type头

### 分页和筛选

大多数列表端点支持以下分页参数：

- `page` - 页码，默认为1
- `page_size` - 每页数量，默认为20（最大100）

对话列表支持以下筛选参数：

- `human_id` - 人类用户ID
- `ai_id` - AI ID
- `dialogue_type` - 对话类型（human_ai、ai_self、ai_ai、human_human_private、human_human_group、human_ai_group、ai_multi_human）
- `status` - 状态（active/closed）
- `start_date` - 开始日期
- `end_date` - 结束日期
- `search_text` - 搜索文本

消息列表支持以下筛选参数：

- `role` - 角色（user/assistant）
- `content_type` - 内容类型
- `start_date` - 开始日期
- `end_date` - 结束日期
- `search_text` - 搜索文本

完整 API 文档可通过启动服务后访问 Swagger UI（`/docs`）或 ReDoc（`/redoc`）获取。

## 开发进度

- [x] **阶段 1**：需求分析和系统设计
  - [x] 定义系统架构和数据模型
  - [x] 设计 API 接口
  - [x] 实现基础框架

- [x] **阶段 2**：基础能力开发
  - [x] 实现数据库集成
  - [x] 开发核心对话处理逻辑
  - [x] 集成 LLM 客户端
  - [x] 添加日志和监控系统

- [x] **阶段 3**：接口、扩展和日志
  - [x] 完善 API 接口，添加分页和筛选功能
  - [x] 实现全链路日志和请求跟踪
  - [x] 开发工具调用框架和内置工具
  - [x] 添加工具调用API端点

- [x] **阶段 4**：实时通信和多模态处理
  - [x] 实现WebSocket实时通信
  - [x] 添加流式响应功能
  - [x] 支持多模态内容处理（图像、音频等）
  - [x] 实现媒体文件上传和处理
  - [x] 实现多模态输入解析器
  - [x] 添加统一对话查询API

- [ ] **阶段 5**：测试、优化和发布
  - [ ] 全面测试覆盖
  - [ ] 性能优化
  - [ ] 安全审计
  - [ ] 文档完善

- [x] **阶段 6**：高级能力和持续迭代
  - [x] 添加自我反思能力
  - [x] 实现多智能体协作
  - [x] 支持知识库集成
  - [x] 实现自省引擎和情绪状态追踪
  - [x] 持续改进和优化

## 测试

运行单元测试：

```bash
pytest
```

运行特定测试：

```bash
pytest tests/test_dialogue_service.py
```

## 贡献指南

我们欢迎各种形式的贡献！如果您想参与项目开发，请遵循以下步骤：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

如有任何问题或建议，请通过以下方式联系我们：

- 项目负责人：[Your Name](mailto:your.email@example.com)
- 问题反馈：[GitHub Issues](https://github.com/yourusername/RainbowAI-Python/issues)

---

<p align="center">
  彩虹城 AI 团队 © 2025
</p>
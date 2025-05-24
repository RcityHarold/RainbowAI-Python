-- SurrealDB Schema for RainbowAI Dialogue Management System
-- 基于四层数据结构：Message、Turn、Session、Dialogue

-- 定义命名空间和数据库
DEFINE NAMESPACE rainbow;
USE NAMESPACE rainbow;

DEFINE DATABASE dialogue;
USE DATABASE dialogue;

-- 定义表和字段
-- 消息表（Message）
DEFINE TABLE message SCHEMAFULL;
DEFINE FIELD dialogue_id ON message TYPE string;
DEFINE FIELD session_id ON message TYPE string;
DEFINE FIELD turn_id ON message TYPE string;
DEFINE FIELD sender_role ON message TYPE string;
DEFINE FIELD sender_id ON message TYPE string;
DEFINE FIELD content ON message TYPE string;
DEFINE FIELD content_type ON message TYPE string;
DEFINE FIELD created_at ON message TYPE datetime;
DEFINE FIELD metadata ON message TYPE object;

-- 轮次表（Turn）
DEFINE TABLE turn SCHEMAFULL;
DEFINE FIELD dialogue_id ON turn TYPE string;
DEFINE FIELD session_id ON turn TYPE string;
DEFINE FIELD initiator_role ON turn TYPE string;
DEFINE FIELD responder_role ON turn TYPE string;
DEFINE FIELD started_at ON turn TYPE datetime;
DEFINE FIELD closed_at ON turn TYPE datetime;
DEFINE FIELD status ON turn TYPE string;
DEFINE FIELD response_time ON turn TYPE float;
DEFINE FIELD messages ON turn TYPE array;
DEFINE FIELD metadata ON turn TYPE object;

-- 会话表（Session）
DEFINE TABLE session SCHEMAFULL;
DEFINE FIELD dialogue_id ON session TYPE string;
DEFINE FIELD session_type ON session TYPE string;
DEFINE FIELD start_at ON session TYPE datetime;
DEFINE FIELD end_at ON session TYPE datetime;
DEFINE FIELD description ON session TYPE string;
DEFINE FIELD created_by ON session TYPE string;
DEFINE FIELD turns ON session TYPE array;
DEFINE FIELD metadata ON session TYPE object;

-- 对话表（Dialogue）
DEFINE TABLE dialogue SCHEMAFULL;
DEFINE FIELD dialogue_type ON dialogue TYPE string;
DEFINE FIELD human_id ON dialogue TYPE string;
DEFINE FIELD ai_id ON dialogue TYPE string;
DEFINE FIELD relation_id ON dialogue TYPE string;
DEFINE FIELD created_at ON dialogue TYPE datetime;
DEFINE FIELD is_active ON dialogue TYPE bool;
DEFINE FIELD last_activity_at ON dialogue TYPE datetime;
DEFINE FIELD sessions ON dialogue TYPE array;
DEFINE FIELD metadata ON dialogue TYPE object;

-- 定义索引
-- 消息索引
DEFINE INDEX message_dialogue_idx ON message FIELDS dialogue_id;
DEFINE INDEX message_session_idx ON message FIELDS session_id;
DEFINE INDEX message_turn_idx ON message FIELDS turn_id;
DEFINE INDEX message_sender_idx ON message FIELDS sender_role, sender_id;
DEFINE INDEX message_created_idx ON message FIELDS created_at;
DEFINE INDEX message_content_type_idx ON message FIELDS content_type;

-- 轮次索引
DEFINE INDEX turn_dialogue_idx ON turn FIELDS dialogue_id;
DEFINE INDEX turn_session_idx ON turn FIELDS session_id;
DEFINE INDEX turn_status_idx ON turn FIELDS status;
DEFINE INDEX turn_started_idx ON turn FIELDS started_at;

-- 会话索引
DEFINE INDEX session_dialogue_idx ON session FIELDS dialogue_id;
DEFINE INDEX session_type_idx ON session FIELDS session_type;
DEFINE INDEX session_start_idx ON session FIELDS start_at;

-- 对话索引
DEFINE INDEX dialogue_type_idx ON dialogue FIELDS dialogue_type;
DEFINE INDEX dialogue_human_idx ON dialogue FIELDS human_id;
DEFINE INDEX dialogue_ai_idx ON dialogue FIELDS ai_id;
DEFINE INDEX dialogue_active_idx ON dialogue FIELDS is_active;
DEFINE INDEX dialogue_last_activity_idx ON dialogue FIELDS last_activity_at;

-- 定义关系
-- 消息关系
DEFINE FIELD dialogue ON message TYPE record(dialogue);
DEFINE FIELD session ON message TYPE record(session);
DEFINE FIELD turn ON message TYPE record(turn);

-- 轮次关系
DEFINE FIELD dialogue ON turn TYPE record(dialogue);
DEFINE FIELD session ON turn TYPE record(session);
DEFINE FIELD message_records ON turn TYPE array<record(message)>;

-- 会话关系
DEFINE FIELD dialogue ON session TYPE record(dialogue);
DEFINE FIELD turn_records ON session TYPE array<record(turn)>;

-- 对话关系
DEFINE FIELD session_records ON dialogue TYPE array<record(session)>;

-- 创建事件表（用于日志和事件追踪）
DEFINE TABLE event_log SCHEMAFULL;
DEFINE FIELD event_type ON event_log TYPE string;
DEFINE FIELD dialogue_id ON event_log TYPE string;
DEFINE FIELD session_id ON event_log TYPE string;
DEFINE FIELD turn_id ON event_log TYPE string;
DEFINE FIELD message_id ON event_log TYPE string;
DEFINE FIELD actor_role ON event_log TYPE string;
DEFINE FIELD actor_id ON event_log TYPE string;
DEFINE FIELD event_data ON event_log TYPE object;
DEFINE FIELD created_at ON event_log TYPE datetime;

-- 创建工具调用表
DEFINE TABLE tool_call SCHEMAFULL;
DEFINE FIELD tool_id ON tool_call TYPE string;
DEFINE FIELD dialogue_id ON tool_call TYPE string;
DEFINE FIELD turn_id ON tool_call TYPE string;
DEFINE FIELD parameters ON tool_call TYPE object;
DEFINE FIELD result ON tool_call TYPE object;
DEFINE FIELD success ON tool_call TYPE bool;
DEFINE FIELD error ON tool_call TYPE string;
DEFINE FIELD execution_time ON tool_call TYPE float;
DEFINE FIELD created_at ON tool_call TYPE datetime;

-- 创建自省记录表
DEFINE TABLE introspection_session SCHEMAFULL;
DEFINE FIELD ai_id ON introspection_session TYPE string;
DEFINE FIELD session_type ON introspection_session TYPE string;
DEFINE FIELD trigger_source ON introspection_session TYPE string;
DEFINE FIELD goal ON introspection_session TYPE string;
DEFINE FIELD started_at ON introspection_session TYPE datetime;
DEFINE FIELD completed_at ON introspection_session TYPE datetime;
DEFINE FIELD steps ON introspection_session TYPE array;
DEFINE FIELD summary ON introspection_session TYPE string;
DEFINE FIELD metadata ON introspection_session TYPE object;

-- 创建多模态内容表（用于存储大型内容如图片、音频等）
DEFINE TABLE content_store SCHEMAFULL;
DEFINE FIELD message_id ON content_store TYPE string;
DEFINE FIELD content_type ON content_store TYPE string;
DEFINE FIELD content_url ON content_store TYPE string;
DEFINE FIELD content_data ON content_store TYPE string;
DEFINE FIELD metadata ON content_store TYPE object;
DEFINE FIELD created_at ON content_store TYPE datetime;

-- 创建用户表
DEFINE TABLE user SCHEMAFULL;
DEFINE FIELD username ON user TYPE string;
DEFINE FIELD display_name ON user TYPE string;
DEFINE FIELD email ON user TYPE string;
DEFINE FIELD created_at ON user TYPE datetime;
DEFINE FIELD last_login ON user TYPE datetime;
DEFINE FIELD preferences ON user TYPE object;
DEFINE FIELD metadata ON user TYPE object;

-- 创建AI表
DEFINE TABLE ai SCHEMAFULL;
DEFINE FIELD name ON ai TYPE string;
DEFINE FIELD description ON ai TYPE string;
DEFINE FIELD personality ON ai TYPE object;
DEFINE FIELD created_at ON ai TYPE datetime;
DEFINE FIELD last_active ON ai TYPE datetime;
DEFINE FIELD metadata ON ai TYPE object;

-- 创建用户索引
DEFINE INDEX user_username_idx ON user FIELDS username UNIQUE;
DEFINE INDEX user_email_idx ON user FIELDS email UNIQUE;

-- 创建AI索引
DEFINE INDEX ai_name_idx ON ai FIELDS name UNIQUE;

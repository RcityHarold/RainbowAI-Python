"""
常量定义模块
包含系统中使用的各种常量和枚举值
"""

# 对话类型常量
class DialogueTypes:
    # 人类与人类对话类型
    HUMAN_HUMAN_PRIVATE = "human_human_private"  # 人类 ⇄ 人类 私聊
    HUMAN_HUMAN_GROUP = "human_human_group"      # 人类 ⇄ 人类 群聊
    
    # 人类与AI对话类型
    HUMAN_AI = "human_ai"                        # 人类 ⇄ AI 私聊
    HUMAN_AI_GROUP = "human_ai_group"            # 人类 ⇄ AI 群组 (LIO)
    
    # AI相关对话类型
    AI_AI = "ai_ai"                              # AI ⇄ AI 对话
    AI_SELF = "ai_self"                          # AI ⇄ 自我（自省/觉知）
    AI_MULTI_HUMAN = "ai_multi_human"            # AI ⇄ 多人类 群组
    
    # 所有对话类型列表
    ALL = [
        HUMAN_HUMAN_PRIVATE,
        HUMAN_HUMAN_GROUP,
        HUMAN_AI,
        HUMAN_AI_GROUP,
        AI_AI,
        AI_SELF,
        AI_MULTI_HUMAN
    ]
    
    # 人类参与的对话类型
    HUMAN_INVOLVED = [
        HUMAN_HUMAN_PRIVATE,
        HUMAN_HUMAN_GROUP,
        HUMAN_AI,
        HUMAN_AI_GROUP,
        AI_MULTI_HUMAN
    ]
    
    # AI参与的对话类型
    AI_INVOLVED = [
        HUMAN_AI,
        HUMAN_AI_GROUP,
        AI_AI,
        AI_SELF,
        AI_MULTI_HUMAN
    ]
    
    # 群组对话类型
    GROUP_TYPES = [
        HUMAN_HUMAN_GROUP,
        HUMAN_AI_GROUP,
        AI_MULTI_HUMAN
    ]


# 会话类型常量
class SessionTypes:
    DIALOGUE = "dialogue"           # 普通对话会话
    INTROSPECTION = "introspection" # 自我反思会话
    MULTI_AGENT = "multi_agent"     # 多智能体协作会话
    GROUP_CHAT = "group_chat"       # 群聊会话
    LIO = "lio"                     # 人类-AI群组会话
    ERROR_ANALYSIS = "error_analysis"    # 错误分析会话
    PLANNING = "planning"                # 规划会话
    SYSTEM = "system"                    # 系统会话


# 消息内容类型常量
class ContentTypes:
    TEXT = "text"                        # 纯文本
    IMAGE = "image"                      # 图像
    AUDIO = "audio"                      # 音频
    VIDEO = "video"                      # 视频
    TOOL_OUTPUT = "tool_output"          # 工具输出
    MULTIMODAL_TEXT_IMAGE = "multimodal/text+image"  # 文本+图像
    MULTIMODAL_TEXT_AUDIO = "multimodal/text+audio"  # 文本+音频
    MULTIMODAL_TEXT_VIDEO = "multimodal/text+video"  # 文本+视频


# 角色类型常量
class RoleTypes:
    HUMAN = "human"                      # 人类
    AI = "ai"                            # AI
    SYSTEM = "system"                    # 系统


# 轮次状态常量
class TurnStatus:
    OPEN = "open"                        # 开放状态
    RESPONDED = "responded"              # 已响应
    UNRESPONDED = "unresponded"          # 未响应
    CLOSED = "closed"                    # 已关闭


# AI情绪状态常量
class AIMoodStates:
    NEUTRAL = "neutral"                  # 中性
    HAPPY = "happy"                      # 高兴
    SAD = "sad"                          # 悲伤
    EXCITED = "excited"                  # 兴奋
    CONFUSED = "confused"                # 困惑
    CURIOUS = "curious"                  # 好奇
    CONCERNED = "concerned"              # 关心
    PROFESSIONAL = "professional"        # 专业

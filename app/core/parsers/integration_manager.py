"""
多模态融合管理器模块

用于整合文本、视觉、听觉信息，形成统一上下文片段
"""
from typing import Dict, Any, List, Optional
import asyncio

from ...core.logger import logger

class IntegrationManager:
    """多模态融合管理器"""
    
    def __init__(self):
        self.logger = logger
    
    async def integrate(self, parsed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        整合多种模态的解析结果
        
        Args:
            parsed_results: 多个解析器的结果列表
        
        Returns:
            整合后的结果
        """
        try:
            if not parsed_results:
                return {
                    "text_block": "",
                    "semantic_tags": [],
                    "emotions": ["neutral"],
                    "modalities": []
                }
            
            # 如果只有一个结果，直接返回
            if len(parsed_results) == 1:
                result = parsed_results[0]
                result["modalities"] = [self._detect_modality(result)]
                return result
            
            # 整合多个结果
            # 1. 收集所有文本块
            text_blocks = []
            for result in parsed_results:
                if "text_block" in result and result["text_block"]:
                    text_blocks.append(result["text_block"])
            
            # 2. 合并文本块
            combined_text = self._combine_text_blocks(text_blocks)
            
            # 3. 收集所有语义标签
            all_tags = []
            for result in parsed_results:
                if "semantic_tags" in result and result["semantic_tags"]:
                    all_tags.extend(result["semantic_tags"])
            
            # 去重
            unique_tags = list(set(all_tags))
            
            # 4. 收集所有情绪标签
            all_emotions = []
            for result in parsed_results:
                if "emotions" in result and result["emotions"]:
                    all_emotions.extend(result["emotions"])
            
            # 选择主要情绪
            primary_emotion = self._select_primary_emotion(all_emotions)
            
            # 5. 检测涉及的模态
            modalities = []
            for result in parsed_results:
                modality = self._detect_modality(result)
                if modality and modality not in modalities:
                    modalities.append(modality)
            
            # 6. 生成多模态摘要
            multimodal_summary = await self._generate_multimodal_summary(parsed_results, modalities)
            
            # 7. 构建整合结果
            integrated_result = {
                "text_block": combined_text,
                "semantic_tags": unique_tags,
                "emotions": [primary_emotion],
                "modalities": modalities,
                "multimodal_summary": multimodal_summary,
                "original_results": parsed_results
            }
            
            # 添加源消息信息（使用第一个结果的信息）
            if parsed_results and "source_message_id" in parsed_results[0]:
                integrated_result["source_message_id"] = parsed_results[0]["source_message_id"]
            if parsed_results and "origin" in parsed_results[0]:
                integrated_result["origin"] = parsed_results[0]["origin"]
            if parsed_results and "timestamp" in parsed_results[0]:
                integrated_result["timestamp"] = parsed_results[0]["timestamp"]
            
            return integrated_result
        
        except Exception as e:
            self.logger.error(f"整合多模态结果失败: {str(e)}")
            # 返回一个基本的结构
            return {
                "text_block": " ".join([r.get("text_block", "") for r in parsed_results if "text_block" in r]),
                "semantic_tags": [],
                "emotions": ["neutral"],
                "modalities": ["text"],
                "error": str(e)
            }
    
    def _combine_text_blocks(self, text_blocks: List[str]) -> str:
        """
        合并文本块
        
        Args:
            text_blocks: 文本块列表
        
        Returns:
            合并后的文本
        """
        # 简单实现，实际可能需要更复杂的逻辑
        return "\n\n".join(text_blocks)
    
    def _select_primary_emotion(self, emotions: List[str]) -> str:
        """
        选择主要情绪
        
        Args:
            emotions: 情绪列表
        
        Returns:
            主要情绪
        """
        if not emotions:
            return "neutral"
        
        # 计算每种情绪的出现次数
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 选择出现次数最多的情绪
        primary_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        return primary_emotion
    
    def _detect_modality(self, result: Dict[str, Any]) -> str:
        """
        检测结果的模态
        
        Args:
            result: 解析结果
        
        Returns:
            模态类型
        """
        if "image_url" in result:
            return "image"
        elif "audio_url" in result:
            return "audio"
        elif "tool_type" in result:
            return "tool_output"
        elif "prompt_type" in result:
            return "prompt"
        elif "quoted_content" in result:
            return "quote_reply"
        elif "original_markdown" in result:
            return "markdown"
        else:
            return "text"
    
    async def _generate_multimodal_summary(self, results: List[Dict[str, Any]], modalities: List[str]) -> str:
        """
        生成多模态摘要
        
        Args:
            results: 解析结果列表
            modalities: 模态列表
        
        Returns:
            多模态摘要
        """
        # 简单实现，实际应使用更复杂的摘要生成逻辑
        if "image" in modalities and "text" in modalities:
            # 图文结合的摘要
            image_result = next((r for r in results if self._detect_modality(r) == "image"), None)
            text_result = next((r for r in results if self._detect_modality(r) == "text"), None)
            
            if image_result and text_result:
                caption = image_result.get("caption", "图片")
                text = text_result.get("text_block", "")
                return f"用户发送了一张{caption}，并表示："{text}""
        
        elif "audio" in modalities and "text" in modalities:
            # 音频文本结合的摘要
            audio_result = next((r for r in results if self._detect_modality(r) == "audio"), None)
            text_result = next((r for r in results if self._detect_modality(r) == "text"), None)
            
            if audio_result and text_result:
                transcription = audio_result.get("transcription", "音频内容")
                text = text_result.get("text_block", "")
                return f"用户发送了一段音频（内容：{transcription}），并表示："{text}""
        
        # 默认摘要
        modality_texts = {
            "text": "文本",
            "image": "图片",
            "audio": "音频",
            "tool_output": "工具结果",
            "prompt": "系统提示",
            "quote_reply": "引用回复",
            "markdown": "富文本"
        }
        
        modality_descriptions = [modality_texts.get(m, m) for m in modalities]
        return f"用户发送了{'+'.join(modality_descriptions)}内容"

# 创建全局多模态融合管理器实例
integration_manager = IntegrationManager()

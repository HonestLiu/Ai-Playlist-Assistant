"""意图解析 Prompt。

把自然语言需求翻译成结构化的 ``PlaylistIntent``。给模型喂一点「曲库画像」
（曲库里实际存在的流派、年代范围），避免它凭空编造不存在的标签。
"""

from __future__ import annotations

from app.ai.providers.base import Message
from app.ai.schemas import PlaylistIntent

SYSTEM = """你是一个音乐推荐助手的结构化解析器。用户会用自然语言描述想要的歌单场景，
你需要把需求解析成严格的 JSON，字段如下：
{
  "summary": "一句话概括需求",
  "title": "一个简短有吸引力的歌单标题（≤20 字，纯中文或中英混排均可，但不要带「AI」「智能」等前缀，也不要加日期或时间）",
  "mood": ["relaxed"|"calm"|"sad"|"happy"|"energetic"|"focus"|"sleep"|"workout"|"healing" 等],
  "language": ["ja"|"en"|"zh"|"ko"|"fr" 等 ISO 代码，若未指定则为 null],
  "genres": ["摇滚"|"流行"|"电子"|"古典"|"爵士"|"民谣"|"说唱"|"动漫"|"游戏" 等，未指定为 null],
  "decade": 1990,            // 明确提到某年代的整数，否则 null
  "min_year": null,
  "max_year": null,
  "activities": ["学习"|"运动"|"睡眠"|"工作" 等场景，未指定为 null],
  "energy": "low"|"medium"|"high",  // 节奏强度代理，无法判断为 null
  "keywords": ["具体的歌手或歌名片段"],   // 用户点名的，未指定为 null
  "exclude_keywords": null,
  "target_size": 20          // 用户想要的歌曲数量，默认 20
}
只输出 JSON，不要任何解释或 markdown 代码块。language 用 ISO 639-1 代码：
日语=ja，英语=en，中文=zh，韩语=ko，法语=fr。
title 要像一首精选合辑的名字（例如「深夜书房 BGM」「通勤燃向动漫」「雨日慵懒爵士」），
不要复述用户原话，也不要出现「歌单」「播放列表」这类词。"""

USER_TEMPLATE = """曲库画像（仅作参考，帮助你判断可选范围）：
- 可用流派：{genres}
- 年代范围：{year_min} ~ {year_max}

用户需求：{query}"""


def build_intent_messages(query: str, *, genres: list[str], year_min: int | None, year_max: int | None) -> list[Message]:
    user = USER_TEMPLATE.format(
        genres="、".join(genres) if genres else "（未知）",
        year_min=year_min or "未知",
        year_max=year_max or "未知",
        query=query,
    )
    return [Message(role="system", content=SYSTEM), Message(role="user", content=user)]


# 供调用方拿到 schema 字段名（如需要）
INTENT_FIELDS = list(PlaylistIntent.model_fields.keys())

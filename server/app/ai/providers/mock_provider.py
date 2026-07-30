"""本地 Mock Provider（无需 API key，供开发/测试使用）。

它会模拟真实 LLM 的两段行为：

1. 意图解析：用简单启发式从自然语言里抽取语言/情绪/年代/关键词等。
2. 候选选择：把召回池里的歌曲按要求挑出一部分，并给每首一句理由。

它不调用任何网络，因此可以在没有 LLM key 的环境里把整条推荐管线
端到端跑通。真实模型接入后，业务代码一行都不用改。
"""

from __future__ import annotations

import json
import re

from app.ai.providers.base import ChatRequest, ChatResponse, LLMProvider

_LANG_MAP = {
    "日语": "ja", "日文": "ja", "日本": "ja",
    "英文": "en", "英语": "en", "欧美": "en",
    "中文": "zh", "国语": "zh", "华语": "zh",
    "韩文": "ko", "韩语": "ko", "韩文歌": "ko",
    "法文": "fr", "法语": "fr",
}
_MOOD_MAP = {
    "放松": "relaxed", "轻松": "relaxed", "平静": "calm", "安静": "calm",
    "伤感": "sad", "难过": "sad", "孤独": "sad",
    "开心": "happy", "快乐": "happy", "欢快": "happy",
    "燃": "energetic", "兴奋": "energetic", "嗨": "energetic",
    "专注": "focus", "学习": "focus", "工作": "focus", "写代码": "focus",
    "睡眠": "sleep", "睡觉": "sleep",
    "运动": "workout", "跑步": "workout", "健身": "workout",
    "治愈": "healing", "温柔": "healing",
}
_GENRE_HINTS = ["摇滚", "流行", "电子", "古典", "爵士", "民谣", "说唱", "rap", "金属", "轻音乐", "动漫", "游戏"]


class MockProvider(LLMProvider):
    async def chat(self, request: ChatRequest) -> ChatResponse:
        system = request.messages[0].content if request.messages else ""
        user = request.messages[-1].content if request.messages else ""

        if _is_selection(system, user):
            content = self._select(user)
        else:
            content = self._intent(user)
        return ChatResponse(content=content, model="mock-local")

    # ------------------------------------------------------------------ 意图解析
    def _intent(self, text: str) -> str:
        languages = [code for kw, code in _LANG_MAP.items() if kw in text]
        moods = [code for kw, code in _MOOD_MAP.items() if kw in text]

        genres: list[str] = [g for g in _GENRE_HINTS if g.lower() in text.lower()]

        decade = None
        m = re.search(r"(19|20)\d{2}", text)
        if m:
            year = int(m.group(0))
            decade = (year // 10) * 10

        target_size = 20
        n = re.search(r"(\d+)\s*首", text)
        if n:
            target_size = int(n.group(1))

        keywords = re.findall(r"《([^》]+)》", text) or re.findall(r"\"([^\"]+)\"", text)

        intent = {
            "summary": text,
            "mood": moods or None,
            "language": languages or None,
            "genres": genres or None,
            "decade": decade,
            "min_year": None,
            "max_year": None,
            "activities": None,
            "energy": None,
            "keywords": keywords or None,
            "exclude_keywords": None,
            "target_size": target_size,
        }
        return json.dumps(intent, ensure_ascii=False)

    # ------------------------------------------------------------------ 候选选择
    def _select(self, user: str) -> str:
        candidates = _extract_candidates(user)
        target = 15
        n = re.search(r"挑选\s*(\d+)\s*首", user)
        if n:
            target = int(n.group(1))

        if not candidates:
            return json.dumps({"songs": []}, ensure_ascii=False)

        # 优先挑标题/艺术家命中查询关键词的；其余顺序取，保证确定性
        picked = candidates[:target]
        songs = [
            {
                "song_id": c.get("id"),
                "reason": f"符合「{c.get('artist', '')}」的风格，适合本场景",
            }
            for c in picked
            if c.get("id")
        ]
        return json.dumps({"songs": songs}, ensure_ascii=False)


def _is_selection(system: str, user: str) -> bool:
    marker = "候选" in system or "挑选" in system or "选择" in system
    has_json = "[" in user and "]" in user
    return marker and has_json


def _extract_candidates(text: str) -> list[dict]:
    # 取最后一个 [...]，容忍前后有说明文字
    start = text.rfind("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    blob = text[start : end + 1]
    try:
        data = json.loads(blob)
    except (ValueError, TypeError):
        return []
    return data if isinstance(data, list) else []

"""候选选择 Prompt。

把召回池里的歌曲按意图挑选出来。硬性约束：**只能从下面给出的候选列表里选**，
返回每首歌的 song_id 与一句简短理由。语言/情绪等需要「理解」的维度，模型
要靠候选里的艺术家名、曲名去判断（曲库没有语言字段）。
"""

from __future__ import annotations

import json

from app.ai.providers.base import Message

SYSTEM = """你是一个懂音乐的选歌师。下面会给一份「候选歌曲列表」（JSON 数组，每项含
id / title / artist / album / year / genre）。请你按用户的意图，从中挑选出最契合的若干首。

规则：
1. 只能从列表里选，song_id 必须来自候选列表，禁止编造。
2. 返回严格 JSON：{"songs": [{"song_id": "...", "reason": "一句中文理由"}]}
3. 理由要具体（为什么契合场景/情绪/语言），不要空话。
4. 尽量凑满要求的数量；候选不足时全部选上。
5. 只输出 JSON，不要解释或 markdown 代码块。"""

USER_TEMPLATE = """用户意图：{intent_summary}
需要挑选 {target_size} 首。

候选歌曲列表（仅可从中选择）：
{candidates}"""


def build_selection_messages(
    intent_summary: str, candidates: list[dict], target_size: int
) -> list[Message]:
    payload = json.dumps(candidates, ensure_ascii=False)
    user = USER_TEMPLATE.format(
        intent_summary=intent_summary,
        target_size=target_size,
        candidates=payload,
    )
    return [Message(role="system", content=SYSTEM), Message(role="user", content=user)]

"""AI 推荐相关的数据结构（同时用于内部编排与 API 响应）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlaylistIntent(BaseModel):
    """LLM 从自然语言里解析出的结构化意图。"""

    summary: str = Field(description="对本次需求的简短概括")
    title: str | None = Field(
        default=None,
        description="AI 生成的简短歌单标题（≤20 字，不含「AI」等前缀，不含日期）",
    )
    mood: list[str] | None = Field(default=None, description="情绪标签")
    language: list[str] | None = Field(
        default=None, description="语言偏好，ISO 代码如 ja/en/zh/ko"
    )
    genres: list[str] | None = Field(default=None, description="流派偏好")
    decade: int | None = Field(default=None, description="年代，如 1990/2000")
    min_year: int | None = Field(default=None)
    max_year: int | None = Field(default=None)
    activities: list[str] | None = Field(default=None, description="适用场景，如 学习/运动/睡眠")
    energy: str | None = Field(default=None, description="low/medium/high，节奏强度代理")
    keywords: list[str] | None = Field(default=None, description="具体的歌名/歌手片段")
    exclude_keywords: list[str] | None = Field(default=None)
    target_size: int = Field(default=20, description="期望歌曲数量")


class SelectedSong(BaseModel):
    song_id: str
    reason: str = ""


class SongSelection(BaseModel):
    songs: list[SelectedSong]


class RecommendedSong(BaseModel):
    id: str
    title: str
    artist_name: str | None = None
    album_name: str | None = None
    year: int | None = None
    duration: int | None = None
    reason: str | None = None


class PlaylistRef(BaseModel):
    id: str
    subsonic_id: str
    name: str


class RecommendationResult(BaseModel):
    query: str
    intent: PlaylistIntent
    provider: str
    total_candidates: int
    songs: list[RecommendedSong]
    total_duration: int = 0
    title: str | None = None
    playlist: PlaylistRef | None = None


class DailyMixRequest(BaseModel):
    """每日推荐请求；target_size 不传则默认 20。"""

    target_size: int | None = None


class DailyMixResult(BaseModel):
    """每日推荐结果：含本次主题、推荐明细与（新建/刷新后的）歌单引用。"""

    query: str
    theme: str
    recommendation: RecommendationResult
    playlist: PlaylistRef | None = None
    refreshed: bool = False
    created: bool = False

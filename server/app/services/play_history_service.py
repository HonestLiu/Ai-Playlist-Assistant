"""播放历史服务：记录「真正播放过」的歌曲，并聚合出用户口味画像。

Daily Mix 个性化读取这里的 Top 艺术家 / Top 流派 / 最近播放，作为推荐偏好。
"""

from __future__ import annotations

from sqlmodel import Session, func, select

from app.database.models import PlayHistory, Song


class PlayHistoryService:
    def record(self, session: Session, song_id: str) -> None:
        session.add(PlayHistory(song_id=song_id))
        session.commit()

    def total_plays(self, session: Session) -> int:
        return session.exec(select(func.count(PlayHistory.id))).first() or 0

    def top_artists(self, session: Session, n: int = 8) -> list[str]:
        rows = session.exec(
            select(Song.artist_name, func.count(Song.artist_name))
            .join(PlayHistory, PlayHistory.song_id == Song.id)
            .where(Song.artist_name.is_not(None))
            .group_by(Song.artist_name)
            .order_by(func.count(Song.artist_name).desc())
            .limit(n)
        ).all()
        return [r[0] for r in rows if r[0]]

    def top_genres(self, session: Session, n: int = 6) -> list[str]:
        rows = session.exec(
            select(Song.genre, func.count(Song.genre))
            .join(PlayHistory, PlayHistory.song_id == Song.id)
            .where(Song.genre.is_not(None))
            .group_by(Song.genre)
            .order_by(func.count(Song.genre).desc())
            .limit(n)
        ).all()
        return [r[0] for r in rows if r[0]]

    def recent_song_ids(self, session: Session, limit: int = 40) -> list[str]:
        rows = session.exec(
            select(PlayHistory.song_id)
            .order_by(PlayHistory.played_at.desc())
            .limit(limit)
        ).all()
        seen: set[str] = set()
        out: list[str] = []
        for sid in rows:
            if sid not in seen:
                seen.add(sid)
                out.append(sid)
        return out

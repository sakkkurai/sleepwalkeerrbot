from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    banned_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    banned_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    ban_logs: Mapped[list["BanLog"]] = relationship(back_populates="user")

class BanLog(Base):
    __tablename__ = "ban_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banned_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    banned_by_admin_id: Mapped[int] = mapped_column(BigInteger)
    banned_by_admin_name: Mapped[str] = mapped_column(String(255))
    banned_by_admin_username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    ban_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="ban_logs")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    media_group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    media_content: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    author: Mapped["User"] = relationship(back_populates="posts")
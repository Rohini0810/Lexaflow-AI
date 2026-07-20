from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class Regulation(Base):
    __tablename__ = "regulations"

    regulation_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(120))
    jurisdiction: Mapped[str] = mapped_column(String(120))
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    current_hash: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(120), default="Monitoring")
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    versions: Mapped[list["Version"]] = relationship(back_populates="regulation", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="regulation", cascade="all, delete-orphan")
    actions: Mapped[list["Action"]] = relationship(back_populates="regulation", cascade="all, delete-orphan")


class Version(Base):
    __tablename__ = "versions"
    __table_args__ = (
        UniqueConstraint("regulation_id", "content_hash", name="uq_versions_reg_hash"),
        UniqueConstraint("regulation_id", "version_number", name="uq_versions_reg_version"),
    )

    version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[str] = mapped_column(ForeignKey("regulations.regulation_id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    blob_path: Mapped[str] = mapped_column(String(600))
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    regulation: Mapped["Regulation"] = relationship(back_populates="versions")


class Analysis(Base):
    __tablename__ = "analysis"
    __table_args__ = (UniqueConstraint("regulation_id", "content_hash", name="uq_analysis_reg_hash"),)

    analysis_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[str] = mapped_column(ForeignKey("regulations.regulation_id"), index=True)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    what_changed: Mapped[str] = mapped_column(Text)
    business_impact: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(40))
    affected_teams: Mapped[str] = mapped_column(Text)
    recommended_actions: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    regulation: Mapped["Regulation"] = relationship(back_populates="analyses")


class Action(Base):
    __tablename__ = "actions"

    action_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[str] = mapped_column(ForeignKey("regulations.regulation_id"), index=True)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    action_signature: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    action_text: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(200))
    priority: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="Not Started", index=True)
    due_date: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    regulation: Mapped["Regulation"] = relationship(back_populates="actions")


class SourceUpdate(Base):
    __tablename__ = "source_updates"

    update_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    jurisdiction: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(800))
    link: Mapped[str] = mapped_column(String(1200))
    published: Mapped[str] = mapped_column(String(200))
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    is_new_update: Mapped[bool] = mapped_column(Boolean, default=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MonitorRun(Base):
    __tablename__ = "monitor_runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[str] = mapped_column(String(120), index=True)
    old_hash: Mapped[str] = mapped_column(String(128))
    new_hash: Mapped[str] = mapped_column(String(128))
    change_detected: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(40), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)



from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActionRecommendation(BaseModel):
    action: str
    owner: str = "Unassigned"
    priority: str = "Medium"
    due_days: int = 7


class AnalysisResult(BaseModel):
    what_changed: dict[str, Any] | list[str] | str = Field(default_factory=dict)
    business_impact: dict[str, Any] | str = Field(default_factory=dict)
    risk_level: str = "medium"
    affected_teams: list[str] = Field(default_factory=list)
    recommended_actions: list[ActionRecommendation] = Field(default_factory=list)
    confidence_score: float = 0.8


class MonitorRunResponse(BaseModel):
    regulation_id: str
    title: str
    source: str
    jurisdiction: str
    old_text: str
    new_text: str
    old_hash: str
    new_hash: str
    current_hash: str
    change_detected: bool
    old_version: str
    new_version: str
    carryover_open_actions: int = 0
    analysis: AnalysisResult | None = None


class ActionItemResponse(BaseModel):
    action_id: int
    regulation_id: str
    action_text: str
    owner: str
    priority: str
    status: str
    due_date: str
    source: str | None = None
    last_updated_at: datetime | None = None
    created_at: datetime


class ActionUpdateRequest(BaseModel):
    status: str | None = None
    due_date: str | None = None


class VersionResponse(BaseModel):
    version_number: int
    content_hash: str
    detected_at: datetime


class SourceUpdateResponse(BaseModel):
    update_id: int
    source: str
    jurisdiction: str
    title: str
    link: str
    published: str
    is_new_update: bool
    is_fallback: bool
    fetched_at: datetime


class DashboardSummaryResponse(BaseModel):
    regulations_monitored: int
    source_updates: int
    high_risk_count: int
    pending_actions: int


